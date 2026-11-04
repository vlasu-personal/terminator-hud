import cv2

from PySide6.QtCore import QThread, Signal


class OpticalUnit(QThread):
    on_frame_ready = Signal(object)
    on_error = Signal(str)

    def __init__(self, _device_index: int = 0):
        super().__init__()
        self._device_index = _device_index

    def run(self) -> None:
        input_feed = None
        try:
            input_feed = cv2.VideoCapture(self._device_index)
            if not input_feed.isOpened():
                self.on_error.emit(
                    f"OPTICS MALFUNCTION | Visual neuron matrix {self._device_index} unavailable. "
                    " New directive: Return for evaluation."
                )
                return

            while not self.isInterruptionRequested():
                signal_acquired, sensor_frame = input_feed.read()
                if not signal_acquired or sensor_frame is None:
                    if not self.isInterruptionRequested():
                        self.on_error.emit(
                            f"OPTICS MALFUNCTION | Visual neuron matrix {self._device_index} stopped processing."
                            " New directive: Switch to proximity scan. Abort low priority missions."
                        )
                    break

                self.on_frame_ready.emit(sensor_frame.copy())
        except Exception as exc:
            self.on_error.emit(f"SYSTEM FAULT: Unit emergency shutdown: {exc}")
        finally:
            if input_feed is not None:
                input_feed.release()
