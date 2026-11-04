import cv2
import numpy as np
from dataclasses import dataclass

from PySide6.QtCore import Qt, QRectF, QElapsedTimer, QTimer
from PySide6.QtGui import QCloseEvent, QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QMainWindow, QWidget
from optical_unit import OpticalUnit


@dataclass(slots=True)
class _TextOverlay:
    text: str
    char_interval_ms: int
    lifetime_ms: int
    blink_interval_ms: int | None
    elapsed: QElapsedTimer

    @property
    def typing_duration_ms(self) -> int:
        return max(0, len(self.text) - 1) * self.char_interval_ms


class Hud(QMainWindow):
    def __init__(self, hud_name: str, visual_input: OpticalUnit):
        super().__init__()
        self.setWindowTitle(hud_name)
        self.resize(960, 600)
        self._visual_input = visual_input
        self._display = self._Display()
        self.setCentralWidget(self._display)
        self._stopping = False

    def print_text(self, text: str, *, slot: int, char_interval_ms: int = 45, lifetime_ms: int = 3000, blink_interval_ms: int | None = None) -> int | None:
        return self._display.add_text(text, slot, char_interval_ms, lifetime_ms, blink_interval_ms)

    def start_display(self) -> None:
        self._visual_input.on_frame_ready.connect(self._process_frame)
        self._visual_input.on_error.connect(self._process_visual_unit_error)
        self._visual_input.finished.connect(self._close_after_visual_input_stops)
        self._visual_input.start()
        self.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._visual_input.isRunning():
            event.accept()
            return
        event.ignore()
        if not self._stopping:
            self._stopping = True
            self._visual_input.requestInterruption()

    def _close_after_visual_input_stops(self) -> None:
        if self._stopping:
            self._visual_input.wait()
            self.close()

    def _process_frame(self, frame: np.ndarray) -> None:
        optical_luminance = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        red_phosphor = cv2.convertScaleAbs(
            optical_luminance,
            alpha=1.25,
            beta=-16,
        )
        ember_highlights = cv2.convertScaleAbs(red_phosphor, alpha=0.16)
        no_blue = cv2.subtract(red_phosphor, red_phosphor)
        phosphor_bgr = cv2.merge((no_blue, ember_highlights, red_phosphor))
        phosphor_rgb = cv2.cvtColor(phosphor_bgr, cv2.COLOR_BGR2RGB)
        frame_height, frame_width, _ = phosphor_rgb.shape
        display_frame = QImage(
            phosphor_rgb.data,
            frame_width,
            frame_height,
            phosphor_rgb.strides[0],
            QImage.Format.Format_RGB888,
        ).copy()
        self._display.set_frame(display_frame)

    def _process_visual_unit_error(self, message: str) -> None:
        self._display.set_status(message)

    class _Display(QWidget):
        def __init__(self):
            super().__init__()
            self.setMinimumSize(960, 600)
            self._frame: QImage | None = None
            self._status = "OPTICAL SYSTEM INITIALIZING"
            self._text_overlays: dict[int, _TextOverlay] = {}
            self._text_timer = QTimer(self)
            self._text_timer.setInterval(16)
            self._text_timer.timeout.connect(self._advance_text)

        def add_text(self, text: str, slot: int, char_interval_ms: int, lifetime_ms: int, blink_interval_ms: int | None) -> None:
            if slot in self._text_overlays:
                return None
            elapsed = QElapsedTimer()
            elapsed.start()
            self._text_overlays[slot] = _TextOverlay(text, char_interval_ms, lifetime_ms, blink_interval_ms, elapsed,)
            self._text_timer.start()
            self.update()

        def _advance_text(self) -> None:
            expired_slots = [slot for slot, overlay in self._text_overlays.items() if overlay.elapsed.elapsed() >= overlay.typing_duration_ms + overlay.lifetime_ms]
            for slot in expired_slots:
                del self._text_overlays[slot]

            if not self._text_overlays:
                self._text_timer.stop()
            self.update()

        def set_frame(self, frame: QImage) -> None:
            self._frame = frame
            self._status = ""
            self.update()

        def set_status(self, message: str) -> None:
            self._frame = None
            self._status = message
            self.update()

        def paintEvent(self, _) -> None:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(0, 0, 0))

            frame = self._frame
            if frame is None or frame.isNull():
                image_rect = QRectF(self.rect())
                painter.setPen(QColor(255, 255, 255))
                font = QFont("Consolas")
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(
                    self.rect(),
                    Qt.AlignmentFlag.AlignCenter,
                    self._status,
                )
            else:
                scale = min(
                    self.width() / frame.width(),
                    self.height() / frame.height(),
                )
                image_width = frame.width() * scale
                image_height = frame.height() * scale
                image_rect = QRectF(
                    (self.width() - image_width) / 2,
                    (self.height() - image_height) / 2,
                    image_width,
                    image_height,
                )
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                painter.drawImage(image_rect, frame)

            self._paint_text(painter, image_rect)

        def _paint_text(self, painter: QPainter, image_rect: QRectF) -> None:
            font = QFont("Consolas")
            font.setPixelSize(18)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))

            painter.save()
            painter.setClipRect(image_rect)
            cell_width = image_rect.width() / 3
            cell_height = image_rect.height() / 3
            margin = min(12, min(cell_width, cell_height) * 0.08)
            for slot, overlay in self._text_overlays.items():
                elapsed_ms = overlay.elapsed.elapsed()
                visible_characters = min(
                    len(overlay.text),
                    elapsed_ms // overlay.char_interval_ms + 1,
                )
                text = overlay.text[:visible_characters]
                if (
                    overlay.blink_interval_ms is not None
                    and elapsed_ms >= overlay.typing_duration_ms
                ):
                    blink_phase = (
                        (elapsed_ms - overlay.typing_duration_ms)
                        // overlay.blink_interval_ms
                    )
                    if blink_phase % 2:
                        continue

                row, column = divmod(slot - 1, 3)
                text_rect = QRectF(
                    image_rect.left() + column * cell_width + margin,
                    image_rect.top() + row * cell_height + margin,
                    cell_width - 2 * margin,
                    cell_height - 2 * margin,
                )
                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignLeft
                    | Qt.AlignmentFlag.AlignVCenter
                    | Qt.TextFlag.TextWordWrap,
                    text,
                )
            painter.restore()


