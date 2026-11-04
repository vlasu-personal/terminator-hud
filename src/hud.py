import cv2
import numpy as np

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QCloseEvent, QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QMainWindow, QWidget
from optical_unit import OpticalUnit


class Hud(QMainWindow):
    def __init__(self, hud_name: str, visual_input: OpticalUnit):
        super().__init__()
        self.setWindowTitle(hud_name)
        self.resize(960, 600)
        self._visual_input = visual_input
        self._display = self._Display()
        self.setCentralWidget(self._display)
        self._stopping = False

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
                painter.setPen(QColor(255, 255, 255))
                font = QFont("Consolas")
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(
                    self.rect(),
                    Qt.AlignmentFlag.AlignCenter,
                    self._status,
                )
                return

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


