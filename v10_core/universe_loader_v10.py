# =====================================================================
# Universe Loader V10 — 기본 Universe + 실시간 Candidate Layer 통합 버전
# =====================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import csv
import os
import time


# =====================================================================
# 데이터 구조: UniverseResult
# =====================================================================
@dataclass
class UniverseResult:
    symbols: List[str]                # 최종 종목 리스트
    base_symbols: List[str]           # 기본 Universe
    candidate_symbols: List[str]      # 실시간 포착 Universe
    timestamp: float = field(default_factory=time.time)


# =====================================================================
# Universe Loader V10 
# - 기본 Universe (CSV)
# - 실시간 Candidate Layer (DataCollector 제공)
# - 중복 제거 + 정렬 + 필터 처리
# =====================================================================
class UniverseLoaderV10:

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 기본 Universe 파일 경로
        base_dir = config.get("UNIVERSE", {}).get("base_dir", "universe")
        self.kr_file = os.path.join(base_dir, "universe_kr.csv")
        self.us_file = os.path.join(base_dir, "universe_us.csv")
        self.crypto_file = os.path.join(base_dir, "universe_crypto.csv")

        # candidate 관련 설정
        self.max_candidates = int(config.get("UNIVERSE", {}).get("max_candidates", 30))
        self.candidate_ttl = int(config.get("UNIVERSE", {}).get("candidate_ttl_sec", 900))  # 15분

        # 내부 캐시
        self._candidate_cache: Dict[str, float] = {}  # {symbol: timestamp}


    # -----------------------------------------------------------------
    # CSV 읽기 (기본 Universe)
    # -----------------------------------------------------------------
    def _read_csv(self, file_path: str) -> List[str]:
        if not os.path.exists(file_path):
            return []
        symbols = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) > 0 and row[0].strip():
                        symbols.append(row[0].strip().upper())
            return symbols
        except:
            return []


    # -----------------------------------------------------------------
    # Candidate 추가 (DataCollector가 제공)
    # -----------------------------------------------------------------
    def add_candidates(self, symbols: List[str]):
        now = time.time()
        for sym in symbols:
            sym = sym.upper()
            self._candidate_cache[sym] = now


    # -----------------------------------------------------------------
    # Candidate 만료 처리
    # -----------------------------------------------------------------
    def _prune_candidates(self):
        now = time.time()
        keys = list(self._candidate_cache.keys())
        for sym in keys:
            ts = self._candidate_cache[sym]
            if now - ts > self.candidate_ttl:
                del self._candidate_cache[sym]


    # -----------------------------------------------------------------
    # 최종 Universe 생성
    # -----------------------------------------------------------------
    def load_universe(self, market: str) -> UniverseResult:
        """
        market: "KR", "US", "CRYPTO"
        """

        # (1) 기본 Universe 로드
        if market.upper() == "KR":
            base = self._read_csv(self.kr_file)
        elif market.upper() == "US":
            base = self._read_csv(self.us_file)
        elif market.upper() == "CRYPTO":
            base = self._read_csv(self.crypto_file)
        else:
            base = []

        # (2) Candidate 만료 정리
        self._prune_candidates()

        # (3) Candidate 리스트 생성 (TTL 내 데이터만)
        candidates = sorted(self._candidate_cache.keys())

        # (4) 개수 제한
        candidates = candidates[: self.max_candidates]

        # (5) 기본 + candidate 통합
        final_universe = sorted(set(base + candidates))

        return UniverseResult(
            symbols=final_universe,
            base_symbols=base,
            candidate_symbols=candidates,
        )


# =====================================================================
# 사용 예시 (run 파일 내부)
# =====================================================================
if __name__ == "__main__":
    import yaml

    config = yaml.safe_load(open("config_v10.yaml", "r", encoding="utf-8"))

    loader = UniverseLoaderV10(config)

    # DataCollector가 급등 종목을 포착했다고 가정
    loader.add_candidates(["TSLA", "NVDA"])

    res = loader.load_universe("US")

    print("[FINAL UNIVERSE]", res.symbols)
    print("[BASE]", res.base_symbols)
    print("[CANDIDATE]", res.candidate_symbols)
