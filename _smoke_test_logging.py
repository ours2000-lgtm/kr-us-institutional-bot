# _smoke_test_logging.py
import logging
from risk_engine.infra.logging_adapter import log_info


class DummyCtx:
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id


if __name__ == "__main__":
    # 콘솔 로깅 설정 (smoke test 전용)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s trace_id=%(trace_id)s",
    )

    ctx = DummyCtx(trace_id="abc123")
    log_info("SMOKE TEST: trace_id should appear", ctx=ctx)
