import cv2
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QImage, QPixmap
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget


class OpticalUnit(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CYBERDYNE SYSTEMS SERIES 800 MODEL 408 VERSION 2.4")
        self.resize(960, 600)
        self._stopping = False

        self._preview = QLabel("CYBERDYNE SYSTEMS SERIES 800 MODEL 408 VERSION 2.4 Starting...")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setMinimumSize(640, 360)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._preview)
        self.setCentralWidget(container)

        self._worker = self._OpticalLens(device_index=0, parent=self)
        self._worker.frame_ready.connect(self._show_frame)
        self._worker.error.connect(self._show_camera_error)

        self._close_timer = QTimer(self)
        self._close_timer.setInterval(50)
        self._close_timer.timeout.connect(self._close_when_camera_stops)
        
    def start(self) -> None:
        self._worker.start()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._worker.isRunning():
            event.ignore()
            if not self._stopping:
                self._stopping = True
                self._worker.requestInterruption()
                self._close_timer.start()
            return

        self._close_timer.stop()
        event.accept()

    def _show_frame(self, frame: QImage) -> None:
        self._render_frame(frame)

    def _show_camera_error(self, message: str) -> None:
        self._preview.setPixmap(QPixmap())
        self._preview.setText(message)
        self.statusBar().showMessage(message)

    def _render_frame(self, frame: QImage) -> None:
        if frame is None:
            return

        pixmap = QPixmap.fromImage(frame)
        self._preview.setPixmap(
            pixmap.scaled(
                self._preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _close_when_camera_stops(self) -> None:
        if not self._worker.isRunning():
            self._close_timer.stop()
            self.close()


    class _OpticalLens(QThread):
        frame_ready = Signal(QImage)
        error = Signal(str)

        def __init__(self, device_index: int = 0, parent: QObject | None = None):
            super().__init__(parent)
            self.device_index = device_index

        def run(self) -> None:
            optics_unit = None
            try:
                optics_unit = cv2.VideoCapture(self.device_index)
                if not optics_unit.isOpened():
                    self.error.emit(
                        f"OPTICS MALFUNCTION | Visual neuron matrix {self.device_index} unavailable. "
                        " New directive: Return for evaluation."
                    )
                    return

                while not self.isInterruptionRequested():
                    signal_acquired, sensor_frame = optics_unit.read()
                    if not signal_acquired or sensor_frame is None:
                        if not self.isInterruptionRequested():
                            self.error.emit(
                                f"OPTICS MALFUNCTION | Visual neuron matrix {self.device_index} stopped processing."
                                " New directive: Switch to proximity scan. Abort low priority missions."
                            )
                        break

                    visual_spectrum = cv2.cvtColor(sensor_frame, cv2.COLOR_BGR2RGB)
                    frame_height, frame_width, _ = visual_spectrum.shape
                    display_frame = QImage(
                        visual_spectrum.data,
                        frame_width,
                        frame_height,
                        visual_spectrum.strides[0],
                        QImage.Format.Format_RGB888,
                    ).copy()
                    self.frame_ready.emit(display_frame)
            except Exception as exc:
                self.error.emit(f"SYSTEM FAULT: Unit emergency shutdown: {exc}")
            finally:
                if optics_unit is not None:
                    optics_unit.release()
