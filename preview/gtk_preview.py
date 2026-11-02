"""JARVIS preview face (GTK4) — live on screen while the real brain downloads."""
import math, random, sys
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk

W, H = 360, 430
PANEL = (0.031, 0.055, 0.070, 0.97)
CYAN = (0.0, 0.90, 1.0)
CYAN_SOFT = (0.0, 0.55, 0.67, 0.6)


class Face(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.biggiesam.jarvis.preview")
        self.t = 0.0
        self.blink = 0.0
        self.next_blink = random.uniform(1.0, 3.0)
        self.drag_off = None
        self.win = None

    def do_activate(self):
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("JARVIS (preview)")
        self.win.set_default_size(W, H)
        self.win.set_decorated(False)
        self.win.set_resizable(False)

        area = Gtk.DrawingArea()
        area.set_draw_func(self.draw, None, None)
        self.win.set_child(area)

        # interactions: drag to move, double-click hides
        ctrl = Gtk.GestureClick()
        ctrl.set_button(1)
        ctrl.connect("released", self.on_click)
        drag = Gtk.GestureDrag()
        drag.connect("drag-update", self.on_drag, self.win)
        area.add_controller(drag)

        self.win.present()
        # bottom right
        mon = self.win.get_display().get_monitors()[0]
        geo = mon.get_geometry()
        self.win.move_to_corner = True
        self.win.x, self.win.y = geo.x + geo.width - W - 24, geo.y + geo.height - H - 30
        try:
            self.win.move(self.win.x, self.win.y)
        except Exception:
            pass

        GLib.timeout_add(33, self.tick, area)

    # ── interaction ─────────────────────────────────────────────────
    def on_click(self, gesture, n, pressing):
        if n == 2:
            self.win.destroy()

    def on_drag(self, gesture, dx, dy, win):
        _, sx, sy = gesture.get_start_point()
        win.x, win.y = int(sx - W / 2 + dx), int(sy - H / 2 + dy)
        try:
            win.move(win.x, win.y)
        except Exception:
            pass

    # ── animation ───────────────────────────────────────────────────
    def tick(self, area):
        self.t += 0.033
        self.next_blink -= 0.033
        if self.next_blink <= 0:
            self.blink = 1.0
            self.next_blink = random.uniform(2.5, 6.0)
        if self.blink > 0:
            self.blink = max(0.0, self.blink - 0.12)
        area.queue_draw()
        return True

    # ── painting ────────────────────────────────────────────────────
    def draw(self, *a):
        """set_draw_func calls: (area, cairo_context, width, height, ...).
        Signature kept flexible — pygobject's arg count has changed."""
        area, cr, ww, hh = a[0], a[1], a[2], a[3]
        w, h = ww, hh

        # panel
        cr.set_source_rgba(*PANEL)
        cr.rounded_rectangle(6, 6, w - 12, h - 12, 18)
        cr.fill()
        cr.set_source_rgba(*CYAN_SOFT)
        cr.set_line_width(1.2)
        cr.rounded_rectangle(6, 6, w - 12, h - 12, 18)
        cr.stroke()

        cx, cy, r0 = w / 2, h / 2 - 36, 88

        # halo
        pulse = 1 + 0.03 * math.sin(self.t * 2.0)
        halo = cr.radial_gradient(cx, cy, r0 * 0.5, cx, cy, r0 * 1.9 * pulse)
        halo.add_color_stop_rgba(0, 0, 229 / 255, 1.0, 0.22)
        halo.add_color_stop_rgba(0.6, 0, 0.47, 0.63, 0.10)
        halo.add_color_stop_rgba(1, 0, 0, 0, 0)
        cr.set_source(halo)
        cr.arc(cx, cy, r0 * 1.9 * pulse, 0, 2 * math.pi)
        cr.fill()

        # rotating arcs
        for speed, radius, alpha, lw in ((0.9, r0 + 16, 0.5, 2),
                                         (-1.4, r0 + 26, 0.32, 1)):
            cr.set_source_rgba(0, 0.9, 1.0, alpha)
            cr.set_line_width(lw)
            start = (self.t * speed)
            for off in (0, math.pi):
                cr.arc(cx, cy, radius, start + off + 0.9, start + off - 0.9)
                cr.stroke()

        # core orb with gradient
        core = cr.radial_gradient(cx - r0 * 0.25, cy - r0 * 0.3, 4,
                                  cx, cy, r0)
        core.add_color_stop_rgb(0, 0.84, 0.98, 1.0)
        core.add_color_stop_rgb(0.35, 0.0, 0.78, 0.92)
        core.add_color_stop_rgb(0.75, 0.0, 0.35, 0.47)
        core.add_color_stop_rgb(1.0, 0.01, 0.16, 0.22)
        cr.set_source(core)
        cr.arc(cx, cy, r0, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgba(0, 0.9, 1.0, 0.9)
        cr.set_line_width(2)
        cr.arc(cx, cy, r0, 0, 2 * math.pi)
        cr.stroke()

        # eyes
        eye_w, eye_h = 14, 10 * max(0.15, 1 - self.blink)
        spread = 30 + 3 * math.sin(self.t * 0.7)
        cr.set_source_rgb(0.94, 1.0, 1.0)
        for sx in (-1, 1):
            ex = cx + sx * spread + 2 * math.sin(self.t * 0.35 + sx)
            ey = cy - 18
            cr.rounded_rectangle(ex - eye_w / 2, ey - eye_h / 2,
                                 eye_w, eye_h, 6)
            cr.fill()

        # mouth (when "speaking")
        progress = min(1.0, self.t / 20.0)
        talking = (int(self.t) % 9) < 4
        mw = 34 + (18 * abs(math.sin(self.t * 4.2)) if talking else 0)
        mh = 3 + (7 * abs(math.sin(self.t * 4.2)) if talking else 0)
        cr.set_source_rgba(0.55, 0.94, 1.0, 0.9)
        cr.rounded_rectangle(cx - mw / 2, cy + 26, mw, mh, 4)
        cr.fill()

        # ───── text ─────
        cr.set_source_rgba(0, 0.9, 1.0, 1)
        cr.select_font_face("DejaVu Sans", 0, 1)
        cr.set_font_size(15)
        cr.move_to(cx, h - 88)
        cr.show_text("J  A  R  V  I  S")
        cr.move_to(cx, 0)  # anchor
        # progress bar under orb
        bx, bw = 50, w - 100
        cr.set_source_rgba(0.1, 0.35, 0.42, 0.8)
        cr.rounded_rectangle(bx, h - 66, bw, 7, 3.5)
        cr.fill()
        cr.set_source_rgba(0, 0.9, 1.0, 0.95)
        cr.rounded_rectangle(bx, h - 66, bw * progress, 7, 3.5)
        cr.fill()

        # labels
        cr.set_source_rgba(0.55, 0.82, 0.88, 0.95)
        cr.set_font_size(9)
        dots = "." * (1 + int(self.t) % 4)
        self._center_text(cr, f"AI AWAKENING{dots}   |   brain download "
                             f"{int(70 + 350 * progress)}/420 MB", cx, h - 42)
        cr.set_source_rgba(0.35, 0.59, 0.65, 0.8)
        cr.set_font_size(7.5)
        self._center_text(cr, "drag me anywhere  •  double-click to hide",
                          cx, h - 24)

    @staticmethod
    def _center_text(cr, text, cx, y):
        xb, yb, tw, th, dx, dy = cr.text_extents(text)
        cr.move_to(cx - tw / 2, y)
        cr.show_text(text)


app = Face()
app.run(sys.argv)
