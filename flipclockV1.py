#!/usr/bin/env python3
"""
Flip Clock Pro - Full Featured Minimal Design
- Small SWITCH and GEAR buttons in white box
- Theme selector in gear dropdown (working!)
- Full timer with input and presets
- Smooth flip animation
- Single minimalist window
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import cairo
import datetime
import json
import os
import sys
import subprocess
import math
import time

# Configuration
CONFIG_DIR = os.path.expanduser("~/.config/flipclock")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "window_pos": {"x": -1, "y": -1},
    "animation_speed": 0.5,
    "sound_type": "chime",
    "opacity": 1.0,
    "mode": "clock",
    "theme": "hacker",
}

# THEMES DEFINITION
THEMES = {
    "hacker": {
        "bg": "#0a0e27",
        "box_bg": "#0f1419",
        "border": "#00ff41",
        "text": "#00ff41",
        "accent": "#00d4ff",
        "button_bg": "#1a1f3a",
        "button_hover": "#00ff41",
        "font": "Courier New",
        "name": "🔥 HACKER"
    },
    "macos": {
        "bg": "#f5f5f7",
        "box_bg": "#ffffff",
        "border": "#d0d0d0",
        "text": "#000000",
        "accent": "#007aff",
        "button_bg": "#e5e5ea",
        "button_hover": "#d0d0d0",
        "font": "San Francisco",
        "name": "🍎 macOS"
    },
    "pink": {
        "bg": "#2a1a2e",
        "box_bg": "#3d2645",
        "border": "#ff006e",
        "text": "#ff006e",
        "accent": "#ff1493",
        "button_bg": "#4a3560",
        "button_hover": "#ff006e",
        "font": "Courier New",
        "name": "💖 PINK"
    },
    "cyan": {
        "bg": "#0a1628",
        "box_bg": "#0f2540",
        "border": "#00d4ff",
        "text": "#00d4ff",
        "accent": "#00ffff",
        "button_bg": "#1a3a5a",
        "button_hover": "#00d4ff",
        "font": "Courier New",
        "name": "💎 CYAN"
    },
    "dark": {
        "bg": "#1a1a1a",
        "box_bg": "#2d2d2d",
        "border": "#ffffff",
        "text": "#ffffff",
        "accent": "#888888",
        "button_bg": "#3d3d3d",
        "button_hover": "#ffffff",
        "font": "Courier New",
        "name": "⚫ DARK"
    }
}

def generate_css(theme):
    """Generate CSS for the selected theme."""
    t = THEMES[theme]
    css = f"""
window {{
    background: {t['bg']};
}}

.main-box {{
    background: {t['box_bg']};
    border: 2px solid {t['border']};
    border-radius: 8px;
    padding: 12px;
}}

.separator {{
    color: {t['text']};
}}

.unit-label {{
    font-family: "{t['font']}", monospace;
    font-size: 7px;
    color: {t['text']};
    opacity: 0.5;
}}

.timer-input {{
    background: {t['bg']};
    color: {t['text']};
    border: 1px solid {t['border']};
    font-family: "{t['font']}", monospace;
    font-size: 12px;
    padding: 4px;
}}

