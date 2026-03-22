# =====================================================================
# utils_v8.py  (V8 PLUS — SAFE UTILS)
# 기관급 자동매매 공통 유틸리티 모듈
# - 안전 로깅
# - 예외 처리
# - JSON / YAML 입출력
# - 경로 체크
# - 시간/포맷 처리
# =====================================================================

import os
import sys
import json
import yaml
import time
import traceback
from datetime import datetime


# ---------------------------------------------------------------------
# 경로 유틸
# ---------------------------------------------------------------------
def ensure_dir(path: str):
    """폴더가 없으면 자동 생성"""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception as e:
        print(f"[폴더 생성 실패] {path} → {e}")


# ---------------------------------------------------------------------
# 로깅 (파일 + 콘솔)
# ---------------------------------------------------------------------
def safe_log(message: str, log_file: str = None):
    """
    콘솔 + 파일 모두 기록하는 안전 로그
    log_file이 없으면 콘솔 출력만 수행
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{now}] {message}"

    # 콘솔 출력
    print(msg)

    # 파일 출력
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            print(f"[로그 파일 쓰기 실패] {log_file}")


# ---------------------------------------------------------------------
# 예외 처리용 Wrapper
# ---------------------------------------------------------------------
def safe_try(func, *args, **kwargs):
    """
    함수 실행 중 오류가 발생해도 프로그램이 멈추지 않도록 보호
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------
# JSON 저장/로드
# ---------------------------------------------------------------------
def save_json(path: str, data: dict):
    """안전하게 JSON 저장"""
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[JSON 저장 실패] {path} → {e}")


def load_json(path: str):
    """JSON 로드 (없으면 None 반환)"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[JSON 로드 실패] {path} → {e}")
        return None


# ---------------------------------------------------------------------
# YAML 저장/로드
# ---------------------------------------------------------------------
def load_yaml(path: str):
    """YAML 로드"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[YAML 로드 실패] {path} → {e}")
        return None


def save_yaml(path: str, data: dict):
    """YAML 저장"""
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True)
    except Exception as e:
        print(f"[YAML 저장 실패] {path} → {e}")


# ---------------------------------------------------------------------
# 문자열/시간 유틸
# ---------------------------------------------------------------------
def now_kst():
    """한국 시간 기준 현재 시각"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_seconds(sec: float):
    """초를 보기 좋게 표시"""
    try:
        return f"{sec:.2f}s"
    except:
        return str(sec)


# ---------------------------------------------------------------------
# 에러 로그 생성기
# ---------------------------------------------------------------------
def log_exception(context: str, log_file: str = None):
    """
    try/except에서 except 부분에 사용
    """
    err = traceback.format_exc()
    msg = f"[예외 발생] {context}\n{err}"
    safe_log(msg, log_file)


# ---------------------------------------------------------------------
# 파일 잠금 방지 (Windows 권장)
# ---------------------------------------------------------------------
def safe_write_text(path: str, text: str):
    """텍스트 안전 저장 (덮어쓰기)"""
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print(f"[텍스트 저장 실패] {path} → {e}")
