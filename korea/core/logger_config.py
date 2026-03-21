import logging
import os
from datetime import datetime

def configure_logger(log_dir: str, prefix: str = "KR_ENGINE"):
    """
    log_dir: 로그 폴더 경로 (예: E:/KR_US_INSTITUTIONAL_BOT/korea/logs)
    prefix : 로그 파일 이름 접두사
    """

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 파일명: 20251120_KR_ENGINE.log
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(log_dir, f"{date_str}_{prefix}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 파일 핸들러
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 핸들러
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    logging.info("=== Logger Initialized ===")
    logging.info(f"Log file created: {log_path}")

    return logger
