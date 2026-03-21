# =============================================================
#  logger_config_kr_v7_plus.py
#  한국 V7 PLUS 자동매매 엔진 전용 로거 설정
# =============================================================

import os
import logging
from datetime import datetime


def get_kr_logger(name="KR_V7_PLUS"):
    """
    한국장 V7 PLUS 전용 로거 생성
    - 로그는 /korea/KR_PLUS_LOG_V7/ 폴더에 날짜별로 생성
    """

    # 로그 폴더
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "KR_PLUS_LOG_V7")
    os.makedirs(log_dir, exist_ok=True)

    # 날짜 기반 로그 파일명
    today = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(log_dir, f"{today}_KR_V7_PLUS.log")

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        stream_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
