#!/usr/bin/env python3
"""
 *  Eleòra CharM
 *  Emoji and special character picker for Linux/KDE.
 *
 *  https://github.com/eleora-dev/charm
 *  License: MIT
"""

import sys, os, json, socket, subprocess, threading, time, unicodedata, locale
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QScrollArea, QGridLayout, QLabel, QStackedWidget, QFrame,
    QSizePolicy, QToolTip, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QEvent, QSize, QUrl
from PySide6.QtGui import (
    QIcon, QFont, QPixmap, QColor, QPainter, QCursor,
    QFontDatabase, QFontMetrics, QDesktopServices, QPalette
)

try:
    import resources  # generated with: pyside6-rcc charm.qrc -o resources.py
except ImportError:
    resources = None

try:
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# ── APP CONSTANTS + LOCALIZATION ─────────────────────────────────────────────

DEV_NAME = "Eleòra"
DEV_URL = "https://github.com/eleora-dev"
APP_NAME = "CharM"
APP_VERSION = "1.0"
APP_COPYRIGHT = "© 2026 Gerardo Perilli"
APP_HOTKEY_DISPLAY = "Ctrl+Alt+E"
APP_HOTKEY_CONFIG = "<ctrl>+<alt>+e"
APP_ICON_RESOURCE = ":/icons/charm.png"
APP_ICON_CHAR = "✨"
CLOSE_BUTTON_TEXT = "×"
IPC_SHOW_COMMAND = "show"
LOG_PREFIX = f"[{APP_NAME}]"

SERVICE_PRIVACY_URL = "https://eleora-dev.github.io/charm/privacy.html"
SERVICE_LICENSE_URL = "https://eleora-dev.github.io/charm/LICENSE"
SERVICE_ISSUES_URL = "https://github.com/eleora-dev/charm/issues"

LANG_IT = "it"
LANG_EN = "en"
SUPPORTED_LANGS = {LANG_IT, LANG_EN}


def detect_app_language() -> str:
    """Use Italian only when the system locale is Italian; English otherwise."""
    checks = [
        os.environ.get("LC_ALL", ""),
        os.environ.get("LC_MESSAGES", ""),
        os.environ.get("LANGUAGE", ""),
        os.environ.get("LANG", ""),
    ]
    try:
        checks.append(locale.getlocale()[0] or "")
    except Exception:
        pass

    for value in checks:
        first = str(value).split(":", 1)[0].split(".", 1)[0].replace("-", "_").lower()
        if first == "it" or first.startswith("it_"):
            return LANG_IT
    return LANG_EN


APP_LANG = detect_app_language()

STRINGS = {
    LANG_EN: {
        "header_title": f"{DEV_NAME} {APP_NAME} v{APP_VERSION.split('-', 1)[0]}",
        "window_title": f"{DEV_NAME} {APP_NAME}",
        "hotkey_badge": APP_HOTKEY_DISPLAY,
        "clear_recent_button": "Clear Recent",
        "clear_recent_tooltip": "Clear the history of recently used emoji",
        "clear_recent_done": "Recent history cleared",
        "recent_empty": "No recent emoji yet.\nPick something to see it here.",
        "search_placeholder": "Search emoji or character…",
        "no_results": "No results",
        "service_privacy": "Privacy",
        "service_license": "License",
        "service_issue": "Report issue",
        "service_privacy_tooltip": "Privacy policy",
        "service_license_tooltip": "MIT License",
        "service_issue_tooltip": "Report an issue on GitHub",
        "tray_tooltip": f"{DEV_NAME} {APP_NAME}  [{APP_HOTKEY_DISPLAY}]",
        "tray_open": f"Open {APP_NAME}",
        "tray_paste_info": f"{APP_HOTKEY_DISPLAY} • paste: {{method}}",
        "title_icon_tooltip": f"{DEV_NAME} on GitHub",
        "tray_quit": "Quit",
        "copied_notification": "'{char}' copied to clipboard — press Ctrl+V",
        "system_tray_unavailable": f"{LOG_PREFIX} System tray unavailable.",
        "hotkey_missing": (
            f"{LOG_PREFIX} pynput is unavailable → global shortcut disabled.\n"
            "              Install with: pip install pynput\n"
            "              Or configure a KDE shortcut that runs:\n"
            "              python {file} --show"
        ),
        "hotkey_error": f"{LOG_PREFIX} Hotkey listener error: {{error}}",
        "socket_error": f"{LOG_PREFIX} Socket server error: {{error}}",
        "xdotool_error": f"{LOG_PREFIX} xdotool error: {{error}}",
        "ydotool_error": f"{LOG_PREFIX} ydotool error: {{error}}",
        "local_font_load_error": f"{LOG_PREFIX} Local font load error {{path}}: {{error}}",
        "local_fonts": f"{LOG_PREFIX} Local fonts: {{fonts}}",
        "symbol_font": f"{LOG_PREFIX} Symbol font: «{{font}}»",
        "symbol_font_partial": f"{LOG_PREFIX} Symbol font (partial match): «{{font}}»",
        "symbol_font_fallback": f"{LOG_PREFIX} Symbol font: sans-serif fallback",
        "asset_check_title": f"{LOG_PREFIX} ASSET CHECK",
        "asset_dir": "  Asset directory : {path}",
        "asset_present": "  Present         : {ok}/{total}",
        "asset_missing": "  Missing         : {count}",
        "asset_missing_first": "\nFirst missing assets:",
        "asset_missing_item": "  {char}   try one of: {candidates}",
        "asset_missing_target": "\nPut at least one candidate PNG in:",
        "asset_target_path": "  {path}",
        "renderer_twemoji": "Local Twemoji: {count} assets; symbols: {font}",
        "renderer_none": "Local Twemoji: 0 assets; symbol fallback: {font}",
        "startup": (
            f"{LOG_PREFIX} Started!  Session: {{session}}\n"
            "  Language   : {lang}\n"
            "  Shortcut   : {hotkey}\n"
            "  Auto-paste : {paste_method}\n"
            "  Pynput     : {pynput_status}\n"
            "  Socket IPC : {socket_path}\n"
            "  Renderer   : {renderer}\n"
            "  Local font : {font_dir}\n"
            "  Twemoji    : {twemoji_dir}\n"
            "  Config     : {config_file}"
        ),
        "pynput_missing_short": "not available; install with: pip install pynput",
        "category_recent": "Recent",
        "category_smileys": "Smileys",
        "category_gestures": "Gestures",
        "category_hearts": "Hearts",
        "category_animals": "Animals",
        "category_nature": "Nature",
        "category_food": "Food",
        "category_vehicles": "Vehicles",
        "category_sport": "Sport",
        "category_objects": "Objects",
        "category_basic": "Basic",
        "category_math": "Math",
        "category_specials": "Special",
    },
    LANG_IT: {
        "header_title": f"{DEV_NAME} {APP_NAME} v{APP_VERSION.split('-', 1)[0]}",
        "window_title": f"{DEV_NAME} {APP_NAME}",
        "hotkey_badge": APP_HOTKEY_DISPLAY,
        "clear_recent_button": "Cancella Recenti",
        "clear_recent_tooltip": "Cancella la cronologia degli emoji usati di recente",
        "clear_recent_done": "Cronologia Recenti cancellata",
        "recent_empty": "Nessun emoji recente.\nSeleziona qualcosa per vederlo qui.",
        "search_placeholder": "Cerca emoji o carattere…",
        "no_results": "Nessun risultato",
        "service_privacy": "Privacy",
        "service_license": "Licenza",
        "service_issue": "Segnala problema",
        "service_privacy_tooltip": "Informativa sulla privacy",
        "service_license_tooltip": "Licenza MIT",
        "service_issue_tooltip": "Segnala un problema su GitHub",
        "tray_tooltip": f"{DEV_NAME} {APP_NAME}  [{APP_HOTKEY_DISPLAY}]",
        "tray_open": f"Apri {APP_NAME}",
        "tray_paste_info": f"{APP_HOTKEY_DISPLAY} • incolla: {{method}}",
        "title_icon_tooltip": f"{DEV_NAME} su GitHub",
        "tray_quit": "Esci",
        "copied_notification": "'{char}' copiato negli appunti — premi Ctrl+V",
        "system_tray_unavailable": f"{LOG_PREFIX} System tray non disponibile.",
        "hotkey_missing": (
            f"{LOG_PREFIX} pynput non disponibile → scorciatoia globale disabilitata.\n"
            "              Installa con: pip install pynput\n"
            "              Oppure configura una scorciatoia KDE che esegue:\n"
            "              python {file} --show"
        ),
        "hotkey_error": f"{LOG_PREFIX} Errore listener hotkey: {{error}}",
        "socket_error": f"{LOG_PREFIX} Socket server error: {{error}}",
        "xdotool_error": f"{LOG_PREFIX} xdotool error: {{error}}",
        "ydotool_error": f"{LOG_PREFIX} ydotool error: {{error}}",
        "local_font_load_error": f"{LOG_PREFIX} Errore caricamento font locale {{path}}: {{error}}",
        "local_fonts": f"{LOG_PREFIX} Font locali: {{fonts}}",
        "symbol_font": f"{LOG_PREFIX} Font simboli: «{{font}}»",
        "symbol_font_partial": f"{LOG_PREFIX} Font simboli (match parziale): «{{font}}»",
        "symbol_font_fallback": f"{LOG_PREFIX} Font simboli: fallback sans-serif",
        "asset_check_title": f"{LOG_PREFIX} ASSET CHECK",
        "asset_dir": "  Cartella asset : {path}",
        "asset_present": "  Presenti       : {ok}/{total}",
        "asset_missing": "  Mancanti       : {count}",
        "asset_missing_first": "\nPrimi asset mancanti:",
        "asset_missing_item": "  {char}   prova uno di: {candidates}",
        "asset_missing_target": "\nMetti almeno uno dei PNG candidati in:",
        "asset_target_path": "  {path}",
        "renderer_twemoji": "Twemoji locale: {count} asset; simboli: {font}",
        "renderer_none": "Twemoji locale: 0 asset; fallback simboli: {font}",
        "startup": (
            f"{LOG_PREFIX} Avviato!  Sessione: {{session}}\n"
            "  Lingua     : {lang}\n"
            "  Scorciatoia: {hotkey}\n"
            "  Auto-paste : {paste_method}\n"
            "  Pynput     : {pynput_status}\n"
            "  Socket IPC : {socket_path}\n"
            "  Renderer   : {renderer}\n"
            "  Font local : {font_dir}\n"
            "  Twemoji    : {twemoji_dir}\n"
            "  Config     : {config_file}"
        ),
        "pynput_missing_short": "non disponibile; installa con: pip install pynput",
        "category_recent": "Recenti",
        "category_smileys": "Faccine",
        "category_gestures": "Gesti",
        "category_hearts": "Cuori",
        "category_animals": "Animali",
        "category_nature": "Natura",
        "category_food": "Cibo",
        "category_vehicles": "Veicoli",
        "category_sport": "Sport",
        "category_objects": "Oggetti",
        "category_basic": "Base",
        "category_math": "Matematica",
        "category_specials": "Speciali",
    },
}

