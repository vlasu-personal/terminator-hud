import sys

from PySide6.QtWidgets import QApplication
from optical_unit import OpticalUnit


def main() -> int:
    autonomous_control_loop = QApplication(sys.argv)
    opticals = OpticalUnit()
    opticals.start()
    return autonomous_control_loop.exec()


if __name__ == "__main__":
    sys.exit(main())
