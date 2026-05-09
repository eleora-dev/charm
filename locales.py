#!/usr/bin/env python3
"""Localization helpers for Eleòra CharM."""

import locale
import os

LANG_IT = "it"
LANG_EN = "en"
SUPPORTED_LANGS = {LANG_IT, LANG_EN}


_APP_CONTEXT = {
    "DEV_NAME": "Eleòra",
    "APP_NAME": "CharM",
    "APP_VERSION": "1.0",
    "APP_VERSION_BASE": "1.0",
    "APP_HOTKEY_DISPLAY": "Ctrl+Alt+E",
    "LOG_PREFIX": "[CharM]",
}


def configure_locales(**context: object) -> None:
    """Provide application metadata used by localized string templates."""
    _APP_CONTEXT.update({key: str(value) for key, value in context.items()})


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


class _SafeFormatDict(dict):
    """Leave unknown placeholders untouched instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


STRINGS = {
    LANG_EN: {
        "header_title": "{DEV_NAME} {APP_NAME}",
        "window_title": "{DEV_NAME} {APP_NAME} v{APP_VERSION_BASE}",
        "hotkey_badge": "{APP_HOTKEY_DISPLAY}",
        "clear_recent_button": "Clear Recent",
        "clear_recent_tooltip": "Clear the history of recently used emoji",
        "clear_recent_done": "Recent history cleared",
        "recent_empty": "No recent emoji yet.\nUse a few and they’ll appear here.",
        "search_placeholder": "Search emoji or character…",
        "no_results": "No results",
        "service_privacy": "Privacy",
        "service_license": "License",
        "service_issue": "Report issue",
        "service_privacy_tooltip": "Privacy policy",
        "service_license_tooltip": "MIT License",
        "service_issue_tooltip": "Report an issue on GitHub",
        "tray_tooltip": "{DEV_NAME} {APP_NAME}  [{APP_HOTKEY_DISPLAY}]",
        "tray_open": "Open {APP_NAME}",
        "tray_paste_info": "{APP_HOTKEY_DISPLAY} • paste: {method}",
        "title_icon_tooltip": "{DEV_NAME} on GitHub",
        "tray_quit": "Quit",
        "copied_notification": "'{char}' copied to clipboard — press Ctrl+V",
        "system_tray_unavailable": "{LOG_PREFIX} System tray unavailable.",
        "hotkey_missing": (
            "{LOG_PREFIX} pynput is unavailable → global shortcut disabled.\n"
            "              Install with: pip install pynput\n"
            "              Or configure a KDE shortcut that runs:\n"
            "              python {file} --show"
        ),
        "hotkey_error": "{LOG_PREFIX} Hotkey listener error: {error}",
        "socket_error": "{LOG_PREFIX} Socket server error: {error}",
        "xdotool_error": "{LOG_PREFIX} xdotool error: {error}",
        "ydotool_error": "{LOG_PREFIX} ydotool error: {error}",
        "local_font_load_error": "{LOG_PREFIX} Local font load error {path}: {error}",
        "local_fonts": "{LOG_PREFIX} Local fonts: {fonts}",
        "symbol_font": "{LOG_PREFIX} Symbol font: «{font}»",
        "symbol_font_partial": "{LOG_PREFIX} Symbol font (partial match): «{font}»",
        "symbol_font_fallback": "{LOG_PREFIX} Symbol font: sans-serif fallback",
        "asset_check_title": "{LOG_PREFIX} ASSET CHECK",
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
            "{LOG_PREFIX} Started!  Session: {session}\n"
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
        "header_title": "{DEV_NAME} {APP_NAME}",
        "window_title": "{DEV_NAME} {APP_NAME} v{APP_VERSION_BASE}",
        "hotkey_badge": "{APP_HOTKEY_DISPLAY}",
        "clear_recent_button": "Cancella Recenti",
        "clear_recent_tooltip": "Cancella la cronologia degli emoji usati di recente",
        "clear_recent_done": "Cronologia Recenti cancellata",
        "recent_empty": "Nessun emoji recente.\nUsane qualcuno e lo vedrai comparire qui.",
        "search_placeholder": "Cerca emoji o carattere…",
        "no_results": "Nessun risultato",
        "service_privacy": "Privacy",
        "service_license": "Licenza",
        "service_issue": "Segnala problema",
        "service_privacy_tooltip": "Informativa sulla privacy",
        "service_license_tooltip": "Licenza MIT",
        "service_issue_tooltip": "Segnala un problema su GitHub",
        "tray_tooltip": "{DEV_NAME} {APP_NAME}  [{APP_HOTKEY_DISPLAY}]",
        "tray_open": "Apri {APP_NAME}",
        "tray_paste_info": "{APP_HOTKEY_DISPLAY} • incolla: {method}",
        "title_icon_tooltip": "{DEV_NAME} su GitHub",
        "tray_quit": "Esci",
        "copied_notification": "'{char}' copiato negli appunti — premi Ctrl+V",
        "system_tray_unavailable": "{LOG_PREFIX} System tray non disponibile.",
        "hotkey_missing": (
            "{LOG_PREFIX} pynput non disponibile → scorciatoia globale disabilitata.\n"
            "              Installa con: pip install pynput\n"
            "              Oppure configura una scorciatoia KDE che esegue:\n"
            "              python {file} --show"
        ),
        "hotkey_error": "{LOG_PREFIX} Errore listener hotkey: {error}",
        "socket_error": "{LOG_PREFIX} Socket server error: {error}",
        "xdotool_error": "{LOG_PREFIX} xdotool error: {error}",
        "ydotool_error": "{LOG_PREFIX} ydotool error: {error}",
        "local_font_load_error": "{LOG_PREFIX} Errore caricamento font locale {path}: {error}",
        "local_fonts": "{LOG_PREFIX} Font locali: {fonts}",
        "symbol_font": "{LOG_PREFIX} Font simboli: «{font}»",
        "symbol_font_partial": "{LOG_PREFIX} Font simboli (match parziale): «{font}»",
        "symbol_font_fallback": "{LOG_PREFIX} Font simboli: fallback sans-seri",
        "asset_check_title": "{LOG_PREFIX} ASSET CHECK",
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
            "{LOG_PREFIX} Avviato!  Sessione: {session}\n"
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


def tr(key: str, **kwargs: object) -> str:
    """Return the localized string for the current system language."""
    lang_table = STRINGS.get(APP_LANG, STRINGS[LANG_EN])
    value = lang_table.get(key, STRINGS[LANG_EN].get(key, key))
    return value.format_map(_SafeFormatDict({**_APP_CONTEXT, **kwargs}))