TRAY_THEME_ICON_CANDIDATES = [
    "face-smile",
    "face-smile-big",
    "emblem-favorite",
    "insert-emoticon",
    "accessories-character-map",
]


def tr(key: str, **kwargs) -> str:
    """Return the localized string for the current system language."""
    lang_table = STRINGS.get(APP_LANG, STRINGS[LANG_EN])
    value = lang_table.get(key, STRINGS[LANG_EN].get(key, key))
    return value.format(**kwargs) if kwargs else value


def make_footer_link(text_key: str, tooltip_key: str, url: str) -> QPushButton:
    """Create a compact footer link button."""
    btn = QPushButton(tr(text_key))
    btn.setFlat(True)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip(tr(tooltip_key))
    btn.setStyleSheet(footer_link_button_style())
    btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
    return btn


CATEGORY_RECENT = "⭐ Recenti"
CATEGORY_SMILEYS = "😊 Faccine"
CATEGORY_GESTURES = "👋 Gesti"
CATEGORY_HEARTS = "❤️ Cuori"
CATEGORY_ANIMALS = "🐱 Animali"
CATEGORY_NATURE = "🌺 Natura"
CATEGORY_FOOD = "🍕 Cibo"
CATEGORY_VEHICLES = "🚗 Veicoli"
CATEGORY_SPORT = "⚽ Sport"
CATEGORY_OBJECTS = "💼 Oggetti"
CATEGORY_BASIC = "🔤 Base"
CATEGORY_MATH = "∑ Matematica"
CATEGORY_SPECIALS = "🔣 Speciali"

CATEGORY_I18N_KEYS = {
    CATEGORY_RECENT: "category_recent",
    CATEGORY_SMILEYS: "category_smileys",
    CATEGORY_GESTURES: "category_gestures",
    CATEGORY_HEARTS: "category_hearts",
    CATEGORY_ANIMALS: "category_animals",
    CATEGORY_NATURE: "category_nature",
    CATEGORY_FOOD: "category_food",
    CATEGORY_VEHICLES: "category_vehicles",
    CATEGORY_SPORT: "category_sport",
    CATEGORY_OBJECTS: "category_objects",
    CATEGORY_BASIC: "category_basic",
    CATEGORY_MATH: "category_math",
    CATEGORY_SPECIALS: "category_specials",
}


def category_label(category: str) -> str:
    """Localized category label for text-only UI contexts."""
    return tr(CATEGORY_I18N_KEYS.get(category, "category_specials"))


def category_tooltip(category: str) -> str:
    """Plain-text tooltip for tab buttons (no emoji prefix to avoid rendering gaps)."""
    return category_label(category)

# Runtime font and pixmap cache
SYMBOL_FONT: str = ""        # font for symbols/math/typography not covered by Twemoji
_px_cache: dict = {}          # pre-rendered pixmap cache


def setup_symbol_font() -> str:
    """
    Find a text font for symbols, math, and typography.
    Twemoji covers emoji, but not many characters in the Special tab
    (∞, ∑, ℝ, «», etc.); those are drawn with a normal Unicode font.
    """
    global SYMBOL_FONT

    candidates = [
        "Noto Sans Symbols",      # zodiac, religious/gender signs, assorted symbols
        "Noto Sans Symbols 2",    # monochrome emoji-symbols, dice, cards, technical signs
        "Noto Sans Math",         # ℕ ℝ ∑ ⟵ etc.
        "DejaVu Sans",
        "Liberation Sans",
        "FreeSans",
        "Symbola",
        "sans-serif",
    ]

    available = set(QFontDatabase.families())
    for c in candidates:
        if c == "sans-serif" or c in available:
            SYMBOL_FONT = c
            print(tr("symbol_font", font=c))
            return c

    # Partial match for systems that register slightly different family names.
    for family in sorted(available):
        fl = family.lower()
        if "symbols" in fl or "math" in fl or "dejavu" in fl:
            SYMBOL_FONT = family
            print(tr("symbol_font_partial", font=family))
            return family

    SYMBOL_FONT = "sans-serif"
    print(tr("symbol_font_fallback"))
    return SYMBOL_FONT

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

CONFIG_DIR  = Path.home() / ".config" / "emojipicker"
CONFIG_FILE = CONFIG_DIR / "config.json"
RECENT_FILE = CONFIG_DIR / "recent.json"
SOCKET_PATH = f"/tmp/emojipicker_{os.getuid()}.sock"

SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "x11").lower()

DEFAULT_CONFIG = {
    "hotkey":       APP_HOTKEY_CONFIG,
    "btn_size":     42,
    "grid_cols":    11,
    "recent_max":   36,
    "auto_paste":   True,
}


APP_THEME_LIGHT = {
    "bg":                   "#ffffff",
    "text":                 "#222222",
    "nav_bg":               "#f5f5f5",
    "nav_border":           "#e8e8e8",
    "accent":               "#ffa726",
    "accent_text":          "#ffffff",
    "accent_shadow":        "rgba(0, 0, 0, 0.25)",
    "btn_color":            "#222222",
    "btn_hover_bg":         "#eeeeee",
    "bg_alt":               "#fff3e0",
    "text_alt":             "#222222",
    "footer_bg":            "#1565d8",
    "footer_text":          "#ffffff",
    "footer_link_hover_bg": "rgba(255, 255, 255, 0.15)",
    "footer_divider":       "rgba(255, 255, 255, 0.35)",
    "ctx_bg":               "#ffffff",
    "ctx_border":           "#e0e0e0",
    "ctx_shadow":           "rgba(0, 0, 0, 0.18)",
    "ctx_text":             "#222222",
    "ctx_separator":        "#e8e8e8",
    "container_shadow":     "rgba(0, 0, 0, 0.15)",
}

APP_THEME_DARK = {
    **APP_THEME_LIGHT,
    "bg":               "#1e1e1e",
    "text":             "#eeeeee",
    "nav_bg":           "#252525",
    "nav_border":       "#333333",
    "btn_color":        "#bbbbbb",
    "btn_hover_bg":     "#333333",
    "bg_alt":           "#332514",
    "text_alt":         "#eeeeee",
    "ctx_bg":           "#252525",
    "ctx_border":       "#383838",
    "ctx_shadow":       "rgba(0, 0, 0, 0.50)",
    "ctx_text":         "#eeeeee",
    "ctx_separator":    "#383838",
    "container_shadow": "rgba(0, 0, 0, 0.50)",
}


def _use_dark_palette() -> bool:
    """Return True when the active Qt palette looks dark."""
    app = QApplication.instance()
    if app is None:
        return False
    return app.palette().color(QPalette.ColorRole.Window).lightness() < 128


def app_theme() -> dict[str, str]:
    """Return the app color set matching the current KDE/Qt theme."""
    return APP_THEME_DARK if _use_dark_palette() else APP_THEME_LIGHT


def ui_color(name: str) -> str:
    """Return a color from the active app palette."""
    return app_theme()[name]


def _qcolor(name: str) -> QColor:
    """Return a QColor from the active app palette."""
    return QColor(ui_color(name))


def icon_button_style() -> str:
    """Stylesheet for compact icon-like buttons."""
    t = app_theme()
    return f"""
        QPushButton {{
            border: none;
            border-radius: 6px;
            background: transparent;
            color: {t['btn_color']};
            padding: 0px;
        }}
        QPushButton:hover {{
            background: {t['btn_hover_bg']};
            color: {t['accent']};
        }}
        QPushButton:pressed {{
            background: {t['accent']};
            color: {t['accent_text']};
        }}
    """


def text_button_style() -> str:
    """Stylesheet for small text buttons."""
    t = app_theme()
    return f"""
        QPushButton {{
            border: none;
            border-radius: 6px;
            background: transparent;
            color: {t['btn_color']};
            padding: 3px 8px;
        }}
        QPushButton:hover {{
            background: {t['btn_hover_bg']};
            color: {t['accent']};
        }}
        QPushButton:pressed {{
            background: {t['accent']};
            color: {t['accent_text']};
        }}
        QPushButton:disabled {{
            color: {t['nav_border']};
        }}
    """


def category_button_style() -> str:
    """Stylesheet for category buttons."""
    t = app_theme()
    return f"""
        QPushButton {{
            border: none;
            border-radius: 6px;
            background: transparent;
            padding: 0px;
        }}
        QPushButton:hover {{
            background: {t['btn_hover_bg']};
        }}
        QPushButton:checked {{
            background: {t['bg_alt']};
            border-bottom: 2px solid {t['accent']};
        }}
        QPushButton:pressed {{
            background: {t['accent']};
        }}
    """


def scroll_area_style() -> str:
    """Stylesheet for emoji and search scroll areas."""
    t = app_theme()
    return f"""
        QScrollArea {{
            border: none;
            background: {t['bg']};
        }}
        QScrollArea > QWidget > QWidget {{
            background: {t['bg']};
        }}
        QScrollBar:vertical {{
            background: {t['nav_bg']};
            width: 6px;
            margin: 0px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['btn_hover_bg']};
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t['accent']};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


def search_bar_style() -> str:
    """Stylesheet for the search field."""
    t = app_theme()
    return f"""
        QLineEdit {{
            background: {t['ctx_bg']};
            border: 1px solid {t['ctx_border']};
            border-radius: 8px;
            color: {t['ctx_text']};
            padding: 7px 10px;
            selection-background-color: {t['accent']};
            selection-color: {t['accent_text']};
        }}
        QLineEdit:focus {{
            border-color: {t['accent']};
        }}
    """


def menu_style() -> str:
    """Stylesheet for the tray context menu."""
    t = app_theme()
    return f"""
        QMenu {{
            background: {t['ctx_bg']};
            color: {t['ctx_text']};
            border: 1px solid {t['ctx_border']};
            border-radius: 8px;
            padding: 4px 0px;
        }}
        QMenu::item {{
            padding: 7px 18px 7px 14px;
        }}
        QMenu::item:selected {{
            background: {t['accent']};
            color: {t['accent_text']};
        }}
        QMenu::separator {{
            height: 1px;
            background: {t['ctx_separator']};
            margin: 4px 0px;
        }}
    """


def card_style() -> str:
    """Stylesheet for the main picker card."""
    t = app_theme()
    return f"""
        QFrame#card {{
            background: {t['bg']};
            color: {t['text']};
            border: 1px solid {t['nav_border']};
            border-radius: 12px;
        }}
    """


def header_style() -> str:
    """Stylesheet for the header strip."""
    t = app_theme()
    return f"""
        QFrame#header {{
            background: {t['nav_bg']};
            border-bottom: 1px solid {t['nav_border']};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }}
    """


def hotkey_badge_style() -> str:
    """Stylesheet for the hotkey badge."""
    t = app_theme()
    return f"""
        QLabel#hotkeyBadge {{
            background: {t['bg_alt']};
            color: {t['text_alt']};
            border-radius: 4px;
            padding: 2px 7px;
        }}
    """


def footer_style() -> str:
    """Stylesheet for the footer strip."""
    t = app_theme()
    return f"""
        QFrame#footer {{
            background: {t['footer_bg']};
            color: {t['footer_text']};
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        }}
        QFrame#footer QLabel {{
            color: {t['footer_text']};
        }}
    """


def footer_link_button_style() -> str:
    """Stylesheet for footer link buttons."""
    t = app_theme()
    return f"""
        QPushButton {{
            border: none;
            border-radius: 4px;
            background: transparent;
            color: {t['footer_text']};
            padding: 1px 5px;
            text-decoration: none;
        }}
        QPushButton:hover {{
            background: {t['footer_link_hover_bg']};
        }}
        QPushButton:pressed {{
            background: {t['footer_link_hover_bg']};
        }}
    """


def muted_label_style() -> str:
    """Stylesheet for secondary/empty-state labels."""
    t = app_theme()
    return f"""
        QLabel#mutedLabel {{
            color: {t['btn_color']};
        }}
    """


def apply_card_shadow(card: QFrame) -> None:
    """Apply a soft shadow to the picker card."""
    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(18)
    shadow.setOffset(0, 4)
    shadow.setColor(QColor(0, 0, 0, 128 if _use_dark_palette() else 38))
    card.setGraphicsEffect(shadow)


# ── EMOJI DATA BY CATEGORY ───────────────────────────────────────────────────

EMOJI_DATA: dict[str, list[str]] = {
    CATEGORY_RECENT: [],   # Filled at runtime

    CATEGORY_SMILEYS: [
        "😀","😃","😄","😁","😆","😅","🤣","😂","🙂","🙃","😉","😊","😇",
        "🥰","😍","🤩","😘","😗","☺️","😚","😙","🥲","😋","😛","😜","🤪",
        "😝","🤑","🤗","🤭","🤫","🤔","🤐","🤨","😐","😑","😶","😏","😒",
        "🙄","😬","🤥","😌","😔","😪","🤤","😴","😷","🤒","🤕","🤢","🤮",
        "🤧","🥵","🥶","🥴","😵","🤯","🤠","🥳","🥸","😎","🤓","🧐","😕",
        "😟","🙁","☹️","😮","😯","😲","😳","🥺","😦","😧","😨","😰","😥",
        "😢","😭","😱","😖","😣","😞","😓","😩","😫","🥱","😤","😡","😠",
        "🤬","😈","👿","💀","☠️","💩","🤡","👹","👺","👻","👽","👾","🤖",
    ],

    CATEGORY_GESTURES: [
        "👋","🤚","🖐️","✋","🖖","👌","🤌","🤏","✌️","🤞","🤟","🤘","🤙",
        "👈","👉","👆","🖕","👇","☝️","👍","👎","✊","👊","🤛","🤜","👏",
        "🙌","🫶","👐","🤲","🤝","🙏","✍️","💅","🤳","💪","🦾","🦿","🦵",
        "🦶","👂","🦻","👃","🫀","🫁","🧠","🦷","🦴","👀","👁️","👅","👄","🫦",
    ],

    CATEGORY_HEARTS: [
        "❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💔",
        "❤️‍🔥","❤️‍🩹","❣️","💕","💞","💓","💗","💖","💘","💝","💟","♥️","💋","💌",
    ],

    CATEGORY_ANIMALS: [
        "🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷",
        "🐸","🐵","🙈","🙉","🙊","🐔","🐧","🐦","🐤","🦆","🦅","🦉","🦇",
        "🐺","🐗","🐴","🦄","🐝","🐛","🦋","🐌","🐞","🐜","🦟","🦗","🕷️",
        "🦂","🐢","🐍","🦎","🦖","🦕","🐙","🦑","🦐","🦞","🦀","🐡","🐠",
        "🐟","🐬","🐳","🐋","🦈","🐊","🐅","🐆","🦓","🦍","🦧","🦣","🐘",
        "🦛","🦏","🐪","🐫","🦒","🦘","🦬","🐃","🐂","🐄","🐎","🐖","🐏",
        "🐑","🦙","🐐","🦌","🐕","🐩","🦮","🐕‍🦺","🐈","🐈‍⬛","🪶","🐓",
        "🦃","🦤","🦚","🦜","🦢","🦩","🕊️","🐇","🦝","🦨","🦡","🦫","🦦",
        "🦥","🐁","🐀","🐿️","🦔",
    ],

    CATEGORY_NATURE: [
        "🌸","🌼","🌻","🌹","🥀","🌷","🌱","🌲","🌳","🌴","🌵","🌾","🍀",
        "🍁","🍂","🍃","🍄","🌰","🐚","🪸","🌊","💧","💦","🌧️","⛈️","🌩️",
        "🌨️","❄️","☃️","⛄","🌬️","💨","🌪️","🌈","☀️","🌤️","⛅","🌥️","☁️",
        "🌦️","🌫️","🌀","🌙","🌛","🌜","🌝","🌞","⭐","🌟","💫","✨","⚡",
        "☄️","🔥","🌍","🌎","🌏","🗻","🏔️","⛰️","🌋","🏕️","🏖️","🏜️","🏝️","🏞️",
    ],

    CATEGORY_FOOD: [
        "🍏","🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🫐","🍈","🍒","🍑",
        "🥭","🍍","🥥","🥝","🍅","🍆","🥑","🥦","🥬","🥒","🌶️","🫑","🧄",
        "🧅","🥔","🍠","🫘","🌽","🥕","🫛","🧆","🥙","🧇","🥞","🧈","🍳",
        "🥚","🍖","🍗","🥩","🥓","🌭","🍔","🍟","🍕","🫓","🥪","🌮","🌯",
        "🫔","🥗","🥘","🫕","🍝","🍜","🍲","🍛","🍣","🍱","🥟","🦪","🍤",
        "🍙","🍚","🍘","🍥","🥮","🍡","🧁","🍰","🎂","🍮","🍭","🍬","🍫",
        "🍿","🍩","🍪","🥜","🍯","🧃","🥤","🧋","☕","🍵","🫖","🍺","🍻",
        "🥂","🍷","🫗","🥃","🍸","🍹","🧉","🍾",
    ],

    CATEGORY_VEHICLES: [
        "🚗","🚕","🚙","🚌","🚎","🏎️","🚓","🚑","🚒","🚐","🛻","🚚","🚛",
        "🚜","🏍️","🛵","🛺","🚲","🛴","🛹","🛼","⛽","🚨","🚥","🚦","🛑",
        "🚧","⚓","🛟","⛵","🚤","🛥️","🛳️","⛴️","🚢","✈️","🛩️","🛫","🛬",
        "🪂","💺","🚁","🚟","🚠","🚡","🛰️","🚀","🛸","🪐",
    ],

    CATEGORY_SPORT: [
        "⚽","🏀","🏈","⚾","🥎","🎾","🏐","🏉","🥏","🎱","🏓","🏸","🏒",
        "🏑","🥍","🏏","🪃","🥅","⛳","🪁","🏹","🎣","🤿","🥊","🥋","🏆",
        "🥇","🥈","🥉","🏅","🎖️","🎗️","🎪","🤹","🎭","🩰","🎨","🎬","🎤",
        "🎧","🎼","🎹","🥁","🪘","🎷","🎺","🎸","🪕","🎻","🎲","♟️","🎯",
        "🎳","🎰","🎮","🕹️",
    ],

    CATEGORY_OBJECTS: [
        "💻","🖥️","🖨️","⌨️","🖱️","🖲️","💽","💾","💿","📀","📱","☎️","📞",
        "📟","📠","📺","📻","🧭","⏱️","⏰","⏲️","🕰️","⌚","💡","🔦","🕯️",
        "💎","🔮","🪄","🧿","📿","💈","⚗️","🔭","🔬","🩹","🩺","💊","💉",
        "🩸","🩼","🩻","🚪","🛗","🪞","🪟","🛏️","🛋️","🚽","🚿","🛁","🧴",
        "🧷","🧹","🧺","🧻","🪣","🧼","🫧","🪥","🧽","🧯","🛒","📦","📫",
        "📌","📍","✂️","📎","📏","📐","✏️","🔍","🔎","🔑","🗝️","🔒","🔓","🔐",
    ],

    CATEGORY_BASIC: [
        # Digits
        "0","1","2","3","4","5","6","7","8","9",
        # Lowercase Latin letters
        "a","b","c","d","e","f","g","h","i","j","k","l","m",
        "n","o","p","q","r","s","t","u","v","w","x","y","z",
        # Uppercase Latin letters
        "A","B","C","D","E","F","G","H","I","J","K","L","M",
        "N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
        # Common accents for Italian and European languages
        "à","è","é","ì","ò","ù","À","È","É","Ì","Ò","Ù",
        "á","í","ó","ú","Á","Í","Ó","Ú","â","ê","î","ô","û",
        "ä","ë","ï","ö","ü","ç","Ç","ñ","Ñ",
        # Common punctuation and symbols
        ".",",",";",":","!","?","'","\"","`","´","^","~",
        "_","-","–","—","+","=","*","/","\\","|",
        "@","#","$","%","&","§","¶","°",
        "(",")","[","]","{","}","<",">",
        "«","»","“","”","‘","’","…","·","•",
        "€","£","¥","¢","₿","©","®","™",
    ],

    CATEGORY_MATH: [
        # Basic operators and comparisons
        "+","−","±","∓","×","÷","=","≠","≈","≃","≅","≡",
        "<",">","≤","≥","¬","∧","∨",
        # Roots, sums, integrals, constants
        "√","∛","∜","∞","∑","∏","∫","∬","∮",
        "∂","∇","∆","π","τ","∝","%","‰","′","″","°",
        # Sets and logic
        "∈","∉","∋","∅","∪","∩","⊂","⊃","⊆","⊇",
        "∀","∃","∄","⇒","⇔","⊕","⊗","⊙",
        "ℕ","ℤ","ℚ","ℝ","ℂ","ℵ",
    ],

    CATEGORY_SPECIALS: [
        # Math
        "∞","≈","≠","≤","≥","±","∓","×","÷","√","∛","∜","∑","∏","∫",
        "∂","∇","∆","∈","∉","∋","∅","∪","∩","⊂","⊃","⊆","⊇","∀","∃",
        "∄","⊕","⊗","⊙","ℕ","ℤ","ℚ","ℝ","ℂ","ℵ","π","∝","∞",
        # Currencies
        "€","£","¥","¢","₹","₿","₽","₩","₺","₴","₸","₦","₫","₱","₡","₵",
        # Typography
        "«","»","‹","›","„","\u201C","\u201D","\u2018","\u2019",
        "‚","—","–","…","·","•","†","‡","§","¶","©","®","™","°","′","″","‰",
        # Arrows
        "←","→","↑","↓","↔","↕","↖","↗","↘","↙",
        "⇐","⇒","⇑","⇓","⇔","⇕","⟵","⟶","⟷","⟸","⟹","⟺","↩","↪",
        "⇄","⇆","⇇","⇉","↫","↬","↭","↮","↯","↰","↱","↲","↳","↴","↵",
        # Lowercase Greek
        "α","β","γ","δ","ε","ζ","η","θ","ι","κ","λ","μ",
        "ν","ξ","ο","π","ρ","σ","τ","υ","φ","χ","ψ","ω",
        # Uppercase Greek
        "Α","Β","Γ","Δ","Ε","Ζ","Η","Θ","Ι","Κ","Λ","Μ",
        "Ν","Ξ","Ο","Π","Ρ","Σ","Τ","Υ","Φ","Χ","Ψ","Ω",
        # Stars and symbols
        "★","☆","✦","✧","✩","✪","✫","✬","✭","✮","✯","✰",
        "♠","♣","♥","♦","♤","♧","♡","♢","♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓",
        "☐","☑","☒","☓","✓","✔","✗","✘","⊞","⊟","⊠","⊡",
        "⚀","⚁","⚂","⚃","⚄","⚅","♩","♪","♫","♬","♭","♮","♯",
        "№","℃","℉","Å","µ","ℓ","⌀","⌂","⌘","⌛","⌚","✉","☎","☮","☯","☸","✝","☪",
        "⚕","⚖","⚗","⚙","⚛","⚜","⚝","⚞","⚟","⚠","⚡","⚢","⚣","⚤","⚥","⚦","⚧","⚨","⚩",
    ],
}

# Text characters are rendered with Unicode fonts, not Twemoji.
SPECIAL_SYMBOL_CHARS = set(EMOJI_DATA.get(CATEGORY_SPECIALS, []))
BASIC_TEXT_CHARS = set(EMOJI_DATA.get(CATEGORY_BASIC, []))
MATH_TEXT_CHARS = set(EMOJI_DATA.get(CATEGORY_MATH, []))
TEXT_SYMBOL_CHARS = SPECIAL_SYMBOL_CHARS | BASIC_TEXT_CHARS | MATH_TEXT_CHARS

# Character sets used to choose the best primary font family.
# Qt usually falls back between families, but on KDE/XWayland it may miss
# some glyphs; these sets guide the primary family choice.
MATH_SYMBOL_CHARS = set(
    "∞≈≠≤≥±∓×÷√∛∜∑∏∫∂∇∆∈∉∋∅∪∩⊂⊃⊆⊇∀∃∄⊕⊗⊙ℕℤℚℝℂℵπ∝"
    "⟵⟶⟷⟸⟹⟺≃≅≡∬∮τ∧∨¬⇒⇔−"
)

NOTO_SYMBOLS1_CHARS = set(
    "♈♉♊♋♌♍♎♏♐♑♒♓"
    "☮☯☸✝☪⚕⚖⚗⚙⚛⚜⚝⚞⚟⚢⚣⚤⚥⚦⚧⚨⚩"
    "⌀⌂⌘"
)

NOTO_SYMBOLS2_CHARS = set(
    "★☆✦✧✩✪✫✬✭✮✯✰♠♣♥♦♤♧♡♢"
    "☐☑☒☓✓✔✗✘⊞⊟⊠⊡⚀⚁⚂⚃⚄⚅"
    "♩♪♫♬♭♮♯№℃℉Åµℓ⌛⌚✉☎⚠⚡"
)

# Symbols from the Special tab that Twemoji also ships as PNG files.
# Pasting still uses the original Unicode character.
TWEMOJI_SPECIAL_FALLBACK_CHARS = set(
    "©®™"
    "↔↕↖↗↘↙↩↪"
    "⌛⌚⌨✉☎"
    "☑☠☹☺☮☯☸☪"
    "♠♣♥♦"
    "♈♉♊♋♌♍♎♏♐♑♒♓♟"
    "✔"
    "⚕⚖⚗⚙⚛⚜⚠⚡⚧"
    "❣❤"
)

TAB_ICON_CANDIDATES = {
    CATEGORY_RECENT:   ["⭐", "✨", "😀"],
    CATEGORY_SMILEYS:  ["😀", "😃", "😊"],
    CATEGORY_GESTURES:    ["👋", "👍", "👌"],
    CATEGORY_HEARTS:   ["❤️", "💙", "💕"],
    CATEGORY_ANIMALS:  ["🐱", "🐶", "🐼"],
    CATEGORY_NATURE:   ["🌺", "🌸", "🌻"],
    CATEGORY_FOOD:     ["🍕", "🍔", "🍎"],
    CATEGORY_VEHICLES:  ["🚗", "🚀", "✈️"],
    CATEGORY_SPORT:    ["⚽", "🏆", "🎮"],
    CATEGORY_OBJECTS:  ["💻", "📱", "📦"],
    CATEGORY_BASIC:    ["🔤", "⌨️", "✏️"],
    CATEGORY_MATH:     ["🔢", "🧮", "⚙"],
    CATEGORY_SPECIALS: ["🔣", "✨", "✔"],
}

TAB_ICON_CHARS = {category: candidates[0] for category, candidates in TAB_ICON_CANDIDATES.items()}


# ── CONFIG AND RECENTS ───────────────────────────────────────────────────────

class Config:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_FILE) as f:
                self._d = {**DEFAULT_CONFIG, **json.load(f)}
        except Exception:
            self._d = dict(DEFAULT_CONFIG)

    def save(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._d, f, indent=2)

    def __getitem__(self, k):
        return self._d.get(k, DEFAULT_CONFIG.get(k))

    def __setitem__(self, k, v):
        self._d[k] = v


class RecentEmojis:
    def __init__(self, max_items: int = 36):
        self.max_items = max_items
        self._list: list[str] = self._load()

    def _load(self) -> list[str]:
        try:
            with open(RECENT_FILE) as f:
                return json.load(f)
        except Exception:
            return []

    def add(self, ch: str) -> None:
        if ch in self._list:
            self._list.remove(ch)
        self._list.insert(0, ch)
        self._list = self._list[: self.max_items]
        try:
            with open(RECENT_FILE, "w") as f:
                json.dump(self._list, f)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear recent characters and update the local history file."""
        self._list.clear()
        try:
            with open(RECENT_FILE, "w") as f:
                json.dump([], f)
        except Exception:
            try:
                RECENT_FILE.unlink(missing_ok=True)
            except Exception:
                pass

    @property
    def items(self) -> list[str]:
        return list(self._list)


