# 경로: E:\AI_TRADING\KR_US_INSTITUTIONAL_BOT\v2\utils\logger.py

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def get_logger(name: str, log_dir: str | None = None) -> logging.Logger:
    """
    V2 공용 로거 생성 스켈레톤.
    - 매일 롤링되는 파일 핸들러
    - 콘솔 핸들러
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    # 파일
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            filename=str(Path(log_dir) / f"{name}.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger
