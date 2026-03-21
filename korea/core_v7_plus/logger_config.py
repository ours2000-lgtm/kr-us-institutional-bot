# =============================================================
# logger_config.py
# V7 PLUS 공통 로거 설정 파일 (한국/미국 공용)
# -------------------------------------------------------------
# 특징:
#   • 날짜별 폴더 자동 생성
#   • 파일 로그 + 콘솔 로그 동시 출력
#   • UTF-8 대응
#   • 엔진 단위로 prefix 지정하여 분리 저장 가능
# =============================================================

import os
import logging
from datetime import datetime


def configure_logger(
    folder_name="KR_AUTO_V7",
    filename_prefix="ENGINE_V7"
):
    """
    folder_name   → 로그가 저장될 상위 폴더 이름
    filename_prefix → 파일명 접두사
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # logs 폴더 생성
    logs_dir = os.path.join(base_dir, "logs", folder_name)
    os.makedirs(logs_dir, exist_ok=True