# ── CROSS-THREAD SIGNAL BRIDGE ───────────────────────────────────────────────

class AppSignals(QObject):
    toggle_window = Signal()
    show_window   = Signal()

signals = AppSignals()


# ── FOCUS TRACKER + AUTO-PASTE ───────────────────────────────────────────────

class FocusTracker:
    """Track the previous window for auto-paste."""

    def __init__(self):
        self._win_id: str | None = None
        self._has_xdotool = self._check("xdotool")
        self._has_ydotool = self._check("ydotool")

    @staticmethod
    def _check(cmd: str) -> bool:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    @property
    def paste_method(self) -> str:
        if SESSION_TYPE == "wayland":
            return "ydotool" if self._has_ydotool else "clipboard"
        return "xdotool" if self._has_xdotool else "clipboard"

    def capture(self) -> None:
        """Capture the active window before showing the picker."""
        if not self._has_xdotool or SESSION_TYPE == "wayland":
            return
        try:
            r = subprocess.run(
                ["xdotool", "getactivewindow"],
                capture_output=True, text=True, timeout=1
            )
            if r.returncode == 0 and r.stdout.strip():
                self._win_id = r.stdout.strip()
        except Exception:
            self._win_id = None

    def paste_to_previous(self) -> bool:
        """Restore focus and simulate Ctrl+V in a background thread."""
        win_id = self._win_id

        def _x11():
            time.sleep(0.15)
            try:
                if win_id:
                    subprocess.run(
                        ["xdotool", "windowfocus", "--sync", win_id], timeout=2
                    )
                    time.sleep(0.07)
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "ctrl+v"], timeout=2
                )
            except Exception as e:
                print(tr("xdotool_error", error=e))

        def _wayland():
            time.sleep(0.15)
            try:
                subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], timeout=2)
            except Exception as e:
                print(tr("ydotool_error", error=e))

        if SESSION_TYPE == "wayland" and self._has_ydotool:
            threading.Thread(target=_wayland, daemon=True).start()
            return True
        elif self._has_xdotool:
            threading.Thread(target=_x11, daemon=True).start()
            return True
        return False


