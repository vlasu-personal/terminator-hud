from abc import ABC, abstractmethod

from PySide6.QtCore import QElapsedTimer, QRectF
from PySide6.QtGui import QPainter


class HudItem(ABC):
    def __init__(self) -> None:
        self._elapsed = QElapsedTimer()
        self._started = False

    @property
    @abstractmethod
    def duration_ms(self) -> int:
        raise NotImplementedError

    @property
    def elapsed_ms(self) -> int:
        return self._elapsed.elapsed() if self._started else 0

    def start(self) -> bool:
        if self._started:
            return False
        self._elapsed.start()
        self._started = True
        return True

    def has_expired(self) -> bool:
        return self._started and self.elapsed_ms >= self.duration_ms

    @abstractmethod
    def paint(self, painter: QPainter, rect: QRectF, elapsed_ms: int) -> None:
        raise NotImplementedError