.timer-button {{
    background: {t['button_bg']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 3px;
    padding: 3px 6px;
    font-size: 8px;
    font-family: "{t['font']}", monospace;
    font-weight: bold;
}}

.timer-button:hover {{
    background: {t['button_hover']};
    color: {t['bg']};
}}

.small-button {{
    background: {t['button_bg']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 2px;
    padding: 2px 4px;
    font-size: 7px;
    font-family: "{t['font']}", monospace;
    font-weight: bold;
}}

.small-button:hover {{
    background: {t['button_hover']};
    color: {t['bg']};
}}

.preset-button {{
    background: {t['button_bg']};
    color: {t['accent']};
    border: 1px solid {t['accent']};
    border-radius: 2px;
    padding: 2px 4px;
    font-size: 7px;
    font-family: "{t['font']}", monospace;
}}

.preset-button:hover {{
    background: {t['accent']};
    color: {t['bg']};
}}

.wood-base {{
    background: {t['text']};
    border-radius: 0 0 6px 6px;
    min-height: 1px;
}}
""".encode()
    return css


class FlipDigitCanvas(Gtk.DrawingArea):
    """Custom widget that draws a single digit with smooth flip animation."""
    
    def __init__(self, animation_speed=0.5, theme="hacker"):
        super().__init__()
        self.current_digit = "0"
        self.target_digit = "0"
        self.animation_progress = 0.0
        self.is_animating = False
        self.animation_speed = animation_speed
        self.flip_start_time = 0
        self.theme = theme
        self.animation_handle = None
        
        self.set_size_request(40, 55)
        self.set_double_buffered(True)
        self.connect("draw", self.on_draw)
    
    def set_digit(self, digit):
        """Set digit and trigger flip animation."""
        if self.current_digit != digit:
            if self.animation_handle is not None:
                GLib.source_remove(self.animation_handle)
                self.animation_handle = None
            
            self.target_digit = digit
            self.is_animating = True
            self.flip_start_time = time.time()
            self.animation_progress = 0.0
            
            self.animation_handle = GLib.timeout_add(16, self.animate_flip)
    
    def set_theme(self, theme):
        """Change theme."""
        self.theme = theme
        self.queue_draw()
    
    def animate_flip(self):
        """Smooth animation frame update."""
        if not self.is_animating:
            return False
        
        elapsed = time.time() - self.flip_start_time
        self.animation_progress = min(elapsed / self.animation_speed, 1.0)
        
        self.queue_draw()
        
        if self.animation_progress >= 1.0:
            self.current_digit = self.target_digit
            self.is_animating = False
            self.animation_progress = 0.0
            self.animation_handle = None
            self.queue_draw()
            return False
        
        return True
    
    def on_draw(self, widget, cr):
        """Draw the digit with smooth 3D flip effect."""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        if width <= 1 or height <= 1:
            return
        
        t = THEMES[self.theme]
        
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
        
        bg_rgb = hex_to_rgb(t['bg'])
        border_rgb = hex_to_rgb(t['border'])
        text_rgb = hex_to_rgb(t['text'])
        
        cr.set_source_rgb(*bg_rgb)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        cr.set_source_rgb(*border_rgb)
        cr.set_line_width(1)
        cr.rectangle(0, 0, width, height)
        cr.stroke()
        
        if self.is_animating and 0 < self.animation_progress < 1.0:
            self.draw_flipping_digit(cr, width, height, text_rgb, t['font'])
        else:
            self.draw_static_digit(cr, width, height, text_rgb, t['font'], self.current_digit)
    
    def draw_flipping_digit(self, cr, width, height, text_rgb, font):
        """Draw digit during flip animation."""
        progress = self.animation_progress
        cx = width / 2
        cy = height / 2
        
        cr.save()
        cr.translate(cx, cy)
        
        if progress < 0.5:
            scale_progress = progress * 2
            alpha = 1.0 - scale_progress
            cr.set_source_rgba(*text_rgb, alpha)
            
            cr.save()
            cr.scale(1, 1 - scale_progress)
            cr.scale(1, 0.5)
            cr.translate(-width/2, -height/2)
            self.draw_text(cr, self.current_digit, width, height * 0.5, font)
            cr.restore()
        
        if progress >= 0.5:
            scale_progress = (progress - 0.5) * 2
            alpha = scale_progress
            cr.set_source_rgba(*text_rgb, alpha)
            
            cr.save()
            cr.scale(1, scale_progress)
            cr.translate(-cx, 0)
            cr.translate(cx, cy)
            cr.scale(1, 0.5)
            cr.translate(-width/2, height/2)
            self.draw_text(cr, self.target_digit, width, height * 0.5, font)
            cr.restore()
        
        cr.restore()
    
    def draw_static_digit(self, cr, width, height, text_rgb, font, digit):
        """Draw static digit without animation."""
        cr.set_source_rgb(*text_rgb)
        self.draw_text(cr, digit, width, height, font)
    
    def draw_text(self, cr, digit, width, height, font):
        """Draw digit text centered."""
        cr.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(32)
        
        extents = cr.text_extents(digit)
        x = (width - extents.width) / 2 - extents.x_bearing
        y = (height - extents.height) / 2 - extents.y_bearing
        
        cr.move_to(x, y)
        cr.show_text(digit)


class FlipClockApp(Gtk.Window):
    """Main application window - Full featured."""
    
    def __init__(self):
        super().__init__(title="Flip Clock Pro")
        self.config = load_config()
        self.current_theme = self.config.get("theme", "hacker")
        
        # Window setup
        self.set_decorated(True)
        self.set_keep_above(True)
        self.set_resizable(True)  # ALLOW RESIZING!
        self.set_app_paintable(True)
        self.set_opacity(self.config["opacity"])
        self.set_default_size(250, 150)  # Default size
        
        # RGBA visual
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        
        # Apply CSS
        self.apply_theme(self.current_theme)
        
        # Events
        self.connect("realize", self.position_window)
        self.connect("destroy", self.on_destroy)
        
        # Main container
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_vbox)
        
        # Content box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_vbox.pack_start(self.content_box, True, True, 0)
        
        # Build both modes
        self.build_clock_ui()
        self.build_timer_ui()
        
        # Timer state
        self.timer_running = False
        self.timer_seconds = 0
        
        # Start in clock mode
        self.set_mode("clock")
        
        # Update clock
        self.last_second = -1
        self.update_clock()
        GLib.timeout_add(100, self.update_clock)
    
    def apply_theme(self, theme):
        """Apply CSS theme."""
        css = generate_css(theme)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        screen = self.get_screen()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def build_clock_ui(self):
        """Build clock display UI."""
        self.clock_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.clock_box.get_style_context().add_class("main-box")
        self.clock_box.set_margin_start(6)
        self.clock_box.set_margin_end(6)
        self.clock_box.set_margin_top(6)
        self.clock_box.set_margin_bottom(6)
        
        # Header with buttons
        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        header_row.set_halign(Gtk.Align.END)
        header_row.set_margin_bottom(3)
        self.clock_box.pack_start(header_row, False, False, 0)
        
        switch_btn = Gtk.Button(label="≡")
        switch_btn.get_style_context().add_class("small-button")
        switch_btn.set_size_request(25, 18)
        switch_btn.connect("clicked", self.on_toggle_mode)
        header_row.pack_start(switch_btn, False, False, 0)
        
        gear_btn = Gtk.Button(label="⚙")
        gear_btn.get_style_context().add_class("small-button")
        gear_btn.set_size_request(25, 18)
        gear_btn.connect("clicked", self.on_gear_clicked)
        header_row.pack_start(gear_btn, False, False, 0)
        
        # Digits
        digits_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        digits_row.set_halign(Gtk.Align.CENTER)
        digits_row.set_margin_bottom(2)
        self.clock_box.pack_start(digits_row, True, True, 0)
        
        self.digits = []
        for i in range(6):
            canvas = FlipDigitCanvas(self.config["animation_speed"], self.current_theme)
            self.digits.append(canvas)
            digits_row.pack_start(canvas, False, False, 0)
            
            if i in [1, 3]:
                sep = Gtk.Label(label=":")
                sep.get_style_context().add_class("separator")
                t = THEMES[self.current_theme]
                sep.set_markup(f'<span font="{t["font"]} 24" weight="bold">:</span>')
                digits_row.pack_start(sep, False, False, 0)
        
        # Line
        base = Gtk.Box()
        base.get_style_context().add_class("wood-base")
        base.set_size_request(-1, 1)
        self.clock_box.pack_start(base, False, False, 0)
    
    def build_timer_ui(self):
        """Build timer display UI."""
        self.timer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.timer_box.get_style_context().add_class("main-box")
        self.timer_box.set_margin_start(6)
        self.timer_box.set_margin_end(6)
        self.timer_box.set_margin_top(6)
        self.timer_box.set_margin_bottom(6)
        
        # Header with buttons
        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        header_row.set_halign(Gtk.Align.END)
        header_row.set_margin_bottom(3)
        self.timer_box.pack_start(header_row, False, False, 0)
        
        switch_btn = Gtk.Button(label="≡")
        switch_btn.get_style_context().add_class("small-button")
        switch_btn.set_size_request(25, 18)
        switch_btn.connect("clicked", self.on_toggle_mode)
        header_row.pack_start(switch_btn, False, False, 0)
        
        gear_btn = Gtk.Button(label="⚙")
        gear_btn.get_style_context().add_class("small-button")
        gear_btn.set_size_request(25, 18)
        gear_btn.connect("clicked", self.on_gear_clicked)
        header_row.pack_start(gear_btn, False, False, 0)
        
        # Display
        display_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        display_row.set_halign(Gtk.Align.CENTER)
        display_row.set_margin_bottom(2)
        self.timer_box.pack_start(display_row, False, False, 0)
        
        self.timer_digits = []
        for i in range(4):
            canvas = FlipDigitCanvas(self.config["animation_speed"], self.current_theme)
            self.timer_digits.append(canvas)
            display_row.pack_start(canvas, False, False, 0)
            
            if i == 1:
                sep = Gtk.Label(label=":")
                sep.get_style_context().add_class("separator")
                t = THEMES[self.current_theme]
                sep.set_markup(f'<span font="{t["font"]} 24" weight="bold">:</span>')
                display_row.pack_start(sep, False, False, 0)
        
        # Controls - Compact
        control_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        control_row.set_halign(Gtk.Align.CENTER)
        control_row.set_margin_top(2)
        control_row.set_margin_bottom(2)
        self.timer_box.pack_start(control_row, False, False, 0)
        
        self.custom_input = Gtk.Entry()
        self.custom_input.set_text("00:00")
        self.custom_input.set_max_length(5)
        self.custom_input.get_style_context().add_class("timer-input")
        self.custom_input.set_width_chars(5)
        control_row.pack_start(self.custom_input, False, False, 0)
        
        for label, callback in [("▶", self.on_start), ("⏸", self.on_pause), ("↺", self.on_reset)]:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("timer-button")
            btn.set_size_request(24, 18)
            btn.connect("clicked", callback)
            control_row.pack_start(btn, False, False, 0)
        
        # Presets
        presets_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        presets_row.set_halign(Gtk.Align.CENTER)
        self.timer_box.pack_start(presets_row, False, False, 0)
        
        for minutes in [1, 5, 10, 30]:
            btn = Gtk.Button(label=f"{minutes}m")
            btn.get_style_context().add_class("preset-button")
            btn.set_size_request(28, 16)
            btn.connect("clicked", self.on_preset, minutes * 60)
            presets_row.pack_start(btn, False, False, 0)
        
        # Line
        base = Gtk.Box()
        base.get_style_context().add_class("wood-base")
        base.set_size_request(-1, 1)
        self.timer_box.pack_start(base, False, False, 0)
    
    def set_mode(self, mode):
        """Switch between clock and timer."""
        for child in self.content_box.get_children():
            self.content_box.remove(child)
        
        if mode == "clock":
            self.content_box.pack_start(self.clock_box, True, True, 0)
            self.config["mode"] = "clock"
        else:
            self.content_box.pack_start(self.timer_box, True, True, 0)
            self.config["mode"] = "timer"
        
        self.content_box.show_all()
        save_config(self.config)
    
    def on_toggle_mode(self, widget):
        """Toggle clock/timer."""
        current_mode = self.config.get("mode", "clock")
        self.set_mode("timer" if current_mode == "clock" else "clock")
    
    def on_gear_clicked(self, widget):
        """Show theme menu from gear button."""
        menu = Gtk.Menu()
        
        # Theme submenu
        for theme_key in THEMES.keys():
            item = Gtk.MenuItem(label=THEMES[theme_key]["name"])
            item.connect("activate", self.on_theme_change, theme_key)
            menu.append(item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Opacity
        for opacity_val in [0.5, 0.75, 1.0]:
            item = Gtk.MenuItem(label=f"Opacity {int(opacity_val*100)}%")
            item.connect("activate", self.on_opacity_change, opacity_val)
            menu.append(item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Sound
        for sound in ["chime", "beep", "silent"]:
            item = Gtk.MenuItem(label=f"Sound: {sound.capitalize()}")
            item.connect("activate", self.on_sound_change, sound)
            menu.append(item)
        
        menu.show_all()
        menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST)
    
    def on_theme_change(self, widget, theme):
        """Change theme."""
        self.current_theme = theme
        self.config["theme"] = theme
        save_config(self.config)
        
        self.apply_theme(theme)
        
        for digit in self.digits:
            digit.set_theme(theme)
        for digit in self.timer_digits:
            digit.set_theme(theme)
        
        self.queue_draw()
    
    def on_opacity_change(self, widget, opacity):
        """Change opacity."""
        self.config["opacity"] = opacity
        save_config(self.config)
        self.set_opacity(opacity)
    
    def on_sound_change(self, widget, sound):
        """Change sound."""
        self.config["sound_type"] = sound
        save_config(self.config)
    
    def position_window(self, widget):
        """Position window."""
        self.resize(1, 1)
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        
        if not monitor:
            return
        
        geo = monitor.get_geometry()
        w, h = self.get_size()
        
        if self.config["window_pos"]["x"] != -1:
            self.move(self.config["window_pos"]["x"], self.config["window_pos"]["y"])
        else:
            x = geo.x + (geo.width - w) // 2
            y = geo.y + (geo.height - h) // 2
            self.move(int(x), int(y))
    
    def update_clock(self):
        """Update clock display."""
        now = datetime.datetime.now()
        current_second = now.second
        
        if current_second != self.last_second:
            self.last_second = current_second
            
            h = f"{now.hour:02d}"
            m = f"{now.minute:02d}"
            s = f"{now.second:02d}"
            
            for i, digit in enumerate(h + m + s):
                self.digits[i].set_digit(digit)
        
        return True
    
    def on_preset(self, widget, seconds):
        """Set timer from preset."""
        self.timer_seconds = seconds
        self.timer_running = False
        self.update_timer_display()
    
    def on_start(self, widget):
        """Start timer."""
        custom_text = self.custom_input.get_text()
        if custom_text and ":" in custom_text:
            try:
                parts = custom_text.split(":")
                minutes = int(parts[0])
                seconds = int(parts[1])
                self.timer_seconds = minutes * 60 + seconds
            except:
                pass
        
        if self.timer_seconds > 0:
            self.timer_running = True
            GLib.timeout_add(1000, self.timer_tick)
    
    def on_pause(self, widget):
        """Pause timer."""
        self.timer_running = False
    
    def on_reset(self, widget):
        """Reset timer."""
        self.timer_running = False
        self.timer_seconds = 0
        self.update_timer_display()
    
    def timer_tick(self):
        """Timer countdown."""
        if not self.timer_running:
            return False
        
        self.timer_seconds -= 1
        self.update_timer_display()
        
        if self.timer_seconds <= 0:
            self.timer_running = False
            self.play_alert()
            return False
        
        return True
    
    def update_timer_display(self):
        """Update timer display."""
        minutes = self.timer_seconds // 60
        seconds = self.timer_seconds % 60
        
        m = f"{minutes:02d}"
        s = f"{seconds:02d}"
        
        self.custom_input.set_text(f"{m}:{s}")
        
        digits_str = m + s
        for i, digit in enumerate(digits_str):
            self.timer_digits[i].set_digit(digit)
    
    def play_alert(self):
        """Play alert sound."""
        sound_type = self.config.get("sound_type", "chime")
        
        if sound_type == "silent":
            return
        
        try:
            if sound_type == "chime":
                subprocess.Popen(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif sound_type == "beep":
                subprocess.Popen(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except:
            pass
    
    def on_destroy(self, widget):
        """Handle window close."""
        x, y = self.get_position()
        self.config["window_pos"] = {"x": x, "y": y}
        save_config(self.config)
        self.timer_running = False
        Gtk.main_quit()


def load_config():
    """Load configuration."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
    except:
        pass
    
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass


def main():
    """Main application entry point."""
    try:
        if os.environ.get('DISPLAY') is None:
            print("Error: No display found. Run in a graphical environment.")
            sys.exit(1)
        
        app = FlipClockApp()
        app.show_all()
        
        Gtk.main()
    
    except ImportError:
        print("Error: Missing dependency")
        print("Install with: sudo apt install python3-gi gir1.2-gtk-3.0")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