focus_tracker = FocusTracker()


# ── EMOJI BUTTON ─────────────────────────────────────────────────────────────

class EmojiButton(QLabel):
    """Emoji button drawn as an image.

    Hover and pressed states are painted manually instead of using a QLabel
    stylesheet, keeping native Qt/KDE tooltips untouched.
    """
    clicked = Signal()

    def __init__(self, char: str, size: int = 42, parent=None):
        super().__init__("", parent)
        self.char = char
        self._size = size
        self._hover = False
        self._pressed = False
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        px = render_emoji_pixmap(char, max(18, size - 8))
        if not px.isNull():
            self.setPixmap(px)
        else:
            # Final fallback: Qt text, useful for monochrome symbols.
            self.setText(char)
            f = QFont(SYMBOL_FONT if SYMBOL_FONT else "sans-serif")
            f.setPointSize(max(13, size - 22))
            self.setFont(f)

        try:
            name = unicodedata.name(char[0], "")
            self.setToolTip(name.title() if name else char)
        except Exception:
            self.setToolTip(char)

    def paintEvent(self, event):
        if self._hover or self._pressed:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect().adjusted(1, 1, -2, -2)

            if self._pressed:
                p.setBrush(_qcolor("accent"))
                p.setPen(_qcolor("accent"))
            else:
                p.setBrush(_qcolor("btn_hover_bg"))
                p.setPen(_qcolor("nav_border"))

            p.drawRoundedRect(rect, 7, 7)
            p.end()

        super().paintEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        was_pressed = self._pressed
        self._pressed = False
        self.update()

        if (
            event.button() == Qt.MouseButton.LeftButton
            and was_pressed
            and self.rect().contains(event.pos())
        ):
            self.clicked.emit()

        super().mouseReleaseEvent(event)


# ── RENDERER TWEMOJI PNG ─────────────────────────────────────────────────────

APP_DIR = Path(__file__).resolve().parent
LOCAL_FONT_DIR = APP_DIR / "assets" / "fonts"
TWEMOJI_ASSET_DIR = APP_DIR / "assets" / "twemoji"


def load_local_fonts() -> list[str]:
    """Load .ttf/.otf/.ttc fonts from ./assets/fonts, if present."""
    loaded: list[str] = []
    if not LOCAL_FONT_DIR.exists():
        return loaded

    for path in sorted(LOCAL_FONT_DIR.iterdir()):
        if path.suffix.lower() not in {".ttf", ".otf", ".ttc"}:
            continue
        try:
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id >= 0:
                families = QFontDatabase.applicationFontFamilies(font_id)
                loaded.extend(families)
        except Exception as e:
            print(tr("local_font_load_error", path=path, error=e))

    if loaded:
        print(tr("local_fonts", fonts=", ".join(loaded)))
    return loaded


def _emoji_codepoint_candidates(ch: str) -> list[str]:
    """Return possible Twemoji file names, e.g. ❤️‍🔥 -> 2764-fe0f-200d-1f525."""
    raw = [ord(c) for c in ch if ord(c) != 0xFE0E]
    variants: list[list[int]] = []
    if raw:
        variants.append(raw)
        no_fe0f = [cp for cp in raw if cp != 0xFE0F]
        variants.append(no_fe0f)

        # Some text symbols become emoji only with FE0F; try that form too.
        if 0xFE0F not in raw and len(raw) == 1:
            variants.append([raw[0], 0xFE0F])

    out: list[str] = []
    seen: set[str] = set()
    for v in variants:
        if not v:
            continue
        key = "-".join(f"{cp:x}" for cp in v)
        if key not in seen:
            out.append(key)
            seen.add(key)
    return out


def _twemoji_cache_path(code: str) -> Path:
    return TWEMOJI_ASSET_DIR / f"{code}.png"


def _get_twemoji_png_bytes(ch: str) -> bytes | None:
    for code in _emoji_codepoint_candidates(ch):
        cache = _twemoji_cache_path(code)
        if cache.exists() and cache.stat().st_size > 100:
            try:
                return cache.read_bytes()
            except Exception:
                pass
    return None


def _twemoji_pixmap(ch: str, size: int) -> QPixmap:
    data = _get_twemoji_png_bytes(ch)
    if not data:
        return QPixmap()
    px = QPixmap()
    if not px.loadFromData(data, "PNG") or px.isNull():
        return QPixmap()
    return px.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def required_twemoji_candidates() -> dict[str, tuple[str, list[str]]]:
    """Return each emoji with the local Twemoji file names to try.

    Twemoji is not fully uniform about variation selectors: some emoji written
    as character + U+FE0F are stored without FE0F, while many ZWJ sequences keep
    it. Asset checks therefore accept multiple candidate names.
    """
    out: dict[str, tuple[str, list[str]]] = {}
    seen_chars: set[str] = set()

    for category, emojis in EMOJI_DATA.items():
        if category == CATEGORY_RECENT:
            continue
        for ch in emojis:
            # Pure text symbols stay out of the Twemoji manifest.
            # Exceptions are Unicode symbols that Twemoji covers as images
            # and that are used as visual fallbacks in the Special tab (♈, ⌛, ☮...).
            if ch in TEXT_SYMBOL_CHARS and ch not in TWEMOJI_SPECIAL_FALLBACK_CHARS:
                continue
            if ch in seen_chars:
                continue
            seen_chars.add(ch)
            candidates = [f"{code}.png" for code in _emoji_codepoint_candidates(ch)]
            if candidates:
                out[ch] = (ch, candidates)

    # Tab icons must also be available locally.
    # They are chosen from category items, but are added
    # explicitly to the manifest to avoid future regressions.
    for ch in TAB_ICON_CHARS.values():
        if ch in seen_chars:
            continue
        seen_chars.add(ch)
        candidates = [f"{code}.png" for code in _emoji_codepoint_candidates(ch)]
        if candidates:
            out[ch] = (ch, candidates)

    return out


