from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SnapshotStatus:
    OK = "OK"
    SUPPLIER_FAILED = "SUPPLIER_FAILED"
    ENGINE_SNAPSHOT_INVALID = "ENGINE_SNAPSHOT_INVALID"
    BROKER_SNAPSHOT_INVALID = "BROKER_SNAPSHOT_INVALID"
    BROKER_SNAPSHOT_INVALID_ROWS = "BROKER_SNAPSHOT_INVALID_ROWS"
    BROKER_SNAPSHOT_DUPLICATE_KEYS = "BROKER_SNAPSHOT_DUPLICATE_KEYS"


class BlockReason:
    BROKER_SNAPSHOT_SUPPLIER_FAILED = "BROKER_SNAPSHOT_SUPPLIER_FAILED"
    ENGINE_SNAPSHOT_INVALID = "ENGINE_SNAPSHOT_INVALID"
    BROKER_SNAPSHOT_INVALID = "BROKER_SNAPSHOT_INVALID"
    BROKER_SNAPSHOT_INVALID_ROWS = "BROKER_SNAPSHOT_INVALID_ROWS"
    BROKER_SNAPSHOT_DUPLICATE_KEYS = "BROKER_SNAPSHOT_DUPLICATE_KEYS"
    RECON_INVALID_DATA = "RECON_INVALID_DATA"
    RECON_BROKER_ONLY = "RECON_BROKER_ONLY"
    RECON_ENGINE_ONLY = "RECON_ENGINE_ONLY"
    RECON_QTY_MISMATCH = "RECON_QTY_MISMATCH"
    RECON_AVG_PRICE_MISMATCH = "RECON_AVG_PRICE_MISMATCH"


@dataclass
class ReconciliationMismatch:
    key: str
    type: str
    broker_qty: Optional[str] = None
    engine_qty: Optional[str] = None
    broker_avg: Optional[str] = None
    engine_avg: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None


@dataclass
class ReconciliationResult:
    matched: bool
    broker_positions: int
    engine_positions: int
    qty_mismatches: int = 0
    avg_price_mismatches: int = 0
    broker_only: int = 0
    engine_only: int = 0
    invalid_data: int = 0
    mismatches: List[ReconciliationMismatch] = field(default_factory=list)