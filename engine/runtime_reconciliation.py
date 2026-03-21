# path: engine/runtime_reconciliation.py

import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


ARTIFACT_SCHEMA_VERSION = "runtime_reconciliation_artifact_v4"


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if is_dataclass(value):
        return asdict(value)

    return str(value)


class RuntimeReconciliationRunner:

    def __init__(
        self,
        reconciliation_engine,
        broker_snapshot_supplier,
        artifact_dir: str = "logs/reconciliation",
        store_full_snapshots: bool = True,
    ):
        self.reconciliation_engine = reconciliation_engine
        self.broker_snapshot_supplier = broker_snapshot_supplier
        self.store_full_snapshots = store_full_snapshots

        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------
    # main
    # ---------------------------------

    def run(
        self,
        engine_snapshot: dict,
        broker_snapshot: Optional[dict] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)

        engine_snapshot_error = self._validate_engine_snapshot(engine_snapshot)

        supplier_error: Optional[str] = None
        broker_snapshot_supplied = broker_snapshot is not None

        if broker_snapshot is None:
            try:
                supplied = self.broker_snapshot_supplier()

                if not isinstance(supplied, dict):
                    raise ValueError("broker_snapshot_supplier returned non-dict")

                broker_snapshot = supplied

            except Exception as exc:
                supplier_error = str(exc)
                logger.exception(
                    "BROKER_SNAPSHOT_SUPPLIER_FAILED error=%s",
                    exc,
                )

        if supplier_error is not None:
            return {
                "artifact_path": None,
                "result": None,
                "supplier_error": supplier_error,
                "engine_snapshot_error": engine_snapshot_error,
                "artifact_write_error": None,
                "should_block_trading": True,
                "block_reason": "BROKER_SNAPSHOT_SUPPLIER_FAILED",
            }

        if broker_snapshot is None:
            logger.error("BROKER_SNAPSHOT_NONE")
            return {
                "artifact_path": None,
                "result": None,
                "supplier_error": supplier_error,
                "engine_snapshot_error": engine_snapshot_error,
                "artifact_write_error": None,
                "should_block_trading": True,
                "block_reason": "BROKER_SNAPSHOT_NONE",
            }

        if engine_snapshot_error is not None:
            return {
                "artifact_path": None,
                "result": None,
                "supplier_error": supplier_error,
                "engine_snapshot_error": engine_snapshot_error,
                "artifact_write_error": None,
                "should_block_trading": True,
                "block_reason": "ENGINE_SNAPSHOT_INVALID",
            }

        broker_positions = broker_snapshot.get("positions", {})
        engine_positions = engine_snapshot.get("positions", {})

        all_mismatches = []
        result = None

        try:
            result = self.reconciliation_engine.reconcile(
                broker_positions=broker_positions,
                engine_positions=engine_positions,
            )
        except Exception as exc:
            logger.exception("RECONCILIATION_EXECUTION_FAILED error=%s", exc)
            return {
                "artifact_path": None,
                "result": None,
                "supplier_error": supplier_error,
                "engine_snapshot_error": engine_snapshot_error,
                "artifact_write_error": None,
                "should_block_trading": True,
                "block_reason": "RECONCILIATION_EXECUTION_FAILED",
            }

        if result is None:
            logger.error("RECON_RESULT_NONE")
            return {
                "artifact_path": None,
                "result": None,
                "supplier_error": supplier_error,
                "engine_snapshot_error": engine_snapshot_error,
                "artifact_write_error": None,
                "should_block_trading": True,
                "block_reason": "RECON_RESULT_NONE",
            }

        all_mismatches = (
            list(result.missing_in_engine)
            + list(result.missing_in_broker)
            + list(result.qty_mismatches)
            + list(result.avg_price_mismatches)
        )

        if len(all_mismatches) > 0:
            logger.error(
                "RECON_MISMATCH_SUMMARY missing_in_engine=%s missing_in_broker=%s qty=%s price=%s broker_snapshot_supplied=%s",
                len(result.missing_in_engine),
                len(result.missing_in_broker),
                len(result.qty_mismatches),
                len(result.avg_price_mismatches),
                broker_snapshot_supplied,
            )

        should_block_trading, block_reason = self._determine_block_policy(
            result=result,
        )

        artifact_write_error = None
        artifact_path = self.artifact_dir / now.strftime("recon_%Y%m%d_%H%M%S_%f.json")

        payload = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "timestamp": now.isoformat(),
            "snapshot_status": "OK",
            "broker_snapshot_supplied": broker_snapshot_supplied,
            "matched": result.ok,
            "should_block_trading": should_block_trading,
            "block_reason": block_reason,
            "supplier_error": supplier_error,
            "engine_snapshot_error": engine_snapshot_error,
            "artifact_write_error": None,
            "summary": {
                "checked_key_count": result.details.get("checked_key_count", 0),
                "price_tolerance": result.details.get("price_tolerance"),
                "missing_in_engine_count": len(result.missing_in_engine),
                "missing_in_broker_count": len(result.missing_in_broker),
                "qty_mismatch_count": len(result.qty_mismatches),
                "avg_price_mismatch_count": len(result.avg_price_mismatches),
                "mismatch_count": len(all_mismatches),
            },
            "details": result.details,
            "missing_in_engine": result.missing_in_engine,
            "missing_in_broker": result.missing_in_broker,
            "qty_mismatches": result.qty_mismatches,
            "avg_price_mismatches": result.avg_price_mismatches,
            "mismatches": all_mismatches,
        }

        if self.store_full_snapshots:
            payload["broker_snapshot"] = broker_snapshot
            payload["engine_snapshot"] = engine_snapshot

        try:
            with artifact_path.open("w", encoding="utf-8") as f:
                json.dump(
                    payload,
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=_json_default,
                )
        except Exception as exc:
            artifact_write_error = str(exc)
            payload["artifact_write_error"] = artifact_write_error

            logger.exception(
                "RUNTIME_RECON_ARTIFACT_WRITE_FAILED artifact=%s error=%s",
                artifact_path,
                exc,
            )

        artifact_path_str = None if artifact_write_error else str(artifact_path)

        if should_block_trading:
            logger.error(
                "RUNTIME_RECON_BLOCK artifact=%s matched=%s block_reason=%s mismatch_count=%s missing_in_engine=%s missing_in_broker=%s qty_mismatch=%s avg_price_mismatch=%s supplier_error=%s engine_snapshot_error=%s artifact_write_error=%s broker_snapshot_supplied=%s",
                artifact_path_str,
                result.ok,
                block_reason,
                len(all_mismatches),
                len(result.missing_in_engine),
                len(result.missing_in_broker),
                len(result.qty_mismatches),
                len(result.avg_price_mismatches),
                supplier_error,
                engine_snapshot_error,
                artifact_write_error,
                broker_snapshot_supplied,
            )
        elif result.ok:
            logger.info(
                "RUNTIME_RECON_OK artifact=%s checked_keys=%s broker_snapshot_supplied=%s",
                artifact_path_str,
                result.details.get("checked_key_count", 0),
                broker_snapshot_supplied,
            )
        else:
            logger.warning(
                "RUNTIME_RECON_WARN artifact=%s mismatch_count=%s missing_in_engine=%s missing_in_broker=%s qty_mismatch=%s avg_price_mismatch=%s broker_snapshot_supplied=%s",
                artifact_path_str,
                len(all_mismatches),
                len(result.missing_in_engine),
                len(result.missing_in_broker),
                len(result.qty_mismatches),
                len(result.avg_price_mismatches),
                broker_snapshot_supplied,
            )

        for m in all_mismatches:
            logger.debug("RECON_MISMATCH %s", m)

        return {
            "artifact_path": artifact_path_str,
            "result": result,
            "supplier_error": supplier_error,
            "engine_snapshot_error": engine_snapshot_error,
            "artifact_write_error": artifact_write_error,
            "should_block_trading": should_block_trading,
            "block_reason": block_reason,
        }

    # ---------------------------------
    # validation
    # ---------------------------------

    def _validate_engine_snapshot(self, engine_snapshot: Any) -> Optional[str]:
        if not isinstance(engine_snapshot, dict):
            return "engine_snapshot must be dict"

        positions = engine_snapshot.get("positions")
        if positions is None:
            return "engine_snapshot missing positions"

        if not isinstance(positions, dict):
            return "engine_snapshot positions must be dict"

        if len(positions) == 0:
            logger.warning("ENGINE_SNAPSHOT_EMPTY")

        return None

    # ---------------------------------
    # block policy
    # ---------------------------------

    def _determine_block_policy(self, result):
        if len(result.missing_in_engine) > 0:
            return True, "RECON_MISSING_IN_ENGINE"

        if len(result.missing_in_broker) > 0:
            return True, "RECON_MISSING_IN_BROKER"

        if len(result.qty_mismatches) > 0:
            return True, "RECON_QTY_MISMATCH"

        if len(result.avg_price_mismatches) > 0:
            return False, "RECON_AVG_PRICE_MISMATCH"

        return False, None