def check_twemoji_assets(verbose: bool = True) -> int:
    """Check that each emoji has at least one local PNG candidate."""
    required = required_twemoji_candidates()
    missing: list[tuple[str, list[str]]] = []
    ok = 0

    for ch, (_, candidates) in sorted(required.items(), key=lambda item: item[0]):
        found = False
        for filename in candidates:
            path = TWEMOJI_ASSET_DIR / filename
            if path.exists() and path.stat().st_size > 100:
                found = True
                break
        if found:
            ok += 1
        else:
            missing.append((ch, candidates))

    if verbose:
        print(tr("asset_check_title"))
        print(tr("asset_dir", path=TWEMOJI_ASSET_DIR))
        print(tr("asset_present", ok=ok, total=len(required)))
        print(tr("asset_missing", count=len(missing)))
        if missing:
            print(tr("asset_missing_first"))
            for ch, candidates in missing[:80]:
                print(tr("asset_missing_item", char=ch, candidates=" | ".join(candidates)))
            print(tr("asset_missing_target"))
            print(tr("asset_target_path", path=TWEMOJI_ASSET_DIR))
    return 0 if not missing else 2


def emoji_renderer_info() -> str:
    cached = 0
    try:
        if TWEMOJI_ASSET_DIR.exists():
            cached = len(list(TWEMOJI_ASSET_DIR.glob("*.png")))
    except Exception:
        cached = 0
    if cached:
        return tr("renderer_twemoji", count=cached, font=SYMBOL_FONT or "?")
    return tr("renderer_none", font=SYMBOL_FONT or "?")


