"""JARVIS preview face — a taste of the real thing while the brain downloads."""
import sys, random, math

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QRadialGradient,
                         QFont)
from PyQt6.QtWidgets import QApplication, QWidget

CYAN = QColor(0, 229, 255)
CYAN_DIM = QColor(0, 140, 170, 160)
BG = QColor(8, 14, 18, 235)


class Face(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS (preview)")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(340, 400)
        self._t = 0.0
        self._blink = 0.0            # 0 open .. 1 closed
        self._next_blink = 2.0
        self._drag = None
        self._mouth = 0.0            # speaks a few boot lines

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    # ── drag support ────────────────────────────────────────────────
    def mousePressEvent(self, e):
        self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def mouseDoubleClickEvent(self, e):   # quit preview
        QApplication.quit()

    # ── animation ──────────────────────────────────────────────────
    def tick(self):
        self._t += 0.016
        # blinking
        self._next_blink -= 0.016
        if self._next_blink <= 0:
            self._blink = 1.0
            self._next_blink = random.uniform(2.5, 5.5)
        if self._blink > 0:
            self._blink = max(0.0, self._blink - 0.12)
        # mouth: talks when bar updates
        self._mouth = abs(math.sin(self._t * 4.2)) if int(self._t) % 8 < 4 else 0.0
        self.update()

    # ── painting ───────────────────────────────────────────────────
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # panel
        p.setPen(QPen(CYAN_DIM, 1))
        p.setBrush(QBrush(BG))
        p.drawRoundedRect(QRectF(6, 6, w - 12, h - 12), 18, 18)

        cx, cy, r0 = w / 2, h / 2 - 34, 95

        # outer halo
        pulse = 1 + 0.03 * math.sin(self._t * 2.0)
        halo = QRadialGradient(cx, cy, r0 * 1.8 * pulse)
        halo.setColorAt(0.0, QColor(0, 229, 255, 60))
        halo.setColorAt(0.55, QColor(0, 120, 160, 28))
        halo.setColorAt(1.0, Qt.GlobalColor.transparent)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QPointF(cx, cy), r0 * 1.8 * pulse, r0 * 1.8 * pulse)

        # rotating arc rings
        for speed, radius, alpha, width in ((0.9, r0 + 16, 140, 2),
                                            (-1.4, r0 + 26, 90, 1)):
            start = (self._t * speed * 57.3) % 360
            pen = QPen(QColor(0, 229, 255, alpha), width)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
                      int(start * 16), 110 * 16)
            p.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
                      int((start + 180) * 16), 110 * 16)

        # core orb
        core = QRadialGradient(cx - r0 * 0.2, cy - r0 * 0.25, r0)
        core.setColorAt(0.0, QColor(210, 250, 255))
        core.setColorAt(0.35, QColor(0, 200, 235, 230))
        core.setColorAt(0.75, QColor(0, 90, 120, 220))
        core.setColorAt(1.0, QColor(3, 40, 55, 235))
        p.setPen(QPen(CYAN, 2))
        p.setBrush(QBrush(core))
        p.drawEllipse(QPointF(cx, cy), r0, r0)

        # eyes (blink squashes height)
        eye_w, eye_h = 13, 9 * max(0.12, 1 - self._blink)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(240, 255, 255)))
        spread = 30 + 3 * math.sin(self._t * .7)          # slight look-around
        for sx in (-1, 1):
            ex = cx + sx * spread + 2 * math.sin(self._t * .35 + sx)
            ey = cy - 18
            p.drawRoundedRect(QRectF(ex - eye_w / 2, ey - eye_h / 2,
                                     eye_w, eye_h), 6, 6)

        # mouth — moves when "speaking"
        mw = 34 + 18 * self._mouth
        mh = 3 + 7 * self._mouth
        p.setBrush(QBrush(QColor(140, 240, 255, 220)))
        p.drawRoundedRect(QRectF(cx - mw / 2, cy + 28, mw, mh), 5, 5)

        # ── text ──────────────────────────────────────────────────────
        p.setPen(QPen(CYAN))
        f = QFont("DejaVu Sans", 13, QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(QRectF(6, h - 92, w - 12, 26), Qt.AlignmentFlag.AlignCenter,
                   "J  A  R  V  I  S")
        p.setPen(QPen(QColor(140, 210, 225)))
        f2 = QFont("DejaVu Sans", 8)
        p.setFont(f2)
        dots = "." * (1 + int(self._t) % 4)
        p.drawText(QRectF(6, h - 62, w - 12, 20), Qt.AlignmentFlag.AlignCenter,
                   f"AI AWAKENING{dots}")
        p.drawText(QRectF(6, h - 44, w - 12, 18), Qt.AlignmentFlag.AlignCenter,
                   "brain: downloading 70/420 MB")
        p.setPen(QPen(QColor(90, 150, 165, 180)))
        f3 = QFont("DejaVu Sans", 7)
        p.setFont(f3)
        p.drawText(QRectF(6, h - 30, w - 12, 16), Qt.AlignmentFlag.AlignCenter,
                   "drag me anywhere  •  double-click to hide")
        p.end()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("jarvis-preview")
    f = Face()
    # bottom-right of screen
    scr = app.primaryScreen().availableGeometry()
    f.move(scr.right() - f.width() - 28, scr.bottom() - f.height() - 8)
    f.show()
    app.exec()


if __name__ == "__main__":
    main()
