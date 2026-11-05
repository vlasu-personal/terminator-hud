import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QRandomGenerator
from optical_unit import OpticalUnit
from hud import Hud

assembly_6502 = """
0800:  D8    CLD
0801:  A2 FF LDX #$FF
0803:  9A    TXS
0804:  A9 00 LDA #$00
0806:  85 FB STA $FB
0808:  A9 04 LDA #$04
080A:  85 FC STA $FC
080C:  A0 00 LDY #$00
080E:  A9 A0 LDA #$A0
"""

def text_worker(hud, text: str, slot_id: int | None = None, interval_ms: int = 45, lifetime: int = 3000, blink_interval: int | None = None):
     hud.print_text(text, slot=slot_id, char_interval_ms=interval_ms, lifetime_ms=lifetime, blink_interval_ms=blink_interval)


def main() -> int:
    autonomous_control_loop = QApplication(sys.argv)
    hud = Hud('Cyberdyne Systems Model 702, Series 800, Version 2.4', OpticalUnit(0))
    hud.start_display()
    QTimer.singleShot(500, lambda: hud.print_text('Directive: Find and terminate John Connor', slot=5, char_interval_ms=50, lifetime_ms=60000))
    QTimer.singleShot(500, lambda: hud.print_text('Mode: Tracking', slot=8, char_interval_ms=100, lifetime_ms=60000, blink_interval_ms=500))

    rng = QRandomGenerator.global_()
    allowed = [1, 2, 4, 6, 7, 9]
    timer = QTimer()
    timer.timeout.connect(lambda: (timer.setInterval(rng.bounded(3000, 6000)), hud.print_text(assembly_6502, slot=allowed[rng.bounded(len(allowed))], char_interval_ms=5, lifetime_ms=2000, blink_interval_ms=50)))
    timer.timeout.connect(lambda: (timer.setInterval(rng.bounded(2000, 4000)), hud.print_animation(slot=allowed[rng.bounded(len(allowed))])))
    timer.start()

    return autonomous_control_loop.exec()


if __name__ == "__main__":
    sys.exit(main())
