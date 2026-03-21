from decimal import Decimal

from engine.position_reconciliation import PositionReconciliationEngine


KEY = "ACC|005930|KRX|KRW|EQUITY"


def engine_snapshot(qty, avg, key=KEY):
    return {
        "positions": {
            key: {
                "qty": qty,
                "avg_price": str(avg),
            }
        }
    }


def broker_snapshot(qty, avg, key=KEY):
    return {
        "positions": {
            key: {
                "qty": qty,
                "avg_price": str(avg),
            }
        }
    }


def mismatch_types(result):
    return {m.type for m in result.mismatches}


# ---------------------------------
# exact match
# ---------------------------------

def test_reconciliation_match():
    engine = PositionReconciliationEngine()

    result = engine.reconcile(
        broker_snapshot=broker_snapshot(1, 100),
        engine_snapshot=engine_snapshot(1, 100),
    )

    assert result.matched is True
    assert len(result.mismatches) == 0


# ---------------------------------
# empty snapshots
# ---------------------------------

def test_reconciliation_empty_snapshots_match():
    engine = PositionReconciliationEngine()

    result = engine.reconcile(
        broker_snapshot={"positions": {}},
        engine_snapshot={"positions": {}},
    )

    assert result.matched is True
    assert len(result.mismatches) == 0


# ---------------------------------
# broker only
# ---------------------------------

def test_reconciliation_broker_only():
    engine = PositionReconciliationEngine()

    result = engine.reconcile(
        broker_snapshot=broker_snapshot(1, 100),
        engine_snapshot={"positions": {}},
    )

    assert result.matched is False
    assert len(result.mismatches) == 1
    assert "BROKER_ONLY" in mismatch_types(result)

    m = result.mismatches[0]
    assert m.key == KEY
    assert m.broker_qty == 1
    assert m.engine_qty is None


# ---------------------------------
# engine only
# ---------------------------------

def test_reconciliation_engine_only():
    engine = PositionReconciliationEngine()

    result = engine.reconcile(
        broker_snapshot={"positions": {}},
        engine_snapshot=engine_snapshot(1, 100),
    )

    assert result.matched is False
    assert len(result.mismatches) == 1
    assert "ENGINE_ONLY" in mismatch_types(result)

    m = result.mismatches[0]
    assert m.key == KEY
    assert m.broker_qty is None
    assert m.engine_qty == 1


# ---------------------------------
# qty mismatch
# ---------------------------------

def test_reconciliation_qty_mismatch():
    engine = PositionReconciliationEngine()

    result = engine.reconcile(
        broker_snapshot=broker_snapshot(1, 100),
        engine_snapshot=engine_snapshot(2, 100),
    )

    assert result.matched is False
    assert len(result.mismatches) == 1
    assert "QTY_MISMATCH" in mismatch_types(result)

    m = result.mismatches[0]
    assert m.key == KEY
    assert m.broker_qty == 1
    assert m.engine_qty == 2
    assert m.broker_avg == Decimal("100")
    assert m.engine_avg == Decimal("100")


# ---------------------------------
# avg price mismatch
# ---------------------------------

def test_reconciliation_avg_price_mismatch():
    engine = PositionReconciliationEngine(price_tolerance=Decimal("0.01"))

    result = engine.reconcile(
        broker_snapshot=broker_snapshot(1, 100),
        engine_snapshot=engine_snapshot(1, 100.5),
    )

    assert result.matched is False
    assert len(result.mismatches) == 1
    assert "AVG_PRICE_MISMATCH" in mismatch_types(result)

    m = result.mismatches[0]
    assert m.key == KEY
    assert m.broker_qty == 1
    assert m.engine_qty == 1
    assert m.broker_avg == Decimal("100")
    assert m.engine_avg == Decimal("100.5")


# ---------------------------------
# tolerance boundary is inclusive
# abs(diff) <= tolerance => match
# ---------------------------------

def test_reconciliation_price_tolerance_boundary_is_inclusive():
    engine = PositionReconciliationEngine(price_tolerance=Decimal("0.5"))

    result = engine.reconcile(
        broker_snapshot=broker_snapshot(1, 100),
        engine_snapshot=engine_snapshot(1, 100.5),
    )

    assert result.matched is True
    assert len(result.mismatches) == 0


# ---------------------------------
# invalid qty
# ---------------------------------

def test_reconciliation_invalid_qty_data():
    engine = PositionReconciliationEngine()

    broker = {
        "positions": {
            KEY: {
                "qty": "INVALID",
                "avg_price": "100",
            }
        }
    }

    result = engine.reconcile(
        broker_snapshot=broker,
        engine_snapshot=engine_snapshot(1, 100),
    )

    assert result.matched is False
    assert len(result.mismatches) == 1
    assert "INVALID_DATA" in mismatch_types(result)


# ---------------------------------
# invalid avg price
# ---------------------------------

def test_reconciliation_invalid_avg_price_data():
    engine = PositionReconciliationEngine()

    broker = {
        "positions": {
            KEY: {
                "qty": 1,
                "avg_price": "INVALID",
            }
        }
    }

    result = engine.reconcile(
        broker_snapshot=broker,
        engine_snapshot=engine_snapshot(1, 100),
    )

    assert result.matched is False
    assert len(result.mismatches) == 1
    assert "INVALID_DATA" in mismatch_types(result)


# ---------------------------------
# missing positions key
# policy: invalid snapshot => INVALID_DATA
# ---------------------------------

def test_reconciliation_missing_positions_key():
    engine = PositionReconciliationEngine()

    result = engine.reconcile(
        broker_snapshot={},
        engine_snapshot=engine_snapshot(1, 100),
    )

    assert result.matched is False
    assert "INVALID_DATA" in mismatch_types(result)


# ---------------------------------
# multi-symbol mixed case
# one match, one broker_only, one qty_mismatch
# ---------------------------------

def test_reconciliation_multi_symbol_mixed_case():
    engine = PositionReconciliationEngine()

    broker = {
        "positions": {
            "ACC|005930|KRX|KRW|EQUITY": {
                "qty": 1,
                "avg_price": "100",
            },
            "ACC|000660|KRX|KRW|EQUITY": {
                "qty": 2,
                "avg_price": "200",
            },
            "ACC|035420|KRX|KRW|EQUITY": {
                "qty": 3,
                "avg_price": "300",
            },
        }
    }

    engine_snap = {
        "positions": {
            "ACC|005930|KRX|KRW|EQUITY": {
                "qty": 1,
                "avg_price": "100",
            },
            "ACC|035420|KRX|KRW|EQUITY": {
                "qty": 4,
                "avg_price": "300",
            },
        }
    }

    result = engine.reconcile(
        broker_snapshot=broker,
        engine_snapshot=engine_snap,
    )

    assert result.matched is False
    assert len(result.mismatches) == 2

    types = mismatch_types(result)
    assert "BROKER_ONLY" in types
    assert "QTY_MISMATCH" in types