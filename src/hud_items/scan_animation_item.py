from PySide6.QtCore import QLineF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen

from .huditem import HudItem


class ScanAnimationItem(HudItem):
    GRID_SIZE = 8

    def __init__(self, lifetime_ms: int = 3000) -> None:
        super().__init__()
        self._lifetime_ms = lifetime_ms

    @property
    def duration_ms(self) -> int:
        return self._lifetime_ms

    def paint(self, painter: QPainter, rect: QRectF, elapsed_ms: int) -> None:
        grid_width = rect.width() * 0.8
        grid_height = rect.height() * 0.8
        grid_rect = QRectF(
            rect.center().x() - grid_width / 2,
            rect.center().y() - grid_height / 2,
            grid_width,
            grid_height,
        )

        painter.setPen(QPen(QColor(255, 255, 255, 145), 1))
        for grid_line in range(1, self.GRID_SIZE):
            x = grid_rect.left() + grid_rect.width() * grid_line / self.GRID_SIZE
            y = grid_rect.top() + grid_rect.height() * grid_line / self.GRID_SIZE
            painter.drawLine(QLineF(x, grid_rect.top(), x, grid_rect.bottom()))
            painter.drawLine(QLineF(grid_rect.left(), y, grid_rect.right(), y))

        painter.setPen(QPen(QColor(255, 255, 255, 240), 2))
        painter.drawRect(grid_rect)

        progress = min(elapsed_ms / max(1, self._lifetime_ms), 1.0)
        search_position = 1 - abs(2 * progress - 1)
        cross_x = grid_rect.left() + grid_rect.width() * search_position
        cross_y = grid_rect.top() + grid_rect.height() * search_position
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(QLineF(cross_x, grid_rect.top(), cross_x, grid_rect.bottom()))
        painter.drawLine(QLineF(grid_rect.left(), cross_y, grid_rect.right(), cross_y))
