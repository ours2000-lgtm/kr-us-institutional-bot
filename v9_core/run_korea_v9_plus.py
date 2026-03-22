# ======================================================================
# run_korea_v9_plus.py — 한국장 자동매매 엔진 V9 PLUS (OPS Canonical)
# - Engine logic: 기존 V9 PLUS 백업본 유지
# - OPS control: PID JSON + STOP FLAG (graceful) 흡수
# - Launcher compatibility:
#     1) argparse: --mode / --pid_json / --flag_path
#     2) env: PID_JSON / STOP_FLAG / RUN_MODE
# ======================================================================

import time
from datetime import datetime
import traceback
import os
import sys
import json
import argparse


# ----------------------------------------------------------------------
# OPS: PID JSON / STOP FLAG utilities
# ----------------------------------------------------------------------
def write_pid_json(path: str, script: str, mode: str):
    """
    Write PID meta JSON for safe ops.
    - path can be None/empty: then skip silently (engine still runs)
    """
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "pid": os.getpid(),
            "script": os.path.basename(script),
            "mode": mode,
            "started": datetime.now().isoformat(timespec="seconds"),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        # PID 기록 실패는 엔진을 멈추지 않음 (운영 편의)
        pass


def should_stop(flag_path: str) -> bool:
    return bool(flag_path) and os.path.exists(flag_path)


def resolve_ops_args():
    """
    Priority:
      1) CLI args (--mode/--pid_json/--flag_path)
      2) ENV (RUN_MODE/PID_JSON/STOP_FLAG)
      3) None/default
    """
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--mode", default=None)
    p.add_argument("--pid_json", default=None)
    p.add_argument("--flag_path", default=None)

    # unknown args 허용 (향후 확장 대비)
    args, _ = p.parse_known_args()

    mode = args.mode or os.environ.get("RUN_MODE") or None
    pid_json = args.pid_json or os.environ.get("PID_JSON") or None

    # STOP_FLAG가 표준. (이전 FLAG_PATH도 호환)
    flag_path = args.flag_path or os.environ.get("STOP_FLAG") or os.environ.get("FLAG_PATH") or None

    return mode, pid_json, flag_path


# ----------------------------------------------------------------------
# 경로 설정 (주의: v9_core 폴더 내에서 v8_core를 바라보는 구조)
# ----------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(BASE, "v8_core")  # 기존 백업본 그대로 유지
if CORE not in sys.path:
    sys.path.append(CORE)


# ----------------------------------------------------------------------
# 모듈 Import (기존 백업본 그대로)
# ----------------------------------------------------------------------
from config_loader_v8 import load_config
from data_engine_v8 import V8DataCollector
from regime_engine_v9 import RegimeEngineV9
from meta_strategy_engine_v9 import MetaStrategyEngineV9
from signal_engine_v9 import SignalEngineV9
from market_structure_v8 import MarketStructureV8
from orderflow_v8 import OrderflowV8
from ml_gate_v8 import MLQualityGateV8
from portfolio_engine_v8 import PortfolioEngineV8
from executor_engine_v9 import ExecutorEngineV9
from utils_v8 import safe_log


# ======================================================================
# 초기화 (기존 백업본 그대로)
# ======================================================================
CONFIG = load_config()
CONFIG["ENGINE"]["market"] = "KR"

# OPS args 해석: CLI/ENV로 mode 들어오면 CONFIG에 우선 적용
ops_mode, PID_JSON_PATH, STOP_FLAG_PATH = resolve_ops_args()
if ops_mode:
    CONFIG.setdefault("ENGINE", {})
    CONFIG["ENGINE"]["mode"] = ops_mode

ENGINE_MODE = CONFIG.get("ENGINE", {}).get("mode", "PAPER")

safe_log("============================================================")
safe_log("    🇰🇷 한국장 자동매매 V9 PLUS 엔진 시작 ")
safe_log("============================================================")
safe_log(f"[OPS] mode={ENGINE_MODE}")
safe_log(f"[OPS] pid_json={PID_JSON_PATH}")
safe_log(f"[OPS] stop_flag={STOP_FLAG_PATH}")

# -----------------------------
# 모듈 인스턴스 생성
# -----------------------------
data_engine      = V8DataCollector(mode=ENGINE_MODE)
regime_engine    = RegimeEngineV9(CONFIG)
meta_engine      = MetaStrategyEngineV9(CONFIG)
ml_gate          = MLQualityGateV8()

