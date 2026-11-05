from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter

from .huditem import HudItem


class TextItem(HudItem):
    def __init__(self, text: str, char_interval_ms: int = 45, lifetime_ms: int = 3000, blink_interval_ms: int | None = None) -> None:
        super().__init__()
        self._text = text
        self._char_interval_ms = char_interval_ms
        self._lifetime_ms = lifetime_ms
        self._blink_interval_ms = blink_interval_ms

    @property
    def typing_duration_ms(self) -> int:
        return max(0, len(self._text) - 1) * self._char_interval_ms

    @property
    def duration_ms(self) -> int:
        return self.typing_duration_ms + self._lifetime_ms

    def paint(self, painter: QPainter, rect: QRectF, elapsed_ms: int) -> None:
        visible_characters = min(len(self._text), elapsed_ms // self._char_interval_ms + 1)
        text = self._text[:visible_characters]
        if (self._blink_interval_ms is not None and elapsed_ms >= self.typing_duration_ms):
            blink_phase = ((elapsed_ms - self.typing_duration_ms) // self._blink_interval_ms)
            if blink_phase % 2:
                return

        font = QFont("Consolas")
        font.setPixelSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, text)
