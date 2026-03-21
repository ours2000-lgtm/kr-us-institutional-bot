import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
V2_DIR = BASE_DIR / "v2"

# 생성할 폴더 구조 정의
FOLDERS = [
    "core",
    "factor",
    "factor/calculators",
    "factor/window",
    "policy",
    "policy/overrides",
    "aggregation",
    "aggregation/calculators",
    "orchestrator",
    "tests",
    "config",
]

# 생성할 파일 정의 (필요한 경우 자동으로 빈 파일 생성)
FILES = {
    "core/engine_base.py": "",
    "core/core_wrapper.py": "",
    "factor/factor_engine.py": "",
    "factor/feature_utils.py": "",
    "factor/calculators/volatility.py": "",
    "factor/calculators/liquidity.py": "",
    "factor/calculators/imbalance.py": "",
    "factor/calculators/volume.py": "",
    "factor/window/sliding_window.py": "",
    "policy/policy_engine.py": "",
    "policy/regime_classifier.py": "",
    "policy/overrides/override_engine.py": "",
    "policy/overrides/override_rules.yaml": "# override rules here\n",
    "aggregation/aggregation_engine.py": "",
    "aggregation/calculators/exposure.py": "",
    "aggregation/calculators/leverage.py": "",
    "aggregation/calculators/risk_score.py": "",
    "aggregation/calculators/merge.py": "",
    "orchestrator/orchestrator_v2_plus.py": "",
    "tests/test_connection_v1_11_v2_plus.py": "",
    "config/factors.yaml": "# factor config\n",
    "config/policies.yaml": "# policy config\n",
    "config/overrides.yaml": "# override config\n",
    "config/aggregation.yaml": "# aggregation config\n",
}

def main():
    print(f"Creating V2 folder structure under: {V2_DIR}")
    V2_DIR.mkdir(exist_ok=True)

    # 폴더 생성
    for folder in FOLDERS:
        path = V2_DIR / folder
        path.mkdir(parents=True, exist_ok=True)
        # __init__.py 자동 생성
        init_file = path / "__init__.py"
        init_file.touch(exist_ok=True)

    # 파일 생성
    for file_path, content in FILES.items():
        path = V2_DIR / file_path
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    print("Completed! Folder structure created.")

if __name__ == "__main__":
    main()
