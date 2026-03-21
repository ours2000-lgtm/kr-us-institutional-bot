from pathlib import Path


class IdempotencyIndex:

    def __init__(self, path: str):
        self.path = Path(path)
        self.seen = set()

        # 디렉터리 보장
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if self.path.exists():
            self._load()

    def _load(self):
        try:
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    key = line.strip()
                    if key:
                        self.seen.add(key)
        except Exception:
            # index는 캐시이므로 실패 시 초기화
            self.seen = set()

    def exists(self, key: str) -> bool:
        return key in self.seen

    def add(self, key: str):
        if key in self.seen:
            return

        self.seen.add(key)

        with self.path.open("a", encoding="utf-8") as f:
            f.write(key + "\n")