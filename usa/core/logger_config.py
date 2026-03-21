# ============================================================
#  logger_config.py — 공통 로그 설정 (KR/US 통합)
# ============================================================

import os
import logging
from datetime import datetime


def configure_logger(folder_name="KR_AUTO", filename_prefix="ENGINE"):
    """
    공통 로그 생성 함수
    folder_name : KR_AUTO / US_AUTO
    filename_prefix : KR_ENGINE / US_ENGINE
    """

    # 날짜별 로그 파일명 생성
    today = datetime.now().strftime("%Y%m%d")

    log_dir = os.path.join(folder_name)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, f"{today}_{filename_prefix}.log")

    logger = logging.getLogger(filename_prefix)
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
