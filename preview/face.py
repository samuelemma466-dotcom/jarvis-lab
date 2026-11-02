"""JARVIS preview face v2 — maximum-compatibility drawing (plain cairo ops)."""
import math, random, sys, faulthandler, os
faulthandler.enable()
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

W, H = 360, 420


class Face(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.biggiesam.jarvis.preview")
        self.t = 0.0
        self.blink = 0.0
        self.next_blink = random.uniform(1.0, 3.0)
        self.win = None
        self.area = None

    def do_activate(self):
        print("activate: start", flush=True)
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_default_size(W, H)
        self.win.set_decorated(False)
        self.area = Gtk.DrawingArea()
        self.area.set_content_width(W)
        self.area.set_content_height(H)
        try:
            self.area.set_draw_func(self.draw, None, None)
        except TypeError:
            self.area.set_draw_func(self.draw)
        self.win.set_child(self.area)
        ctrl = Gtk.GestureClick()
        ctrl.set_button(1)
        ctrl.connect("pressed", self.on_press)
        self.area.add_controller(ctrl)
        self.win.connect("close-request", self.on_close)
        self.win.present()
        print("activate: window presented", flush=True)
        GLib.timeout_add(33, self.tick)
        GLib.timeout_add_seconds(600, self.auto_reopen)
        return False

    def on_press(self, gesture, n, x, y):
        print("click n=%d" % n, flush=True)
        if n == 2:
            print("double-click -> quit", flush=True)
            self.quit()

    def on_close(self, *a):
        print("close-request", flush=True)
        self.quit()
        return True

    def auto_reopen(self):
        # safety: keep the window alive if it ever maps off
        if self.win:
            try:
                self.win.present()
            except Exception as e:
                print("reopen fail", e, flush=True)
        return True

    def tick(self):
        try:
            self.t += 0.033
            self.next_blink -= 0.033
            if self.next_blink <= 0:
                self.blink = 1.0
                self.next_blink = random.uniform(2.5, 6.0)
            if self.blink > 0:
                self.blink = max(0.0, self.blink - 0.13)
            if self.area:
                self.area.queue_draw()
        except Exception as e:
            print("tick err", e, flush=True)
            return False
        return True

    # ── painting: only arc/fill/stroke/text — nothing exotic ──────────
    def draw(self, *args):
        try:
            area = args[0]; cr = args[1]; w = args[2] or W; h = args[3] or H
            cx, cy, r0 = w / 2.0, h / 2.0 - 34.0, 84.0

            # solid dark panel
            cr.set_source_rgb(0.03, 0.055, 0.07)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            # border
            cr.set_source_rgb(0.0, 0.4, 0.5)
            cr.set_line_width(1.5)
            cr.rectangle(4, 4, w - 8, h - 8)
            cr.stroke()

            # halo (nested circles, alpha via rgba)
            pulse = 1.0 + 0.03 * math.sin(self.t * 2.0)
            for k in range(10, 1, -1):
                rr = r0 * pulse * (1.0 + 0.04 * k)
                cr.set_source_rgba(0.0, 0.65, 0.8, 0.06)
                cr.arc(cx, cy, rr, 0, 2 * math.pi)
                cr.fill()

            # rotating arcs
            for speed, radius, alpha, lw in ((0.9, r0 + 14, 0.5, 2),
                                             (-1.4, r0 + 24, 0.3, 1)):
                cr.set_source_rgba(0.0, 0.9, 1.0, alpha)
                cr.set_line_width(lw)
                start = self.t * speed
                for off in (0, math.pi):
                    cr.arc(cx, cy, radius,
                           start + off + 0.95, start + off + math.pi - 0.95)
                    cr.stroke()

            # core orb
            cr.set_source_rgb(0.02, 0.25, 0.32)
            cr.arc(cx, cy, r0, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgb(0.95, 1.0, 1.0)
            cr.arc(cx - 18, cy - 22, r0 * 0.34, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgb(0.0, 0.72, 0.9)
            cr.set_line_width(2.5)
            cr.arc(cx, cy, r0, 0, 2 * math.pi)
            cr.stroke()

            # eyes
            ew, eh = 13.0, 9.5 * max(0.15, 1 - self.blink)
            spread = 29 + 3.5 * math.sin(self.t * 0.7)
            cr.set_source_rgb(0.94, 1.0, 1.0)
            for sx in (-1.0, 1.0):
                ex = cx + sx * spread
                cr.rectangle(ex - ew / 2, cy - 17 - eh / 2, ew, eh)
                cr.fill()
            # mouth
            talk = (int(self.t) % 9) < 4
            mw = 34.0 + (17 * abs(math.sin(self.t * 4.2)) if talk else 0)
            mh = 3.0 + (6.5 * abs(math.sin(self.t * 4.2)) if talk else 0)
            cr.rectangle(cx - mw / 2, cy + 24, mw, mh)
            cr.fill()

            # progress bar
            prog = min(1.0, 0.18)  # static-ish; real number comes later
            bx, bw = 48, w - 96
            by = h - 64
            cr.set_source_rgb(0.08, 0.3, 0.36)
            cr.rectangle(bx, by, bw, 7)
            cr.fill()
            cr.set_source_rgb(0.0, 0.9, 1.0)
            cr.rectangle(bx, by, bw * prog, 7)
            cr.fill()

            # text
            cr.set_source_rgb(0.0, 0.9, 1.0)
            cr.select_font_face("sans", 0, 1)
            cr.set_font_size(15)
            title = "J  A  R  V  I  S"
            x0, y0, tw, th, dx, dy = cr.text_extents(title)
            cr.move_to((w - tw) / 2, h - 84)
            cr.show_text(title)
            cr.set_source_rgb(0.55, 0.82, 0.88)
            cr.set_font_size(9)
            dots = "." * (1 + int(self.t) % 4)
            sub = "AI AWAKENING" + dots
            x0, y0, tw2, _, _, _ = cr.text_extents(sub)
            cr.move_to((w - tw2) / 2, h - 36)
            cr.show_text(sub)
        except Exception as e:
            import traceback
            traceback.print_exc()
        return False  # let tomorrow's errors surface instead of looping


app = Face()
try:
    sys.exit(app.run(sys.argv))
finally:
    print("bye", flush=True)