def _dedupe(seq: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in seq:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _symbol_font_families_for(char: str) -> list[str]:
    """Choose an optimized fallback font list for a single symbol."""
    c = char.replace("\ufe0f", "").replace("\ufe0e", "")

    common_tail = [
        "Noto Sans Symbols",
        "Noto Sans Symbols 2",
        "Noto Sans Math",
        SYMBOL_FONT or "",
        "DejaVu Sans",
        "Liberation Sans",
        "FreeSans",
        "Symbola",
        "sans-serif",
    ]

    if c in MATH_SYMBOL_CHARS:
        return _dedupe(["Noto Sans Math", *common_tail])
    if c in NOTO_SYMBOLS1_CHARS:
        return _dedupe(["Noto Sans Symbols", *common_tail])
    if c in NOTO_SYMBOLS2_CHARS:
        return _dedupe(["Noto Sans Symbols 2", *common_tail])

    return _dedupe([SYMBOL_FONT or "Noto Sans Symbols", *common_tail])


def _pixmap_has_pixels(px: QPixmap) -> bool:
    """Return True if the pixmap contains visible non-transparent pixels."""
    if px.isNull():
        return False
    img = px.toImage().convertToFormat(px.toImage().Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    # Lightweight sampling, enough to detect empty pixmaps.
    for y in range(0, h, max(1, h // 8)):
        for x in range(0, w, max(1, w // 8)):
            c = img.pixelColor(x, y)
            if c.alpha() > 0 and (c.red() or c.green() or c.blue()):
                return True
    return False


def _display_symbol_text(char: str) -> str:
    """Return display text for Special-tab symbols without variation selectors."""
    return char.replace("\ufe0f", "").replace("\ufe0e", "")


def _font_family_supports_text(family: str, text: str, px_size: int) -> bool:
    """Return True if the font family really contains all glyphs in text."""
    if not family:
        return False
    try:
        f = QFont(family)
        f.setPixelSize(px_size)
        fm = QFontMetrics(f)
        for ch in text:
            cp = ord(ch)
            if cp in (0xFE0E, 0xFE0F, 0x200D):
                continue
            try:
                if not fm.inFontUcs4(cp):
                    return False
            except Exception:
                if not fm.inFont(ch):
                    return False
        return True
    except Exception:
        return False


def _best_symbol_font_family(char: str, px_size: int) -> str | None:
    """Choose a family that actually supports the symbol."""
    text = _display_symbol_text(char)
    for family in _symbol_font_families_for(text):
        if _font_family_supports_text(family, text, px_size):
            return family

    # Last pass: search any Qt-known font that covers the symbol.
    # Slower, but cached after the first render.
    try:
        for family in QFontDatabase.families():
            fl = family.lower()
            if any(x in fl for x in ("noto", "symbol", "dejavu", "liberation", "free", "math")):
                if _font_family_supports_text(family, text, px_size):
                    return family
    except Exception:
        pass
    return None


def _symbol_pixmap(char: str, size: int = 32, require_glyph: bool = False) -> QPixmap:
    """Render a special character with a text Unicode font, not emoji."""
    display_text = _display_symbol_text(char)
    key = (display_text, size, "symbol-v127", SYMBOL_FONT, require_glyph)
    if key in _px_cache:
        return QPixmap(_px_cache[key])

    # Wide symbols and double-struck letters need a bit more room.
    if len(display_text) <= 2:
        px_size = max(14, int(size * 0.62))
    else:
        px_size = max(11, int(size * 0.50))

    family = _best_symbol_font_family(display_text, px_size)
    if require_glyph and not family:
        return QPixmap()

    families = _symbol_font_families_for(display_text)
    if family:
        families = _dedupe([family, *families])

    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    f = QFont(families[0] if families else (SYMBOL_FONT or "sans-serif"))
    try:
        f.setFamilies(families)
    except Exception:
        pass
    f.setPixelSize(px_size)

    p.setFont(f)
    p.setPen(_qcolor("text"))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, display_text)
    p.end()

    _px_cache[key] = QPixmap(px)
    return px


def render_emoji_pixmap(char: str, size: int = 32) -> QPixmap:
    """Render a grid character.

    Text symbols use Unicode fonts; emoji use local Twemoji PNG assets; any
    remaining fallback is rendered with a text/symbol font.
    """
    key = (char, size, "twemoji+symbols", SYMBOL_FONT)
    if key in _px_cache:
        return QPixmap(_px_cache[key])

    # Special-category characters are intentionally rendered as text.
    # Avoid mixed Twemoji/color symbols and, more importantly,
    # avoid tofu boxes when Noto Color Emoji does not cover ∑, ℝ, «», etc.
    if char in TEXT_SYMBOL_CHARS:
        # Some Special-tab symbols are also Twemoji images (♈, ♉, ⌛, ☮...).
        # On KDE/Qt a font can report a glyph but draw it empty/tofu; for these
        # characters, prefer the local PNG so the grid stays visible.
        # Pasting still uses the original Unicode character, not the image.
        if char in TWEMOJI_SPECIAL_FALLBACK_CHARS:
            tw = _twemoji_pixmap(char, size)
            if not tw.isNull():
                _px_cache[key] = QPixmap(tw)
                return tw

        # Math, currency, Greek, and typography symbols should stay textual.
        px = _symbol_pixmap(char, size, require_glyph=True)
        if not px.isNull() and _pixmap_has_pixels(px):
            _px_cache[key] = QPixmap(px)
            return px

        # Last Twemoji attempt for any other available character.
        tw = _twemoji_pixmap(char, size)
        if not tw.isNull():
            _px_cache[key] = QPixmap(tw)
            return tw

        px = _symbol_pixmap(char, size, require_glyph=False)
        _px_cache[key] = QPixmap(px)
        return px

    # Primary robust renderer: local Twemoji PNG assets.
    tw = _twemoji_pixmap(char, size)
    if not tw.isNull():
        _px_cache[key] = QPixmap(tw)
        return tw

    # Final fallback: symbolic/text font.
    px = _symbol_pixmap(char, size)
    _px_cache[key] = QPixmap(px)
    return px


def _icon_from_png(path: str, sizes: tuple[int, ...] = (16, 22, 24, 32, 48, 64, 128, 256)) -> QIcon:
    """Load a PNG as QIcon after validating the pixmap."""
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return QIcon()

    icon = QIcon()
    for size in sizes:
        icon.addPixmap(
            pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    icon.addPixmap(pixmap)
    return icon


def app_window_icon() -> QIcon:
    """Return the app/window icon from Qt resources."""
    icon = _icon_from_png(APP_ICON_RESOURCE)
    if not icon.isNull():
        return icon

    fallback = APP_DIR / "assets" / "charm.png"
    if fallback.exists():
        icon = _icon_from_png(str(fallback))
        if not icon.isNull():
            return icon

    return QIcon()


def _blank_pixmap(size: int) -> QPixmap:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    return px


def local_twemoji_pixmap_for_chars(chars: list[str], size: int = 22) -> QPixmap:
    """Return the first available local Twemoji PNG among candidates."""
    for ch in chars:
        px = _twemoji_pixmap(ch, size)
        if not px.isNull() and _pixmap_has_pixels(px):
            return px
    return _blank_pixmap(size)


def tab_pixmap_for_category(category: str, size: int = 22) -> QPixmap:
    """Return a local pixmap for a category tab."""
    candidates = list(TAB_ICON_CANDIDATES.get(category, ["⭐", "😀"]))

    # Dynamic fallback: if a fixed candidate is missing, use an available PNG
    # from the category items, avoiding pure text symbols.
    for ch in EMOJI_DATA.get(category, []):
        if ch in TEXT_SYMBOL_CHARS and ch not in TWEMOJI_SPECIAL_FALLBACK_CHARS:
            continue
        if ch not in candidates:
            candidates.append(ch)

    return local_twemoji_pixmap_for_chars(candidates, size)


class CategoryBar(QWidget):
    """Horizontal category bar with local Twemoji icons."""

    category_changed = Signal(int)

    _SS_NORMAL = ""
    _SS_ACTIVE = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: list[QPushButton] = []
        self._current: int = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

    def populate(self, categories: list[str]) -> None:
        layout = self.layout()
        for btn in self._buttons:
            layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()

        for i, cat in enumerate(categories):
            btn = QPushButton()
            btn.setFixedHeight(30)
            btn.setStyleSheet(category_button_style())
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCheckable(True)
            px = tab_pixmap_for_category(cat, 18)
            if not px.isNull():
                btn.setIcon(QIcon(px))
                btn.setIconSize(QSize(18, 18))
            btn.setToolTip(category_tooltip(cat))
            btn.clicked.connect(lambda _, idx=i: self.select(idx))
            layout.addWidget(btn)
            self._buttons.append(btn)

        if self._buttons:
            self._apply(self._current if self._current < len(self._buttons) else 0)

    def select(self, index: int) -> None:
        self._apply(index)
        self.category_changed.emit(index)

    def _apply(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)
        self._current = index

    @property
    def current_index(self) -> int:
        return self._current


def build_grid_widget(emojis: list[str], cols: int, btn_size: int, on_click) -> QWidget:
    w = QWidget()
    w.setObjectName("emojiGrid")
    w.setAutoFillBackground(True)
    w.setStyleSheet(f"QWidget#emojiGrid {{ background: {ui_color('bg')}; }}")
    grid = QGridLayout(w)
    grid.setSpacing(2)
    grid.setContentsMargins(4, 4, 4, 4)

    if not emojis:
        lbl = QLabel(tr("recent_empty"))
        lbl.setObjectName("mutedLabel")
        lbl.setStyleSheet(muted_label_style())
        lbl.setContentsMargins(24, 24, 24, 24)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(lbl, 0, 0, 1, cols)
    else:
        for i, ch in enumerate(emojis):
            btn = EmojiButton(ch, btn_size)
            btn.clicked.connect(lambda _checked=False, c=ch: on_click(c))
            grid.addWidget(btn, i // cols, i % cols)

    return w


def build_scroll_grid(emojis: list[str], cols: int, btn_size: int, on_click) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    sa.setStyleSheet(scroll_area_style())
    sa.setWidget(build_grid_widget(emojis, cols, btn_size, on_click))
    return sa


# ── PICKER WINDOW ────────────────────────────────────────────────────────────

class EmojiPickerWindow(QWidget):
    emoji_chosen = Signal(str)

    def __init__(self, cfg: Config, recent: RecentEmojis):
        super().__init__()
        self.cfg    = cfg
        self.recent = recent
        self._bs    = cfg["btn_size"]   # button size
        self._cols  = cfg["grid_cols"]
        self._auto  = cfg["auto_paste"]
        self._search_items: list[str] = []

        self._setup_window()
        self._build_ui()
        self.emoji_chosen.connect(self._handle_chosen)

    # ── Window setup ──────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle(tr("window_title"))
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Width: cols * (btn + gap) + padding
        w = self._cols * (self._bs + 2) + 40
        self.setFixedWidth(w)
        self.setMinimumHeight(460)
        self.setMaximumHeight(640)

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(0)

        # ── Card ─────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(card_style())
        apply_card_shadow(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # ── Header ───────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("header")
        header.setStyleSheet(header_style())
        hdr = QHBoxLayout(header)
        hdr.setContentsMargins(10, 8, 10, 8)
        hdr.setSpacing(6)

        title_icon = QPushButton()
        title_icon.setFixedSize(22, 22)
        title_icon.setFlat(True)
        title_icon.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        title_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        title_icon.setToolTip(tr("title_icon_tooltip"))
        title_icon.setStyleSheet(icon_button_style())
        title_px = app_window_icon().pixmap(22, 22)
        if not title_px.isNull():
            title_icon.setIcon(QIcon(title_px))
            title_icon.setIconSize(QSize(22, 22))
        else:
            title_icon.setText(APP_ICON_CHAR)
        title_icon.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DEV_URL)))

        title = QLabel(tr("header_title"))
        title.setStyleSheet(f"color: {ui_color('text')};")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.Medium)
        title.setFont(title_font)

        hotkey_badge = QLabel(tr("hotkey_badge"))
        hotkey_badge.setObjectName("hotkeyBadge")
        hotkey_badge.setStyleSheet(hotkey_badge_style())
        hotkey_font = hotkey_badge.font()
        hotkey_font.setPointSize(10)
        hotkey_badge.setFont(hotkey_font)
        hotkey_badge.setContentsMargins(7, 2, 7, 2)

        self.clear_recent_btn = QPushButton(tr("clear_recent_button"))
        self.clear_recent_btn.setFixedHeight(22)
        self.clear_recent_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clear_recent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_recent_btn.setToolTip(tr("clear_recent_tooltip"))
        self.clear_recent_btn.setStyleSheet(text_button_style())
        clear_recent_font = self.clear_recent_btn.font()
        clear_recent_font.setPointSize(10)
        self.clear_recent_btn.setFont(clear_recent_font)
        self.clear_recent_btn.clicked.connect(self._clear_history)

        close_btn = QPushButton(CLOSE_BUTTON_TEXT)
        close_btn.setFixedSize(22, 22)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(icon_button_style())
        close_font = close_btn.font()
        close_font.setPointSize(13)
        close_font.setBold(True)
        close_btn.setFont(close_font)
        close_btn.clicked.connect(self.hide)

        hdr.addWidget(title_icon)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self.clear_recent_btn)
        hdr.addSpacing(4)
        hdr.addWidget(hotkey_badge)
        hdr.addSpacing(4)
        hdr.addWidget(close_btn)

        # ── Search bar ───────────────────────────────────────────
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(tr("search_placeholder"))
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.setStyleSheet(search_bar_style())
        search_font = self.search_bar.font()
        search_font.setPointSize(13)
        self.search_bar.setFont(search_font)
        self.search_bar.textChanged.connect(self._on_search)
        self.search_bar.returnPressed.connect(self._pick_first)

        # ── Category bar and stacked content ─────────────────────
        self.cat_bar = CategoryBar()
        self.cat_bar.category_changed.connect(self._on_category_changed)

        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        self.stack.setStyleSheet(f"QStackedWidget#contentStack {{ background: {ui_color('bg')}; }}")

        self._populate_categories()

        # ── Hidden search results scroll area ────────────────────
        self.search_scroll = QScrollArea()
        self.search_scroll.setWidgetResizable(True)
        self.search_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_scroll.setStyleSheet(scroll_area_style())
        self.search_scroll.hide()

        # ── Footer service bar ───────────────────────────────────
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setStyleSheet(footer_style())
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 7, 10, 7)
        footer_layout.setSpacing(6)

        footer_font = self.font()
        footer_font.setPointSize(10)

        copyright_label = QLabel(APP_COPYRIGHT)
        copyright_label.setFont(footer_font)
        copyright_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        privacy_link = make_footer_link(
            "service_privacy", "service_privacy_tooltip", SERVICE_PRIVACY_URL
        )
        license_link = make_footer_link(
            "service_license", "service_license_tooltip", SERVICE_LICENSE_URL
        )
        issue_link = make_footer_link(
            "service_issue", "service_issue_tooltip", SERVICE_ISSUES_URL
        )

        for link in (privacy_link, license_link, issue_link):
            link.setFont(footer_font)

        footer_layout.addWidget(copyright_label)
        footer_layout.addStretch()
        footer_layout.addWidget(privacy_link)
        footer_layout.addWidget(license_link)
        footer_layout.addWidget(issue_link)

        body = QWidget()
        body.setObjectName("body")
        body.setStyleSheet(f"QWidget#body {{ background: {ui_color('bg')}; }}")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 8, 10, 8)
        body_layout.setSpacing(7)
        body_layout.addWidget(self.search_bar)
        body_layout.addWidget(self.cat_bar)
        body_layout.addWidget(self.stack)
        body_layout.addWidget(self.search_scroll)

        cl.addWidget(header)
        cl.addWidget(body)
        cl.addWidget(footer)
        outer.addWidget(card)

    def _populate_categories(self):
        # Clear all widgets from the stack.
        while self.stack.count():
            self.stack.removeWidget(self.stack.widget(0))

        categories = list(EMOJI_DATA.keys())
        for category in categories:
            items = self.recent.items if category == CATEGORY_RECENT else EMOJI_DATA[category]
            sa = build_scroll_grid(
                items, self._cols, self._bs,
                lambda c: self.emoji_chosen.emit(c)
            )
            self.stack.addWidget(sa)

        self.cat_bar.populate(categories)

        if hasattr(self, "clear_recent_btn"):
            self.clear_recent_btn.setEnabled(bool(self.recent.items))

        # If Recents is empty, start from Smileys (index 1).
        start = 0 if self.recent.items else 1
        self.cat_bar.select(start)
        self.stack.setCurrentIndex(start)

    def _on_category_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)

    def _clear_history(self):
        """Clear Recents without touching configuration or assets."""
        self.recent.clear()
        self._search_items = []
        self._populate_categories()
        if self.search_bar.text().strip():
            self._on_search(self.search_bar.text())
        QToolTip.showText(QCursor.pos(), tr("clear_recent_done"))

    # ── Search ─────────────────────────────────────────────────────

    def _on_search(self, text: str):
        t = text.strip()
        if not t:
            self.cat_bar.show()
            self.stack.show()
            self.search_scroll.hide()
            return

        self.cat_bar.hide()
        self.stack.hide()
        self.search_scroll.show()

        results: list[str] = []
        seen: set[str] = set()
        tl = t.lower()

        for category, emojis in EMOJI_DATA.items():
            src = self.recent.items if category == CATEGORY_RECENT else emojis
            for ch in src:
                if ch in seen:
                    continue
                try:
                    name = unicodedata.name(ch[0], "").lower()
                    match = tl in name or tl in ch.lower()
                except Exception:
                    match = tl in ch.lower()
                if match:
                    results.append(ch)
                    seen.add(ch)

        self._search_items = results

        w = build_grid_widget(
            results[:200], self._cols, self._bs,
            lambda c: self.emoji_chosen.emit(c)
        )
        self.search_scroll.setWidget(w)

        if not results:
            empty = QLabel(tr("no_results"))
            empty.setObjectName("mutedLabel")
            empty.setStyleSheet(muted_label_style())
            empty.setContentsMargins(24, 24, 24, 24)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.search_scroll.setWidget(empty)

    def _pick_first(self):
        if self._search_items:
            self.emoji_chosen.emit(self._search_items[0])

    # ── Emoji selection ─────────────────────────────────────────────

    def _handle_chosen(self, char: str):
        self.recent.add(char)
        QApplication.clipboard().setText(char)
        self.hide()

        if self._auto:
            focus_tracker.paste_to_previous()

    # ── Position and visibility ────────────────────────────────────

    def show_at_cursor(self):
        self.search_bar.clear()
        self._on_search("")
        self._populate_categories()  # refresh recents

        self.adjustSize()
        cursor = QCursor.pos()
        screen = QApplication.screenAt(cursor)
        if screen:
            sg = screen.availableGeometry()
            w, h = self.width(), self.height()
            x = min(cursor.x(), sg.right()  - w - 8)
            y = min(cursor.y(), sg.bottom() - h - 8)
            x = max(sg.left() + 8, x)
            y = max(sg.top()  + 8, y)
            self.move(x, y)

        self.show()
        self.raise_()
        self.activateWindow()
        self.search_bar.setFocus()

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.Type.WindowDeactivate:
            QTimer.singleShot(80, self._maybe_hide)
        super().changeEvent(event)

    def _maybe_hide(self):
        if not self.isActiveWindow():
            self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)