signal_engine    = SignalEngineV9(CONFIG, ml_gate)
structure_engine = MarketStructureV8(market="KR")
orderflow_engine = OrderflowV8()
portfolio        = PortfolioEngineV8(CONFIG)

# Broker는 run_all에서 주입하므로 placeholder
class DummyBroker:
    def buy(self, s, q):
        return {"status": "FILLED", "price": portfolio.mock_price(s)}
    def sell(self, s, q):
        return {"status": "FILLED", "price": portfolio.mock_price(s)}

broker = DummyBroker()

executor = ExecutorEngineV9(broker, CONFIG, portfolio, meta_engine)

safe_log("[SYSTEM] 한국장 V9 PLUS 초기화 완료")


# ======================================================================
# 스케줄 체크 (기존 백업본 그대로)
# ======================================================================
def in_trading_time():
    now = datetime.now().strftime("%H:%M:%S")
    start = CONFIG["SCHEDULE"]["KR"]["start"]
    end   = CONFIG["SCHEDULE"]["KR"]["end"]
    return start <= now <= end


def is_warmup_time():
    now = datetime.now().strftime("%H:%M:%S")
    warm = CONFIG["SCHEDULE"]["KR"]["warmup"]
    return now >= warm


# ======================================================================
# 메인 루프 (기존 백업본 + STOP_FLAG 1줄 흡수)
# ======================================================================
def main_loop():
    # --- OPS: write pid meta once at startup ---
    write_pid_json(PID_JSON_PATH, __file__, ENGINE_MODE)
    safe_log("[OPS] PID meta written (if path provided).")

    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")

            # ---------------------------------------------------------
            # [OPS] Stop flag → graceful shutdown
            # ---------------------------------------------------------
            if should_stop(STOP_FLAG_PATH):
                safe_log("[OPS] STOP flag detected → entering graceful shutdown")
                # TODO: cancel_all_orders(), flush_logs(), save_state() 등
                break

            # ---------------------------------------------------------
            # Warm-up 단계 (데이터 적재용)
            # ---------------------------------------------------------
            if not is_warmup_time():
                safe_log(f"[WAIT] Warm-up 대기중... ({now})")
                time.sleep(5)
                continue

            # ---------------------------------------------------------
            # 시장 시간 아니면 대기
            # ---------------------------------------------------------
            if not in_trading_time():
                safe_log(f"[WAIT] 한국장 거래시간 아님... ({now})")
                time.sleep(5)
                continue

            # ---------------------------------------------------------
            # 1) 데이터 수집
            # ---------------------------------------------------------
            ticks = data_engine.collect()
            if not ticks:
                time.sleep(1)
                continue

            # ---------------------------------------------------------
            # 2) 시장 레짐 업데이트
            # ---------------------------------------------------------
            market_tick = structure_engine.get_market_tick()
            regime = regime_engine.update(market_tick)

            # ---------------------------------------------------------
            # 3) 종목 처리
            # ---------------------------------------------------------
            for symbol, tick in ticks.items():
                # [OPS] 종목 루프 중간에도 stop 빠르게 반응
                if should_stop(STOP_FLAG_PATH):
                    safe_log("[OPS] STOP flag detected (mid-loop) → breaking")
                    raise SystemExit

                # 시장 구조 분석 (ORB/AVWAP/MTF)
                struct_info = structure_engine.analyze(symbol, tick)

                # 오더플로우 분석
                flow_info = orderflow_engine.analyze(symbol, tick)

                # 최종 실행 (meta + executor)
                executor.process(
                    symbol=symbol,
                    tick=tick,
                    structure=struct_info,
                    flow=flow_info,
                    regime=regime
                )

                # PnL 업데이트
                portfolio.update_pnl(symbol, tick.get("price"))

        except SystemExit:
            # stop 요청에 의한 종료 플로우
            break

        except KeyboardInterrupt:
            safe_log("[OPS] KeyboardInterrupt → stopping")
            break

        except Exception as e:
            safe_log(f"[ERROR] {e}")
            safe_log(traceback.format_exc())
            time.sleep(3)

    safe_log("[OPS] Engine loop ended. Exiting.")


# ======================================================================
# 실행
# ======================================================================
if __name__ == "__main__":
    main_loop()
