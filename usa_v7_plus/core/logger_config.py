import logging
import os
from datetime import datetime


def configure_logger(folder_name="US_AUTO_V7", filename_prefix="US_ENGINE_V7"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "..", "logs", folder_name)
    log_dir = os.path.abspath(log_dir)

    # 폴더 자동 생성
    os.makedirs(log_dir, exist_ok=True)

    # 파일명
    now = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{filename_prefix}_{now}.log")

    # 로거 설정
    logger = logging.getLogger(folder_name)
    logger.setLevel(logging.INFO)

    # 핸들러 초기화 (중복 방지)
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        sh = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        fh.setFormatter(formatter)
        sh.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(sh)

    return logger
