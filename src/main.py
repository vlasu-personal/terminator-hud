import sys

from PySide6.QtWidgets import QApplication
from optical_unit import OpticalUnit
from hud import Hud


def main() -> int:
    autonomous_control_loop = QApplication(sys.argv)
    hud = Hud('Cyberdyne Systems Model 702, Series 800, Version 2.4', OpticalUnit(0))
    hud.start_display()
    return autonomous_control_loop.exec()


if __name__ == "__main__":
    sys.exit(main())
