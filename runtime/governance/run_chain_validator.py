# runtime/governance/run_chain_validator.py
from __future__ import annotations

import sys
from pathlib import Path

# repo_root/runtime/governance/run_chain_validator.py  -> parents[2] == repo_root
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # import AFTER sys.path bootstrap
    from runtime.governance.chain_validator import main as chain_main  # type: ignore

    # chain_validator.main이 argv를 받아야 하는 형태면 그대로 전달
    try:
        return int(chain_main(argv))  # type: ignore[arg-type]
    except TypeError:
        # chain_validator.main이 argv를 안 받는 형태면 sys.argv로만 파싱할 수 있으니 그냥 호출
        return int(chain_main())  # type: ignore[misc]

if __name__ == "__main__":
    raise SystemExit(main())
