# ======================================================================
# config_loader_v9.py — V9 PLUS 공통 설정 로더
# ----------------------------------------------------------------------
# 기능:
#   ✔ config_v9.yaml 파일 로드
#   ✔ KR / US 개별 설정 분리 반환
#   ✔ 오류 자동 검사
#   ✔ 경로 자동 처리
# ======================================================================

import os
import yaml

# ----------------------------------------------------------------------
# YAML 읽기 함수
# ----------------------------------------------------------------------
def _read_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[CONFIG ERROR] 설정 파일을 찾지 못했습니다: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ----------------------------------------------------------------------
# 메인 설정 로더
# ----------------------------------------------------------------------
def load_config(config_dir, market):
    """
    config_dir : YAML 파일이 들어있는 폴더 경로
    market     : "KR" 또는 "US"
    """

    yaml_path = os.path.join(config_dir, "config_v9.yaml")

    # YAML 로드
    raw = _read_yaml(yaml_path)
    if raw is None:
        raise ValueError("[CONFIG ERROR] YAML 내용을 불러올 수 없습니다.")

    # 시장 설정 블록이 있는지 확인
    if "ENGINE" not in raw:
        raise KeyError("[CONFIG ERROR] 'ENGINE' 키가 없습니다.")

    # KR/US 스케줄 존재 확인
    if "SCHEDULE" not in raw:
        raise KeyError("[CONFIG ERROR] 'SCHEDULE' 키가 없습니다.")
    if market not in raw["SCHEDULE"]:
        raise KeyError(f"[CONFIG ERROR] 'SCHEDULE.{market}' 정보가 없습니다.")

    # 시장별 Universe 존재 여부 확인
    if "UNIVERSE" not in raw:
        raise KeyError("[CONFIG ERROR] 'UNIVERSE' 키가 없습니다.")
    if market not in raw["UNIVERSE"]:
        raise KeyError(f"[CONFIG ERROR] 'UNIVERSE.{market}' 정보가 없습니다.")

    # 브로커 설정 확인
    if "BROKER" not in raw:
        raise KeyError("[CONFIG ERROR] 'BROKER' 키가 없습니다.")
    if market not in raw["BROKER"]:
        raise KeyError(f"[CONFIG ERROR] 'BROKER.{market}' 설정이 없습니다.")

    # ------------------------------------------------------------------
    # 시장별 설정을 하나의 딕셔너리로 구성
    # ------------------------------------------------------------------
    CONFIG = {
        "ENGINE": raw.get("ENGINE", {}),
        "SCHEDULE": {
            market: raw["SCHEDULE"][market]
        },
        "RISK": raw.get("RISK", {}),
        "SIGNAL": raw.get("SIGNAL", {}),
        "ORDERFLOW": raw.get("ORDERFLOW", {}),
        "ML": raw.get("ML", {}),
        "PORTFOLIO": raw.get("PORTFOLIO", {}),
        "UNIVERSE": {
            market: raw["UNIVERSE"][market]
        },
        "BROKER": {
            market: raw["BROKER"][market]
        },
        "LOG": raw.get("LOG", {})
    }

    return CONFIG


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    BASE = os.path.dirname(os.path.abspath(__file__))
    CONFIG_DIR = os.path.join(BASE, "config")

    print("=== CONFIG TEST (KR) ===")
    c_kr = load_config(CONFIG_DIR, "KR")
    print(c_kr)

    print("=== CONFIG TEST (US) ===")
    c_us = load_config(CONFIG_DIR, "US")
    print(c_us)
