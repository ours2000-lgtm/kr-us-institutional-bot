import sys
import os
from datetime import datetime, timezone

from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

# ---- 프로젝트 루트 import 안정화 ----
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# ---- GOV_HEALTH ----
from runtime.observability.health.evaluator import HealthEvaluator, HealthConfig
from runtime.observability.health.snapshot_emitter import SnapshotEmitter
from runtime.observability.health.contracts import IncidentEvent, Severity


def main():
    app = QApplication(sys.argv)

    health_cfg = HealthConfig(evaluate_interval_sec=10)

    health = HealthEvaluator(
        health_cfg,
        strategy_weights={"KIWOOM_PAPER": 1.0},
    )

    # 테스트: 즉시 snapshot 기록
    emitter = SnapshotEmitter(
        base_dir="E:\\KR_US_INSTITUTIONAL_BOT",
        snapshot_interval_sec=0,
        flush_each_write=True,
    )

    ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

    loop = QEventLoop()

    def on_event_connect(err_code):
        print("OnEventConnect err_code =", err_code)

        # 🔥🔥🔥 강제 SEV4 2회 주입 (RED 확정)
        now = datetime.now(timezone.utc)

        health.ingest(
            IncidentEvent(
                ts_utc=now,
                strategy_id="KIWOOM_PAPER",
                incident_code="FORCE_TEST_1",
                severity=Severity.SEV4,
                count=1,
            )
        )

        health.ingest(
            IncidentEvent(
                ts_utc=now,
                strategy_id="KIWOOM_PAPER",
                incident_code="FORCE_TEST_2",
                severity=Severity.SEV4,
                count=1,
            )
        )

        loop.quit()

    ocx.OnEventConnect.connect(on_event_connect)

    print("Calling CommConnect() ...")
    ocx.dynamicCall("CommConnect()")

    loop.exec_()

    # 평가 + emit
    result = health.evaluate(datetime.now(timezone.utc))
    emitter.emit_evaluation(result)

    print("GLOBAL:", result.global_snapshot.global_state,
          result.global_snapshot.global_score)


if __name__ == "__main__":
    main()