# ======================================================================
# run_korea_v9_plus.py — 한국장 자동매매 엔진 V9 PLUS (OPS Canonical)
# - Supports: --mode / --pid_json / --flag_path
# - Also supports env fallback: RUN_MODE / PID_JSON / STOP_FLAG
# - PID JSON meta written at start, updated on shutdown
# - stop.flag detected => graceful CLOSEOUT (no new orders) -> exit
# ======================================================================

import os
import sys
import json
import time
import traceback
import argparse
from datetime import datetime

# ----------------------------------------------------------------------
# Helpers: logging / pid meta / stop flag
# ----------------------------------------------------------------------
def now_ts() -> str:
    return datetime.now().isoformat(timespec="seconds")

def write_pid_json(path: str, script: str, mode: str, flag_path: str, extra: dict | None = None):
    """
    Write or update PID meta JSON.
    """
    if not path:
        raise ValueError("pid_json path is empty (None/blank).")

    dirn = os.path.dirname(path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)

    data = {
        "pid": os.getpid(),
        "script": os.path.basename(script),
        "mode": mode,
        "started": now_ts(),
        "flag_path": flag_path,
        "status": "RUNNING",
    }
    if extra:
        data.update(extra)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_pid_json(path: str, updates: dict):
    """
    Update existing pid json if exists; otherwise ignore.
    """
    if not path:
        return
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        data.update(updates)
        dirn = os.path.dirname(path)
        if dirn:
            os.makedirs(dirn, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        # pid meta update must never crash engine
        pass

def should_stop(flag_path: str) -> bool:
    return bool(flag_path) and os.path.exists(flag_path)

def read_stop_reason(flag_path: str) -> str:
    if not flag_path or not os.path.exists(flag_path):
        return ""
    try:
        with open(flag_path, "r", encoding="utf-8", errors="ignore") as f:
            return (f.read() or "").strip()
    except Exception:
        return ""

# ----------------------------------------------------------------------
# Import resolution (v9_core directory)
# - Your folder shows v9_core/*.py directly (no v8_core folder).
# - We therefore add BASE to sys.path and import modules by name.
# ----------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# ----------------------------------------------------------------------
# Safe import: prefer v9 modules if present; fallback to v8-named ones
# ----------------------------------------------------------------------
def _import_any(primary: str, fallback: str):
    try:
        return __import__(primary, fromlist=["*"])
    except Exception:
        return __import__(fallback, fromlist=["*"])

# config loader
_config_mod = _import_any("config_loader_v9", "config_loader_v8")
load_config = getattr(_config_mod, "load_config")

# data collector
_data_mod = _import_any("data_engine_v9", "data_engine_v8")
V8DataCollector = getattr(_data_mod, "V8DataCollector", None)  # keep original name if defined
if V8DataCollector is None:
    # if v9 file uses a different class name, adapt here if needed later
    raise ImportError("Could not find V8DataCollector in data_engine_v9/v8.")

# rest modules
RegimeEngineV9        = getattr(_import_any("regime_engine_v9", "regime_engine_v9"), "RegimeEngineV9")
MetaStrategyEngineV9  = getattr(_import_any("meta_strategy_engine_v9", "meta_strategy_engine_v9"), "MetaStrategyEngineV9")
SignalEngineV9        = getattr(_import_any("signal_engine_v9", "signal_engine_v9"), "SignalEngineV9")

MarketStructureV8     = getattr(_import_any("market_structure_v9", "market_structure_v8"), "MarketStructureV8")
OrderflowV8           = getattr(_import_any("orderflow_v9", "orderflow_v8"), "OrderflowV8")
MLQualityGateV8       = getattr(_import_any("ml_gate_v9", "ml_gate_v8"), "MLQualityGateV8")
PortfolioEngineV8     = getattr(_import_any("portfolio_engine_v9", "portfolio_engine_v8"), "PortfolioEngineV8")
ExecutorEngineV9      = getattr(_import_any("executor_engine_v9_plus", "executor_engine_v9"), "ExecutorEngineV9", None)
if ExecutorEngineV9 is None:
    ExecutorEngineV9  = getattr(_import_any("executor_engine_v9", "executor_engine_v9"), "ExecutorEngineV9")

_utils_mod = _import_any("utils_v9", "utils_v8")
safe_log = getattr(_utils_mod, "safe_log")

# ----------------------------------------------------------------------
# CLI / ENV
# ----------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default=None, help="RUN MODE (PAPER/LIVE etc.)")
    p.add_argument("--pid_json", default=None, help="PID meta json path")
    p.add_argument("--flag_path", default=None, help="stop.flag path")
    return p.parse_args()

def resolve_runtime_params(args):
    # priority: cli > env > defaults
    mode = (args.mode or os.environ.get("RUN_MODE") or os.environ.get("MODE") or "PAPER").strip()

    pid_json = (args.pid_json or os.environ.get("PID_JSON") or "").strip() or None

    # launcher uses STOP_FLAG; some earlier drafts used FLAG_PATH
    flag_path = (args.flag_path or os.environ.get("STOP_FLAG") or os.environ.get("FLAG_PATH") or "").strip() or None

    return mode, pid_json, flag_path

# ----------------------------------------------------------------------
# Original schedule helpers (unchanged)
# ----------------------------------------------------------------------
def in_trading_time(CONFIG):
    now = datetime.now().strftime("%H:%M:%S")
    start = CONFIG["SCHEDULE"]["KR"]["start"]
    end   = CONFIG["SCHEDULE"]["KR"]["end"]
    return start <= now <= end

def is_warmup_time(CONFIG):
    now = datetime.now().strftime("%H:%M:%S")
    warm = CONFIG["SCHEDULE"]["KR"]["warmup"]
    return now >= warm

# ----------------------------------------------------------------------
# Engine main loop (keeps your original logic, adds stop.flag checks)
# ----------------------------------------------------------------------
def main_loop(CONFIG, data_engine, regime_engine, meta_engine, ml_gate, signal_engine,
              structure_engine, orderflow_engine, portfolio, executor,
              pid_json: str | None, flag_path: str | None, mode: str):

    safe_log("============================================================")
    safe_log("    🇰🇷 한국장 자동매매 V9 PLUS 엔진 시작 (OPS) ")
    safe_log("============================================================")
    safe_log(f"[OPS] mode={mode}")
    safe_log(f"[OPS] pid_json={pid_json}")
    safe_log(f"[OPS] flag_path={flag_path}")

    # PID meta write (once at start)
    if pid_json:
        write_pid_json(
            pid_json,
            __file__,
            mode,
            flag_path or "",
            extra={
                "started_local": now_ts(),
            },
        )

    safe_log("[SYSTEM] 한국장 V9 PLUS 초기화 완료")

    while True:
        try:
            # --- stop.flag first (FAIL-CLOSED) ---
            if should_stop(flag_path):
                reason = read_stop_reason(flag_path)
                safe_log(f"[OPS] stop.flag detected -> entering CLOSEOUT (reason={reason})")

                # TODO: put your closeout sequence here if you have it:
                # - block new orders
                # - cancel open orders
                # - flush logs/state
                # For now, we just exit loop.

                if pid_json:
                    update_pid_json(pid_json, {"status": "STOP_REQUESTED", "stop_reason": reason, "stop_seen_at": now_ts()})
                break

            now = datetime.now().strftime("%H:%M:%S")

            # Warm-up 단계
            if not is_warmup_time(CONFIG):
                safe_log(f"[WAIT] Warm-up 대기중... ({now})")
                time.sleep(5)
                continue

            # 시장 시간 아니면 대기
            if not in_trading_time(CONFIG):
                safe_log(f"[WAIT] 한국장 거래시간 아님... ({now})")
                time.sleep(5)
                continue

            # 1) 데이터 수집
            ticks = data_engine.collect()
            if not ticks:
                time.sleep(1)
                continue

            # 2) 시장 레짐 업데이트
            market_tick = structure_engine.get_market_tick()
            regime = regime_engine.update(market_tick)

            # 3) 종목 처리
            for symbol, tick in ticks.items():
                # stop.flag mid-loop (faster response)
                if should_stop(flag_path):
                    reason = read_stop_reason(flag_path)
                    safe_log(f"[OPS] stop.flag detected during loop -> CLOSEOUT (reason={reason})")
                    if pid_json:
                        update_pid_json(pid_json, {"status": "STOP_REQUESTED", "stop_reason": reason, "stop_seen_at": now_ts()})
                    raise SystemExit(0)

                struct_info = structure_engine.analyze(symbol, tick)
                flow_info   = orderflow_engine.analyze(symbol, tick)

                executor.process(
                    symbol=symbol,
                    tick=tick,
                    structure=struct_info,
                    flow=flow_info,
                    regime=regime
                )

                portfolio.update_pnl(symbol, tick.get("price"))

        except SystemExit:
            break
        except KeyboardInterrupt:
            safe_log("[OPS] KeyboardInterrupt -> exiting")
            break
        except Exception as e:
            safe_log(f"[ERROR] {e}")
            safe_log(traceback.format_exc())
            time.sleep(3)

    # shutdown
    if pid_json:
        update_pid_json(pid_json, {"status": "STOPPED", "stopped": now_ts()})

    safe_log("[OPS] engine exiting now.")
    sys.exit(0)

# ----------------------------------------------------------------------
# Entry
# ----------------------------------------------------------------------
def main():
    args = parse_args()
    mode, pid_json, flag_path = resolve_runtime_params(args)

    # ---- original init (kept) ----
    CONFIG = load_config()
    CONFIG["ENGINE"]["market"] = "KR"

    # Force mode if you want to override CONFIG's engine.mode:
    # (We keep your original CONFIG mode usage but ensure it exists)
    if "ENGINE" not in CONFIG:
        CONFIG["ENGINE"] = {}
    if "mode" not in CONFIG["ENGINE"]:
        CONFIG["ENGINE"]["mode"] = mode
    else:
        # Prefer runtime mode for OPS consistency
        CONFIG["ENGINE"]["mode"] = mode

    data_engine       = V8DataCollector(mode=CONFIG["ENGINE"]["mode"])
    regime_engine     = RegimeEngineV9(CONFIG)
    meta_engine       = MetaStrategyEngineV9(CONFIG)
    ml_gate           = MLQualityGateV8()
    signal_engine     = SignalEngineV9(CONFIG, ml_gate)
    structure_engine  = MarketStructureV8(market="KR")
    orderflow_engine  = OrderflowV8()
    portfolio         = PortfolioEngineV8(CONFIG)

    class DummyBroker:
        def buy(self, s, q):  return {"status": "FILLED", "price": portfolio.mock_price(s)}
        def sell(self, s, q): return {"status": "FILLED", "price": portfolio.mock_price(s)}

    broker   = DummyBroker()
    executor = ExecutorEngineV9(broker, CONFIG, portfolio, meta_engine)

    main_loop(
        CONFIG=CONFIG,
        data_engine=data_engine,
        regime_engine=regime_engine,
        meta_engine=meta_engine,
        ml_gate=ml_gate,
        signal_engine=signal_engine,
        structure_engine=structure_engine,
        orderflow_engine=orderflow_engine,
        portfolio=portfolio,
        executor=executor,
        pid_json=pid_json,
        flag_path=flag_path,
        mode=mode,
    )

if __name__ == "__main__":
    main()
