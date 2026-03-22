import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


# ============================================================
# 기본 경로 / 시간 함수
# ============================================================

def now_kst():
    """현재 KST(한국 시간) 반환"""
    return datetime.utcnow() + timedelta(hours=9)


def timestamp():
    return now_kst().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: str):
    """폴더가 없으면 자동 생성"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


# ============================================================
# 안전 로그 처리
# ============================================================

def safe_log(msg: str, level="info"):
    """터미널 깨짐 방지 + 안전 출력"""
    try:
        clean = msg.encode("utf-8", "replace").decode("utf-8")
    except:
        clean = str(msg)

    if level == "info":
        logging.info(clean)
    elif level == "error":
        logging.error(clean)
    elif level == "warn":
        logging.warning(clean)
    else:
        print(clean)


# ============================================================
# 로거 초기화
# ============================================================

def init_logger(log_dir: str, name: str = "engine"):
    """자동 회전 로그 시스템"""
    ensure_dir(log_dir)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if logger.handlers:
        return logger

    log_path = os.path.join(log_dir, f"{name}.log")

    handler = TimedRotatingFileHandler(
        log_path, when="midnight", interval=1, backupCount=10, encoding="utf-8"
    )
    handler.suffix = "%Y-%m-%d"

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(fmt)

    logger.addHandler(handler)

    # 터미널 출력용
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    return logger


# ============================================================
# JSON / 파일 유틸
# ============================================================

def save_json(path: str, data: dict):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 시간 체크 도구
# ============================================================

def is_time_between(start: str, end: str):
    """
    start/end: "HH:MM:SS"
    예) is_time_between("09:00:00", "15:20:00")
    """
    now = now_kst().time()
    s = datetime.strptime(start, "%H:%M:%S").time()
    e = datetime.strptime(end, "%H:%M:%S").time()
    return s <= now <= e


# ============================================================
# 에러 안전 실행 래퍼
# ============================================================

def safe_run(func, *args, **kwargs):
    """
    안전 실행 래퍼 — 함수 실행 시 오류 발생해도 엔진 전체는 유지.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        safe_log(f"[ERROR] safe_run: {e}", level="error")
        return None
