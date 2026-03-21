from abc import ABC, abstractmethod


class IStrategy(ABC):

    @abstractmethod
    def on_tick(self, state, tick):
        """
        tick을 받아 Signal 생성

        return Signal | None
        """
        pass