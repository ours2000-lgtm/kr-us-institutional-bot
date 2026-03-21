# ================================================================
#  logger_config_us_v7.py — 미국 자동매매 V7 공통 Logger 설정
# ---------------------------------------------------------------
#  특징:
#    • 날짜별 로그 파일 자동 생성
#    • 파일 + 콘솔 동시 출력
#    • 중복 핸들러 방지
#    • V7 PLUS 엔진 통합 구조 대응
# ================================================================

import os
import logging
from datetime import datetime


def get_us_logger(base_dir, prefix="US_V7"):
    """
    미국 자동매매 V7 PLUS 공통 로거 생성 함수
    base_dir : run_us_v7_plus.py 기준 루트 폴더
    prefix   : 로그 파일명 프리픽스 (기본: US_V7)
    """

    # ----------------------------
    # 1. 로그 폴더 생성
    # ----------------------------
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 날짜별 로그 파일
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{today}_{prefix}.log")

    # ----------------------------
    # 2. 로거 설정
    # ----------------------------
    logger = logging.getLogger(prefix)
    logger.setLevel(logging.INFO)

    # 핸들러 중복 추가 방지
    if logger.handlers:
        return logger

    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_format)

    # 로거에 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("=== 미국 자동매매 V7 PLUS Logger Initialized ===")

    return logger
