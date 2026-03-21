"""
단순 RollingWindow 스켈레톤.

실제 구현에서는:
  - deque 기반 윈도우
  - push / snapshot / to_list 등 제공
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Generic, TypeVar, Iterable, List

T = TypeVar("T")


class RollingWindow(Generic[T]):
    def __init__(self, maxlen: int) -> None:
        self.maxlen = maxlen
        self._buf: Deque[T] = deque(maxlen=maxlen)

    def push(self, value: T) -> None:
        self._buf.append(value)

    def extend(self, values: Iterable[T]) -> None:
        self._buf.extend(values)

    def snapshot(self) -> List[T]:
        return list(self._buf)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._buf)
