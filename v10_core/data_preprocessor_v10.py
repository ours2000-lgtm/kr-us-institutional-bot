# =====================================================================
# Data Preprocessor V10 — Feature Engineering & Cleaning Layer
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import pandas as pd
import numpy as np


@dataclass
class PreprocessConfig:
    fill_method: str = "ffill"
    scale_method: str = "zscore"   # "zscore" or "minmax"
    clip_outliers: bool = True
    outlier_sigma: float = 4.0     # Z-score 기준
    add_features: bool = True      # 기술 지표 포함 여부


class DataPreprocessorV10:
    """
    V10 전처리 엔진
    - 결측치 처리
    - 이상치 제거
    - 정규화/스케일링
    - 변동성/수익률 계산
    - 기술적 지표 자동 생성
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.cfg = PreprocessConfig(**(config or {}))

    # ================================================================
    # 1) 결측치 보정
    # ================================================================
    def _fill_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.replace([np.inf, -np.inf], np.nan, inplace=True)

        if self.cfg.fill_method == "ffill":
            df.fillna(method="ffill", inplace=True)
            df.fillna(method="bfill", inplace=True)
        elif self.cfg.fill_method == "zero":
            df.fillna(0, inplace=True)
        else:
            df.fillna(method="ffill", inplace=True)

        return df

    # ================================================================
    # 2) 이상치 제거 / 클리핑
    # ================================================================
    def _clip_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.cfg.clip_outliers:
            return df

        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col]
            mean = series.mean()
            std = series.std()
            upper = mean + self.cfg.outlier_sigma * std
            lower = mean - self.cfg.outlier_sigma * std
            df[col] = series.clip(lower, upper)

        return df

    # ================================================================
    # 3) 스케일링 (zscore / minmax)
    # ================================================================
    def _scale(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if self.cfg.scale_method == "zscore":
            for col in numeric_cols:
                mean = df[col].mean()
                std = df[col].std() or 1e-9
                df[col] = (df[col] - mean) / std

        elif self.cfg.scale_method == "minmax":
            for col in numeric_cols:
                min_val = df[col].min()
                max_val = df[col].max()
                rng = max_val - min_val if max_val != min_val else 1e-9
                df[col] = (df[col] - min_val) / rng

        return df

    # ================================================================
    # 4) 기술 지표 (ATR / RSI / VOL / MOM 등)
    # ================================================================
    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.cfg.add_features:
            return df

        df = df.copy()

        # 1) 수익률 & ATR
        df["return"] = df["close"].pct_change().fillna(0)
        df["volatility"] = df["return"].rolling(20).std().fillna(0)

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr = np.maximum(high - low,
                        np.maximum(abs(high - close.shift()), abs(low - close.shift())))
        df["ATR14"] = tr.rolling(14).mean().fillna(0)

        # 2) RSI
        delta = close.diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        roll_up = pd.Series(gain).rolling(14).mean()
        roll_down = pd.Series(loss).rolling(14).mean()
        rs = roll_up / (roll_down + 1e-9)
        df["RSI14"] = 100 - (100 / (1 + rs))

        # 3) 이동평균 기반 모멘텀
        df["MA20"] = close.rolling(20).mean().fillna(method="bfill")
        df["MA60"] = close.rolling(60).mean().fillna(method="bfill")
        df["MOM20"] = close / df["MA20"] - 1
        df["MOM60"] = close / df["MA60"] - 1

        return df

    # ================================================================
    # 5) 전처리 전체 파이프라인
    # ================================================================
    def preprocess_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or len(df) == 0:
            return pd.DataFrame()

        df = self._fill_missing(df)
        df = self._clip_outliers(df)
        df = self._add_features(df)
        df = self._scale(df)

        return df