# ── HOTKEY LISTENER (separate thread) ────────────────────────────────────────

class HotkeyListener:
    def __init__(self, combo: str, callback):
        self._combo    = combo
        self._callback = callback

    def start(self):
        if not PYNPUT_AVAILABLE:
            print(tr("hotkey_missing", file=__file__))
            return
        threading.Thread(target=self._run, daemon=True, name="hotkey-listener").start()

    def _run(self):
        try:
            hotkey = pynput_keyboard.HotKey(
                pynput_keyboard.HotKey.parse(self._combo),
                self._callback,
            )

            def on_press(key):
                try:
                    hotkey.press(listener.canonical(key))
                except Exception:
                    pass

            def on_release(key):
                try:
                    hotkey.release(listener.canonical(key))
                except Exception:
                    pass

            listener = pynput_keyboard.Listener(
                on_press=on_press, on_release=on_release
            )
            listener.start()
            listener.join()
        except Exception as e:
            print(tr("hotkey_error", error=e))


# ── SYSTEM TRAY ──────────────────────────────────────────────────────────────

class TrayManager:
    def __init__(self, app: QApplication, picker: EmojiPickerWindow):
        self.app    = app
        self.picker = picker
        self.tray   = QSystemTrayIcon()
        self._build()

    # ── Icon ───────────────────────────────────────────────────────

    def _make_icon(self) -> QIcon:
        """Tray icon from KDE/freedesktop theme, with emoji fallback."""
        for name in TRAY_THEME_ICON_CANDIDATES:
            icon = QIcon.fromTheme(name)
            if not icon.isNull():
                return icon
        px = render_emoji_pixmap(APP_ICON_CHAR, 64)
        icon = QIcon()
        if not px.isNull():
            icon.addPixmap(px)
        return icon

    # ── Setup ──────────────────────────────────────────────────────

    def _build(self):
        self.tray.setIcon(self._make_icon())
        self.tray.setToolTip(tr("tray_tooltip"))

        menu = QMenu()
        menu.setStyleSheet(menu_style())
        menu_font = menu.font()
        menu_font.setPointSize(13)
        menu.setFont(menu_font)

        open_a = menu.addAction(QIcon.fromTheme("go-up"), tr("tray_open"))
        open_a.triggered.connect(self._show)
        menu.addSeparator()

        method = focus_tracker.paste_method
        info_a = menu.addAction(
            QIcon.fromTheme("edit-paste"),
            tr("tray_paste_info", method=method)
        )
        info_a.setEnabled(False)
        menu.addSeparator()

        quit_a = menu.addAction(QIcon.fromTheme("application-exit"), tr("tray_quit"))
        quit_a.triggered.connect(self.app.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

    def _on_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show()

    def _show(self):
        focus_tracker.capture()
        self.picker.show_at_cursor()

    def notify_copied(self, char: str):
        self.tray.showMessage(
            APP_NAME,
            tr("copied_notification", char=char),
            QSystemTrayIcon.MessageIcon.Information,
            1800,
        )


# ── SOCKET IPC (--show from KDE shortcuts on Wayland) ────────────────────────

def send_show_command() -> bool:
    """Send "show" to the already-running instance via Unix socket."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(SOCKET_PATH)
        s.send(IPC_SHOW_COMMAND.encode("utf-8"))
        s.close()
        return True
    except Exception:
        return False


def start_socket_server():
    """Listen on the socket for remote commands."""
    def _serve():
        try:
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
            srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            srv.bind(SOCKET_PATH)
            srv.listen(4)
            while True:
                conn, _ = srv.accept()
                try:
                    msg = conn.recv(32).decode().strip()
                    if msg == IPC_SHOW_COMMAND:
                        signals.show_window.emit()
                finally:
                    conn.close()
        except Exception as e:
            print(tr("socket_error", error=e))

    threading.Thread(target=_serve, daemon=True, name="ipc-server").start()


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    show_on_start = "--show" in sys.argv

    # If another instance is already running, ask it to show the picker
    # and exit immediately. Keep --check-assets independent.
    if "--check-assets" not in sys.argv:
        if send_show_command():
            sys.exit(0)

    # ── App setup ─────────────────────────────────────────────────
    # Force XCB on mixed environments (KDE Wayland with XWayland).
    if SESSION_TYPE != "wayland":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setQuitOnLastWindowClosed(False)

    window_icon = app_window_icon()
    app.setWindowIcon(window_icon)

    load_local_fonts()
    setup_symbol_font()

    if "--check-assets" in sys.argv:
        sys.exit(check_twemoji_assets(verbose=True))

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print(tr("system_tray_unavailable"))
        sys.exit(1)

    # ── Main objects ───────────────────────────────────────────────
    cfg    = Config()
    recent = RecentEmojis(cfg["recent_max"])
    picker = EmojiPickerWindow(cfg, recent)
    picker.setWindowIcon(window_icon)
    tray   = TrayManager(app, picker)

    # Copied feedback when auto-paste is unavailable.
    def patched_handle(char: str):
        picker.recent.add(char)
        QApplication.clipboard().setText(char)
        picker.hide()
        if cfg["auto_paste"]:
            pasted = focus_tracker.paste_to_previous()
            if not pasted:
                tray.notify_copied(char)
        else:
            tray.notify_copied(char)

    picker.emoji_chosen.disconnect()
    picker.emoji_chosen.connect(patched_handle)

    # ── Signals ───────────────────────────────────────────────────
    def toggle():
        if picker.isVisible():
            picker.hide()
        else:
            focus_tracker.capture()
            picker.show_at_cursor()

    signals.toggle_window.connect(toggle)
    signals.show_window.connect(lambda: (focus_tracker.capture(), picker.show_at_cursor()))

    if show_on_start:
        QTimer.singleShot(0, signals.show_window.emit)

    # ── Socket IPC ────────────────────────────────────────────────
    start_socket_server()

    # ── Global hotkey ─────────────────────────────────────────────
    def on_hotkey():
        focus_tracker.capture()
        signals.toggle_window.emit()

    listener = HotkeyListener(cfg["hotkey"], on_hotkey)
    listener.start()

    # ── Startup info ──────────────────────────────────────────────
    print(tr(
        "startup",
        session=SESSION_TYPE.upper(),
        lang=APP_LANG.upper(),
        hotkey=cfg["hotkey"],
        paste_method=focus_tracker.paste_method,
        pynput_status="✓" if PYNPUT_AVAILABLE else tr("pynput_missing_short"),
        socket_path=SOCKET_PATH,
        renderer=emoji_renderer_info(),
        font_dir=LOCAL_FONT_DIR,
        twemoji_dir=TWEMOJI_ASSET_DIR,
        config_file=CONFIG_FILE,
    ))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
