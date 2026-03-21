import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from core.execution.reconciliation_types import (
    BlockReason,
    SnapshotStatus,
)


logger = logging.getLogger(__name__)

ARTIFACT_SCHEMA_VERSION = "runtime_reconciliation_artifact_v4"


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if is_dataclass(value):
        return asdict(value)

    raise TypeError("unsupported json type: {}".format(type(value)))


class RuntimeReconciliationRunner:
    """
    책임:
    - broker snapshot supplier 호출
    - engine/broker snapshot 구조 검증
    - reconciliation 실행
    - block policy 결정
    - artifact 기록
    - 필요 시 AccountHardStop 외부 래치 발동
    """

    def __init__(
        self,
        reconciliation_engine,
        broker_snapshot_supplier,
        artifact_dir: str = "logs/reconciliation",
        store_full_snapshots: bool = True,
        account_hard_stop=None,
    ):
        self.reconciliation_engine = reconciliation_engine
        self.broker_snapshot_supplier = broker_snapshot_supplier
        self.store_full_snapshots = store_full_snapshots
        self.account_hard_stop = account_hard_stop

        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------
    # main
    # ---------------------------------

    def run(self, engine_snapshot: dict) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)

        engine_snapshot_error = self._validate_engine_snapshot(engine_snapshot)

        broker_snapshot: Dict[str, Any] = {"positions": {}, "meta": {}}
        supplier_error: Optional[str] = None

        # -------------------------------
        # broker snapshot supplier
        # -------------------------------

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

            # technical fallback only
            broker_snapshot = {"positions": {}, "meta": {}}

        broker_snapshot_error = self._validate_broker_snapshot(broker_snapshot)
        broker_meta = broker_snapshot.get("meta", {}) if isinstance(broker_snapshot, dict) else {}

        result = self.reconciliation_engine.reconcile(
            broker_snapshot=broker_snapshot,
            engine_snapshot=engine_snapshot,
        )

        should_block_trading, block_reason = self._determine_block_policy(
            supplier_error=supplier_error,
            engine_snapshot_error=engine_snapshot_error,
            broker_snapshot_error=broker_snapshot_error,
            broker_meta=broker_meta,
            result=result,
        )

        snapshot_status = self._build_snapshot_status(
            supplier_error=supplier_error,
            engine_snapshot_error=engine_snapshot_error,
            broker_snapshot_error=broker_snapshot_error,
            broker_meta=broker_meta,
        )

        hard_stop_triggered = False
        if should_block_trading and self.account_hard_stop is not None:
            try:
                self.account_hard_stop.trigger_external(
                    reason=block_reason or "RECON_BLOCK",
                    evaluation_point="RECONCILIATION",
                )
                hard_stop_triggered = True
            except Exception as exc:
                logger.exception(
                    "RECON_HARD_STOP_TRIGGER_FAILED reason=%s error=%s",
                    block_reason,
                    exc,
                )

        artifact_write_error = None
        artifact_path = self.artifact_dir / now.strftime("recon_%Y%m%d_%H%M%S_%f.json")

        payload = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "timestamp": now.isoformat(),
            "snapshot_status": snapshot_status,
            "matched": result.matched,
            "should_block_trading": should_block_trading,
            "block_reason": block_reason,
            "hard_stop_triggered": hard_stop_triggered,
            "supplier_error": supplier_error,
            "engine_snapshot_error": engine_snapshot_error,
            "broker_snapshot_error": broker_snapshot_error,
            "artifact_write_error": None,
            "summary": {
                "broker_positions": result.broker_positions,
                "engine_positions": result.engine_positions,
                "qty_mismatches": result.qty_mismatches,
                "avg_price_mismatches": result.avg_price_mismatches,
                "broker_only": result.broker_only,
                "engine_only": result.engine_only,
                "invalid_data": result.invalid_data,
                "mismatch_count": len(result.mismatches),
                "broker_meta": {
                    "invalid_rows_count": int(broker_meta.get("invalid_rows_count", 0) or 0),
                    "duplicate_keys_count": int(broker_meta.get("duplicate_keys_count", 0) or 0),
                    "zero_qty_skipped_count": int(broker_meta.get("zero_qty_skipped_count", 0) or 0),
                    "position_count": broker_meta.get("position_count"),
                    "broker": broker_meta.get("broker"),
                    "account_id": broker_meta.get("account_id"),
                    "exchange": broker_meta.get("exchange"),
                    "currency": broker_meta.get("currency"),
                    "instrument_type": broker_meta.get("instrument_type"),
                },
            },
            "mismatches": result.mismatches,
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

        if should_block_trading:
            logger.error(
                "RUNTIME_RECON_BLOCK artifact=%s matched=%s block_reason=%s mismatches=%s qty=%s avg=%s broker_only=%s engine_only=%s invalid=%s supplier_error=%s engine_snapshot_error=%s broker_snapshot_error=%s invalid_rows=%s duplicate_keys=%s hard_stop_triggered=%s artifact_write_error=%s",
                artifact_path,
                result.matched,
                block_reason,
                len(result.mismatches),
                result.qty_mismatches,
                result.avg_price_mismatches,
                result.broker_only,
                result.engine_only,
                result.invalid_data,
                supplier_error,
                engine_snapshot_error,
                broker_snapshot_error,
                int(broker_meta.get("invalid_rows_count", 0) or 0),
                int(broker_meta.get("duplicate_keys_count", 0) or 0),
                hard_stop_triggered,
                artifact_write_error,
            )
        elif result.matched:
            logger.info(
                "RUNTIME_RECON_OK artifact=%s broker=%s engine=%s",
                artifact_path,
                result.broker_positions,
                result.engine_positions,
            )
        else:
            logger.warning(
                "RUNTIME_RECON_WARN artifact=%s mismatches=%s qty=%s avg=%s broker_only=%s engine_only=%s invalid=%s invalid_rows=%s duplicate_keys=%s",
                artifact_path,
                len(result.mismatches),
                result.qty_mismatches,
                result.avg_price_mismatches,
                result.broker_only,
                result.engine_only,
                result.invalid_data,
                int(broker_meta.get("invalid_rows_count", 0) or 0),
                int(broker_meta.get("duplicate_keys_count", 0) or 0),
            )

        for m in result.mismatches:
            logger.debug(
                "RECON_MISMATCH key=%s type=%s broker_qty=%s engine_qty=%s broker_avg=%s engine_avg=%s",
                m.key,
                m.type,
                m.broker_qty,
                m.engine_qty,
                m.broker_avg,
                m.engine_avg,
            )

        return {
            "artifact_path": str(artifact_path),
            "result": result,
            "supplier_error": supplier_error,
            "engine_snapshot_error": engine_snapshot_error,
            "broker_snapshot_error": broker_snapshot_error,
            "artifact_write_error": artifact_write_error,
            "should_block_trading": should_block_trading,
            "block_reason": block_reason,
            "snapshot_status": snapshot_status,
            "hard_stop_triggered": hard_stop_triggered,
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

        return None

    def _validate_broker_snapshot(self, broker_snapshot: Any) -> Optional[str]:
        if not isinstance(broker_snapshot, dict):
            return "broker_snapshot must be dict"

        positions = broker_snapshot.get("positions")
        if positions is None:
            return "broker_snapshot missing positions"
        if not isinstance(positions, dict):
            return "broker_snapshot positions must be dict"

        meta = broker_snapshot.get("meta")
        if meta is not None and not isinstance(meta, dict):
            return "broker_snapshot meta must be dict"

        return None

    # ---------------------------------
    # policy
    # ---------------------------------

    def _determine_block_policy(
        self,
        supplier_error: Optional[str],
        engine_snapshot_error: Optional[str],
        broker_snapshot_error: Optional[str],
        broker_meta: Dict[str, Any],
        result,
    ):
        """
        우선순위:
        1) supplier failure
        2) snapshot 구조 오류
        3) broker meta integrity 오류
        4) reconciliation mismatch
        """

        if supplier_error is not None:
            return True, BlockReason.BROKER_SNAPSHOT_SUPPLIER_FAILED

        if engine_snapshot_error is not None:
            return True, BlockReason.ENGINE_SNAPSHOT_INVALID

        if broker_snapshot_error is not None:
            return True, BlockReason.BROKER_SNAPSHOT_INVALID

        invalid_rows_count = int(broker_meta.get("invalid_rows_count", 0) or 0)
        duplicate_keys_count = int(broker_meta.get("duplicate_keys_count", 0) or 0)

        if invalid_rows_count > 0:
            return True, BlockReason.BROKER_SNAPSHOT_INVALID_ROWS

        if duplicate_keys_count > 0:
            return True, BlockReason.BROKER_SNAPSHOT_DUPLICATE_KEYS

        if result.invalid_data > 0:
            return True, BlockReason.RECON_INVALID_DATA

        if result.broker_only > 0:
            return True, BlockReason.RECON_BROKER_ONLY

        if result.engine_only > 0:
            return True, BlockReason.RECON_ENGINE_ONLY

        if result.qty_mismatches > 0:
            return True, BlockReason.RECON_QTY_MISMATCH

        if result.avg_price_mismatches > 0:
            return False, BlockReason.RECON_AVG_PRICE_MISMATCH

        return False, None

    def _build_snapshot_status(
        self,
        supplier_error: Optional[str],
        engine_snapshot_error: Optional[str],
        broker_snapshot_error: Optional[str],
        broker_meta: Dict[str, Any],
    ) -> str:
        if supplier_error:
            return SnapshotStatus.SUPPLIER_FAILED

        if engine_snapshot_error:
            return SnapshotStatus.ENGINE_SNAPSHOT_INVALID

        if broker_snapshot_error:
            return SnapshotStatus.BROKER_SNAPSHOT_INVALID

        invalid_rows_count = int(broker_meta.get("invalid_rows_count", 0) or 0)
        duplicate_keys_count = int(broker_meta.get("duplicate_keys_count", 0) or 0)

        if invalid_rows_count > 0:
            return SnapshotStatus.BROKER_SNAPSHOT_INVALID_ROWS

        if duplicate_keys_count > 0:
            return SnapshotStatus.BROKER_SNAPSHOT_DUPLICATE_KEYS

        return SnapshotStatus.OK