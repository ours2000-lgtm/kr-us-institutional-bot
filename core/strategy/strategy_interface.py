from abc import ABC, abstractmethod


class IStrategy(ABC):

    @abstractmethod
    def on_tick(self, state, tick):
        """
        tick 수신 시 전략 로직 실행

        state : 전략 상태 / 포트폴리오 정보
        tick  : 실시간 시장 데이터
        """

        pass