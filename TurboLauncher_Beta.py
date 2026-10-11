import os
import sys
import ssl
import certifi


import turbo_log_fix  # вывод всех логов в файл (см. turbo_log_fix.py)


def fix_ssl_for_compiled():
    """Правильный фикс SSL для скомпилированного .exe"""

    if not getattr(sys, 'frozen', False):
        return

    exe_dir = os.path.dirname(sys.executable)

    # Ищем сертификаты в правильном порядке
    cert_paths = [
        # 1. Сертификат из certifi (скопированный в папку с .exe)
        os.path.join(exe_dir, 'certifi', 'cacert.pem'),
        # 2. Сертификат в корневой папке
        os.path.join(exe_dir, 'cacert.pem'),
        # 3. Сертификат из системной папки certifi
        certifi.where(),
    ]

    found_cert = None
    for path in cert_paths:
        if os.path.exists(path):
            found_cert = path
            print(f"[SSL] Найден сертификат: {path}")
            break

    if found_cert:
        # Устанавливаем переменные окружения для requests
        os.environ['SSL_CERT_FILE'] = found_cert
        os.environ['REQUESTS_CA_BUNDLE'] = found_cert
        print(f"[SSL] Сертификат установлен: {found_cert}")
    else:
        print(f"[SSL] ВНИМАНИЕ: Сертификат не найден!")
        print(f"[SSL] Искал в: {cert_paths}")
        # Используем встроенный certifi
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        print(f"[SSL] Использую certifi: {certifi.where()}")


# Применяем фикс
fix_ssl_for_compiled()
import tarfile
import pygame
import minecraft_launcher_lib
import subprocess
import os
import threading
import sys
import json
import psutil
import uuid
import socket
import traceback
import urllib3
import xml.etree.ElementTree as ET
import shutil
import re
import platform
import zipfile
from minecraft_launcher_lib.exceptions import InvalidChecksum
import random
import math
from tkinter import messagebox
was_in_game = False
# ========== API КЛЮЧИ ==========
DISCORD_APP_ID = "1490607305522282496"
DISCORD_WEBHOOK_URL = ""
JSONBIN_BIN_ID = ""
JSONBIN_API_KEY = ""
BOT_TOKEN = ""
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"

# PATCH: gist_backend
# ===== GitHub Gist backend =====
# Токен НЕ хранится в коде. Читается из файла gist_token.txt рядом с лаунчером.
def _load_gist_token():
    import os
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(base, "gist_token.txt")
    if os.path.exists(p):
        try:
            return open(p, encoding="utf-8").read().strip()
        except Exception:
            pass
    return ""

GITHUB_TOKEN = _load_gist_token()
GIST_ID = "ef50b63ec304887a33206a47fd45de1d"
GIST_FILENAME = "players_stats.json"
GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"
GIST_RAW_URL = f"https://gist.githubusercontent.com/TurboTeamOfficial/{GIST_ID}/raw/{GIST_FILENAME}"

def _gist_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "TurboLauncher/1.0",
    }

def gist_read():
    """Читает players_stats.json из Gist. Возвращает dict или None."""
    if not GITHUB_TOKEN:
        return None
    try:
        import time as _t
        url = GIST_RAW_URL + f"?cb={int(_t.time())}"
        r = requests.get(url, headers={"User-Agent": "TurboLauncher/1.0"}, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  Gist read error: {e}")
    return None

def gist_write(data):
    """Пишет data (dict) в players_stats.json в Gist. True/False."""
    if not GITHUB_TOKEN:
        print("  Gist: токен не задан (gist_token.txt)")
        return False
    try:
        import json as _json
        body = {"files": {GIST_FILENAME: {"content": _json.dumps(data, ensure_ascii=False, indent=2)}}}
        r = requests.patch(GIST_API_URL, headers=_gist_headers(), json=body, timeout=15)
        if r.status_code == 200:
            return True
        print(f"  Gist write error: {r.status_code} {r.text[:150]}")
    except Exception as e:
        print(f"  Gist write error: {e}")
    return False


# ===== ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК =====
def global_exception_handler(exc_type, exc_value, exc_traceback):
    import traceback
    error_text = str(exc_value)
    # Печатаем трейсбек: раньше при ошибке до импорта tk обработчик падал сам
    # (NameError: name 'tk' is not defined) и пользователь не видел ничего
    try:
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    except Exception:
        pass
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка/Error", f"Произошла ошибка:\n{error_text}")
        root.destroy()
    except Exception:
        pass
    sys.exit(1)

sys.excepthook = global_exception_handler

import gc
def get_consistent_uuid(username):
    import hashlib
    md5 = hashlib.md5(f"OfflinePlayer:{username}".encode()).hexdigest()
    return str(uuid.UUID(md5))
gc.enable()
gc.set_threshold(700, 10, 5)  # Оптимизация сборщика мусора
import sys
import os
def is_admin():
    """Проверяет, запущен ли лаунчер от имени администратора"""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False
def resource_path(relative_path):
    """Получает правильный путь к файлу: в разработке или в собранном .exe"""
    try:

        base_path = sys._MEIPASS
    except Exception:

        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

import logging
from datetime import datetime

logger = None
LOG_FILE_PATH = None

def setup_logging():
    """Настраивает систему логирования в файл"""
    global logger, LOG_FILE_PATH

    # Определяем путь к лог-файлу
    # Пока используем временный путь, после инициализации GAME_DIR обновим
    if getattr(sys, 'frozen', False):
        temp_dir = os.path.dirname(sys.executable)
    else:
        temp_dir = os.path.dirname(os.path.abspath(__file__))

    LOG_FILE_PATH = os.path.join(temp_dir, "turbo_launcher.log")

    # Создаём логгер
    logger = logging.getLogger('TurboLauncher')
    logger.setLevel(logging.DEBUG)

    # Очищаем старые обработчики
    if logger.handlers:
        logger.handlers.clear()

    # Файловый обработчик
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Консольный обработчик (для отладки)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info(f"Turbo Launcher запущен")
    logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Лог-файл: {LOG_FILE_PATH}")
    logger.info("=" * 60)

    return logger

def update_log_path(game_dir):
    """Обновляет путь к лог-файлу после определения GAME_DIR"""
    global LOG_FILE_PATH, logger
    if logger and game_dir:
        new_log_path = os.path.join(game_dir, "turbo_launcher.log")
        if new_log_path != LOG_FILE_PATH:
            LOG_FILE_PATH = new_log_path
            # Перенастраиваем файловый обработчик
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)
            new_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
            new_handler.setLevel(logging.DEBUG)
            new_handler.setFormatter(
                logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            logger.addHandler(new_handler)
            logger.info(f"Лог-файл перенесён в: {LOG_FILE_PATH}")

def open_log_file():
    """Открывает файл лога в стандартном просмотрщике"""
    global LOG_FILE_PATH
    try:
        if LOG_FILE_PATH and os.path.exists(LOG_FILE_PATH):
            if platform.system() == "Windows":
                os.startfile(LOG_FILE_PATH)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", LOG_FILE_PATH])
            else:  # Linux
                subprocess.run(["xdg-open", LOG_FILE_PATH])
            if logger:
                logger.info(f"Открыт файл лога: {LOG_FILE_PATH}")
        else:
            # Создаём лог-файл если его нет
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(f"Лог-файл Turbo Launcher\n")
                f.write(f"Создан: {datetime.now()}\n")
                f.write("=" * 50 + "\n")
            if platform.system() == "Windows":
                os.startfile(LOG_FILE_PATH)
    except Exception as e:
        if logger:
            logger.error(f"Не удалось открыть файл лога: {e}")

import platform
import subprocess

# Флаг для Windows
if platform.system() == "Windows":
    CREATE_NO_WINDOW = 0x08000000
    # Дополнительно: скрываем консоль у дочерних процессов
    STARTF_USESHOWWINDOW = 0x00000001
    SW_HIDE = 0
else:
    CREATE_NO_WINDOW = 0

INSTALLER_TIMEOUT = 600  # сек: если установщик ядра не отвечает дольше — прерываем и чистим
MODRINTH_RETRIES = 2  # повторов запроса к Modrinth при таймауте

def no_window_kwargs():
    """Аргументы запуска дочерних процессов, чтобы НЕ мелькали окна консоли."""
    if platform.system() != "Windows":
        return {}
    try:
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = SW_HIDE
        return {"creationflags": CREATE_NO_WINDOW, "startupinfo": info}
    except Exception:
        return {"creationflags": CREATE_NO_WINDOW}


# Инициализируем временный логгер
turbo_log_fix.install(globals())
import sys
from contextlib import redirect_stdout, redirect_stderr

class TeeLogger:
    """Перенаправляет stdout и stderr одновременно в консоль и в лог-файл"""

    def __init__(self, log_file_path):
        self.terminal = sys.stdout
        self.log_file = None
        self.log_path = log_file_path

    def write(self, message):
        self.terminal.write(message)
        if self.log_file and not self.log_file.closed:
            try:
                self.log_file.write(message)
                self.log_file.flush()
            except:
                pass

    def flush(self):
        self.terminal.flush()
        if self.log_file and not self.log_file.closed:
            self.log_file.flush()

    def open_log(self):
        try:
            if self.log_file and not self.log_file.closed:
                self.log_file.close()
            self.log_file = open(self.log_path, 'a', encoding='utf-8')
        except:
            pass

# Глобальная переменная для перенаправления
tee = None

def setup_print_redirect(game_dir):
    """Настраивает перенаправление всех print в лог-файл"""
    global tee
    log_path = os.path.join(game_dir, "turbo_launcher.log")
    tee = TeeLogger(log_path)
    tee.open_log()
    sys.stdout = tee
    sys.stderr = tee
    print(f" Весь вывод перенаправлен в лог-файл: {log_path}")

# ЗАПУСК ОБНОВЛЕНИЯ (updater.exe) С ПРОВЕРКОЙ ВЕРСИИ

import subprocess
import sys
import os
import requests
import json

VERSION_FILE = "version.txt"
FILES_LIST_URL = "https://gitflic.ru/project/turboteam/turbo-launcher/blob/raw?file=files.json&inline=false"


def check_for_update():
    """Проверяет, есть ли новая версия на сервере"""
    try:
        local_version = ""
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                local_version = f.read().strip()
        else:
            return False

        resp = requests.get(FILES_LIST_URL, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            server_version = data.get("version", "")
            return server_version != local_version
    except:
        pass
    return False


def check_and_run_updater():
    """Запускает updater.exe только если есть обновление"""

    if not check_for_update():
        print("Версия актуальна, запуск лаунчера...")
        return

    # ВСЕГДА берём директорию, где находится СКРИПТ (а не .exe)
    # Это работает и для .py, и для собранного .exe
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Если запущен собранный .exe, то __file__ может указывать не туда
    # Проверяем оба варианта
    if getattr(sys, 'frozen', False):
        # Для .exe используем sys.executable
        current_dir = os.path.dirname(sys.executable)

    updater_path = os.path.join(current_dir, "updater.exe")

    print(f"Ищу updater.exe в: {current_dir}")
    print(f"Путь: {updater_path}")
    print(f"Существует: {os.path.exists(updater_path)}")

    if os.path.exists(updater_path):
        print("Найдено обновление, запуск updater.exe...")
        subprocess.Popen([updater_path], **no_window_kwargs())
        sys.exit(0)
    else:
        print("updater.exe не найден! Обновление невозможно.")
        print("Запускаю лаунчер без обновления...")


check_and_run_updater()

current_lang = "ru"
LANG_FILE = "lang.json"

def load_languages():
    global TEXTS
    try:
        with open(LANG_FILE, 'r', encoding='utf-8') as f:
            TEXTS = json.load(f)
        print(f"Загружены переводы: {', '.join(TEXTS.keys())}")
    except Exception as e:
        print(f"Ошибка загрузки переводов: {e}")
        TEXTS = {"ru": {}, "en": {}}

def t(key, **kwargs):
    """Получить перевод по ключу с подстановкой параметров"""
    text = TEXTS.get(current_lang, TEXTS.get("ru", {})).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

load_languages()

from pypresence import Presence
import time

DISCORD_APP_ID = "1490607305522282496"

discord_rpc = None
discord_connected = False

def start_discord_presence():
    global discord_rpc, discord_connected
    try:
        discord_rpc = Presence(DISCORD_APP_ID)
        discord_rpc.connect()
        discord_connected = True
        print(" Discord RPC подключён")
        update_discord_presence("В лаунчере", "      ")
    except Exception as e:
        print(f" Discord ошибка: {e}")

def update_discord_presence(state, details, start_time=None):
    global discord_rpc, discord_connected
    if not discord_connected or discord_rpc is None:
        return
    try:
        activity = {
            "state": state,
            "details": details,
            "large_image": "turbo_logo",
            "large_text": "Turbo Launcher"
        }
        if start_time is None:
            activity["start"] = int(time.time())
        else:
            activity["start"] = start_time
        discord_rpc.update(**activity)
    except Exception as e:
        print(f"  Discord ошибка: {e}")

def stop_discord_presence():
    global discord_rpc, discord_connected
    if discord_rpc and discord_connected:
        try:
            discord_rpc.clear()
            discord_rpc.close()
        except:
            pass
        discord_connected = False

DISCORD_WEBHOOK_URL = ""
JSONBIN_BIN_ID = ""
JSONBIN_API_KEY = ""
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"


# PATCH: gist_backend
def update_online_count(username, is_online):
    """Обновляет количество игроков онлайн в GitHub Gist и отправляет в Discord"""

    def _update():
        try:
            data = gist_read() or {"players": [], "count": 0, "last_update": 0}
            players = data.get("players", [])

            if is_online:
                if username not in players:
                    players.append(username)
                    print(f"  {username} добавлен")
            else:
                if username in players:
                    players.remove(username)
                    print(f"  {username} удалён")

            new_data = {
                "players": players,
                "count": len(players),
                "last_update": time.time(),
            }
            if gist_write(new_data):
                print(f"  Gist обновлён: {len(players)} игроков")

            if is_online:
                send_discord_online_count(len(players), username)
            else:
                send_discord_online_count(len(players))
        except Exception as e:
            print(f"  update_online_count error: {e}")

    threading.Thread(target=_update, daemon=True).start()

def send_discord_online_count(count, joined_player=None):
    """Отправляет количество онлайн в Discord"""

    def _send():
        try:
            if joined_player:
                content = f"**Сейчас в игре: {count} игроков, зашел '{joined_player}'**"
            else:
                content = f"**Сейчас в игре: {count} игроков**"

            data = {
                "content": content,
                "username": "Turbo Launcher Stats",
                "avatar_url": "https://i.postimg.cc/TP0wZMDy/Turbo-Launcher-Preview.png"
            }
            requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
            print(f"  Discord: {content}")
        except Exception as e:
            print(f" Ошибка отправки в Discord: {e}")

    threading.Thread(target=_send, daemon=True).start()

# ПЕРЕОПРЕДЕЛЯЕМ requests.get НА БЕЗОПАСНУЮ ВЕРСИЮ
original_get = requests.get

def safe_get(url, **kwargs):
    # Убираем verify если он есть (чтобы не было конфликта)
    kwargs.pop('verify', None)
    session = get_session(url)
    return session.get(url, **kwargs)

requests.get = safe_get
requests.post = lambda url, **kwargs: get_session(url).post(url, **kwargs)
requests.put = lambda url, **kwargs: get_session(url).put(url, **kwargs)
import certifi
import ssl

def get_session(url, timeout=30):
    session = requests.Session()
    session.timeout = timeout

    # Проблемные домены с кривыми сертификатами
    problem_domains = ["gitflic.ru", "bangbang93.com", "bmclapi2.bangbang93.com"]
    is_problem = any(domain in url for domain in problem_domains)

    if is_problem:

        session.verify = get_custom_ca_bundle()
    else:
        session.verify = certifi.where()

    return session

def get_custom_ca_bundle():
    """Создаёт временный CA bundle с добавлением проблемных сертификатов"""
    import tempfile

    # Скачиваем сертификаты проблемных сайтов
    certs_content = ""
    for domain in ["gitflic.ru", "bangbang93.com"]:
        try:
            # Получаем сертификат сайта
            cert_pem = ssl.get_server_certificate((domain, 443))
            certs_content += cert_pem + "\n"
        except:
            pass

    # Добавляем стандартные сертификаты
    with open(certifi.where(), 'r') as f:
        certs_content += f.read()

    # Создаём временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write(certs_content)
        return f.name
# Устанавливаем таймаут для всех сокетов
socket.setdefaulttimeout(30)
def get_safe_game_dir():
    """
    Создаёт портативную папку .turbo_launcher в директории лаунчера.
    """
    try:
        # Определяем директорию запуска
        if getattr(sys, 'frozen', False):
            # Скомпилированный exe
            current_dir = os.path.dirname(sys.executable)
        else:
            # Режим разработки (скрипт)
            current_dir = os.path.dirname(os.path.abspath(__file__))

        # Портативная папка - рядом с лаунчером
        game_dir = os.path.join(current_dir, ".turbo_launcher")

        # Проверяем права на запись
        test_file = os.path.join(current_dir, ".write_test")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except:
            # Нет прав на запись в текущей папке
            print(f"Нет прав на запись в {current_dir}, использую папку пользователя")
            fallback_dir = os.path.join(os.path.expanduser("~"), ".turbo_launcher")
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir

        # Создаём папку
        os.makedirs(game_dir, exist_ok=True)

        # Создаём маркер портативности (опционально)
        portable_marker = os.path.join(game_dir, "portable.txt")
        if not os.path.exists(portable_marker):
            with open(portable_marker, 'w') as f:
                f.write("Turbo Launcher Portable Mode\n")
                f.write(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        print(f" Портативная папка: {game_dir}")

        update_log_path(game_dir)
        return game_dir

    except Exception as e:
        print(f" Ошибка при создании портативной папки: {e}")
        # Fallback - директория пользователя
        fallback_dir = os.path.join(os.path.expanduser("~"), ".turbo_launcher")
        os.makedirs(fallback_dir, exist_ok=True)
        print(f" Использую fallback: {fallback_dir}")
        return fallback_dir
GAME_DIR = get_safe_game_dir()

JAVA_CACHE_FILE = os.path.join(GAME_DIR, "java_cache.json")


def load_java_cache():
    if os.path.exists(JAVA_CACHE_FILE):
        try:
            with open(JAVA_CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_java_cache(cache):
    try:
        with open(JAVA_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except:
        pass


java_cache = load_java_cache()

MODS_CACHE_DIR = os.path.join(GAME_DIR, "mods_cache")
os.makedirs(MODS_CACHE_DIR, exist_ok=True)


def get_mod_cache_filename(mod_name, version):
    import hashlib
    key = f"{mod_name}_{version}"
    return hashlib.md5(key.encode()).hexdigest() + ".jar"


def find_system_java_cached(min_version=8, max_version=17):
    global java_cache
    cache_key = f"java_{min_version}_{max_version}"

    if cache_key in java_cache:
        cached_path = java_cache[cache_key]
        if os.path.exists(cached_path):
            ver = get_java_major_version(cached_path)
            if ver and min_version <= ver <= max_version:
                return cached_path
        else:
            try:
                del java_cache[cache_key]
                save_java_cache(java_cache)
            except:
                pass

    quick_paths = []
    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        java_exe = os.path.join(java_home, "bin", "java.exe" if platform.system() == "Windows" else "java")
        quick_paths.append(java_exe)

    if platform.system() == "Windows":
        quick_paths.extend([
            "C:\\Program Files\\Java\\jdk-17\\bin\\java.exe",
            "C:\\Program Files\\Java\\jdk-11\\bin\\java.exe",
            "C:\\Program Files\\Java\\jdk-8\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jdk-17\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jdk-11\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jdk-8\\bin\\java.exe",
            "C:\\Program Files\\Microsoft\\jdk-17.0.12\\bin\\java.exe",
            "C:\\Program Files\\Microsoft\\jdk-21.0.4\\bin\\java.exe",
        ])
    else:
        quick_paths.extend([
            "/usr/bin/java",
            "/usr/lib/jvm/java-17-openjdk/bin/java",
            "/usr/lib/jvm/java-11-openjdk/bin/java",
            "/usr/lib/jvm/java-8-openjdk/bin/java",
        ])

    for path in quick_paths:
        if os.path.exists(path):
            ver = get_java_major_version(path)
            if ver and min_version <= ver <= max_version:
                java_cache[cache_key] = path
                save_java_cache(java_cache)
                return path

    possible_roots = [
        os.environ.get("JAVA_HOME", ""),
        "C:\\Program Files\\Java",
        "C:\\Program Files (x86)\\Java",
        "C:\\Program Files\\Microsoft\\jdk-*",
        os.path.expanduser("~")
    ]

    if platform.system() == "Windows":
        import glob
        expanded_roots = []
        for root in possible_roots:
            if "*" in root:
                expanded_roots.extend(glob.glob(root))
            elif root and os.path.exists(root):
                expanded_roots.append(root)
        possible_roots = expanded_roots

    found = None
    for root in possible_roots:
        if not root or not os.path.exists(root):
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                if "java.exe" in filenames and "bin" in dirpath:
                    java_path = os.path.join(dirpath, "java.exe")
                    ver = get_java_major_version(java_path)
                    if ver and min_version <= ver <= max_version:
                        found = java_path
                        break
                if found:
                    break
        except:
            continue
        if found:
            break

    if found:
        java_cache[cache_key] = found
        save_java_cache(java_cache)
        return found

    return None


def download_mod_parallel(mod_name, minecraft_version, game_dir, set_status, semaphore):
    try:
        mod_ids = {"sodium": "AANobbMI", "iris": "YL57xq9U", "fabric-api": "P7dR8mSH"}
        if mod_name not in mod_ids:
            return False

        mods_dir = os.path.join(game_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)

        target_version = None
        if minecraft_version in MODS_DB and mod_name in MODS_DB[minecraft_version]:
            target_version = MODS_DB[minecraft_version][mod_name]

        if target_version:
            cache_filename = get_mod_cache_filename(mod_name, target_version)
            cache_path = os.path.join(MODS_CACHE_DIR, cache_filename)

            if os.path.exists(cache_path):
                mod_path = os.path.join(mods_dir, os.path.basename(cache_path))
                shutil.copy2(cache_path, mod_path)
                return True

        with semaphore:
            return download_mod(mod_name, minecraft_version, game_dir, set_status)
    except:
        return False


def install_fabric_mods_parallel(minecraft_version, game_dir, set_status):
    try:
        if minecraft_version.startswith('1.'):
            parts = minecraft_version.split('.')
            minor = int(parts[1])
            if minor < 16:
                set_status(t("st_mods_unsupported", version=minecraft_version))
                return True

        mods_dir = os.path.join(game_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)

        MODS_INFO = {
            "fabric-api": {"id": "P7dR8mSH", "required": True},
            "sodium": {"id": "AANobbMI", "required": False},
            "iris": {"id": "YL57xq9U", "required": False}
        }

        results = {}

        if minecraft_version in MODS_DB:
            import concurrent.futures
            semaphore = threading.Semaphore(3)

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_mod = {}

                for mod_name, mod_info in MODS_INFO.items():
                    if mod_name not in MODS_DB[minecraft_version]:
                        if mod_info["required"]:
                            set_status(t("st_mod_missing_db", mod=mod_name))
                            return False
                        results[mod_name] = False
                        continue

                    future = executor.submit(
                        download_mod_parallel,
                        mod_name, minecraft_version, game_dir, set_status, semaphore
                    )
                    future_to_mod[future] = mod_name

                for future in concurrent.futures.as_completed(future_to_mod):
                    mod_name = future_to_mod[future]
                    try:
                        results[mod_name] = future.result()
                    except:
                        results[mod_name] = False

        if results.get("fabric-api", False):
            return True
        else:
            set_status(t("st_fabric_api_failed"))
            return False
    except:
        return False


install_fabric_mods = install_fabric_mods_parallel

import threading

def parse_and_install_archive(file_path, game_dir):
    """
    Запускает установку в отдельном потоке, чтобы интерфейс не зависал.
    """

    def _worker():
        if not os.path.exists(file_path):
            if not hide_notifications:
                show_notification(t("notif_error"), t("notif_file_not_found"), color=(220, 60, 60))
            return

        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        # ===== 1. .jar (Моды) — обычное уведомление (с защитой по ID) =====
        if ext == '.jar':
            try:
                is_valid_mod = False
                with zipfile.ZipFile(file_path, 'r') as archive:
                    namelist = archive.namelist()
                    if "fabric.mod.json" in namelist:
                        is_valid_mod = True
                    elif "META-INF/mods.toml" in namelist:
                        is_valid_mod = True
                    elif "mcmod.info" in namelist:
                        is_valid_mod = True
                    elif "quilt.mod.json" in namelist:
                        is_valid_mod = True
                    elif "pack.png" in namelist and any(fname.endswith(".json") for fname in namelist):
                        is_valid_mod = True

                if not is_valid_mod:
                    if not hide_notifications:
                        show_notification(t("notif_security"), t("notif_invalid_mod"), color=(220, 60, 60))
                    return

                mods_dir = os.path.join(game_dir, "mods")
                os.makedirs(mods_dir, exist_ok=True)
                dest_path = os.path.join(mods_dir, filename)
                shutil.copy2(file_path, dest_path)

                if not hide_notifications:
                    # СОЗДАЁМ ОБЫЧНОЕ УВЕДОМЛЕНИЕ И СОХРАНЯЕМ ЕГО ID
                    mod_uid = show_notification(
                        t("notif_mod_installed"),
                        t("notif_mod_name", name=filename)
                    )
                    # Это уведомление больше никто не тронет, потому что у него есть свой ID
                return

            except Exception as e:
                if not hide_notifications:
                    show_notification(t("notif_error"), f"{t('notif_mod_name', name=filename)}: {str(e)}",
                                      color=(220, 60, 60))
                return

        # ===== 2. .mrpack (Modrinth модпак) =====
        elif ext == '.mrpack':
            try:
                archive = zipfile.ZipFile(file_path, 'r')
                namelist = archive.namelist()
                if 'modrinth.index.json' not in namelist:
                    archive.close()
                    if not hide_notifications:
                        show_notification(t("notif_error"), t("notif_invalid_mrpack"), color=(220, 60, 60))
                    return

                index_data = json.loads(archive.read('modrinth.index.json'))
                files_list = index_data.get('files', [])
                overrides_path = 'overrides/'

                # Распаковываем overrides
                for name in namelist:
                    if name.startswith(overrides_path) and len(name) > len(overrides_path):
                        dest_name = name[len(overrides_path):]
                        if not dest_name:
                            continue
                        dest_path = os.path.join(game_dir, dest_name)
                        if name.endswith('/'):
                            os.makedirs(dest_path, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with archive.open(name) as src, open(dest_path, 'wb') as dst:
                                shutil.copyfileobj(src, dst)

                # Скачиваем моды
                mods_dir = os.path.join(game_dir, "mods")
                os.makedirs(mods_dir, exist_ok=True)
                total_files = sum(1 for f in files_list if f.get('path', '').endswith('.jar'))
                downloaded = 0
                failed = 0

                # ===== СОЗДАЁМ УВЕДОМЛЕНИЕ С ПРОГРЕССОМ И СОХРАНЯЕМ ЕГО ID =====
                pack_uid = None
                if not hide_notifications:
                    pack_uid = show_progress(
                        text=t("notif_modrinth_progress", current=0, total=total_files),
                        title=t("notif_modrinth_success"),
                        progress=0
                    )

                for file_info in files_list:
                    try:
                        if 'path' not in file_info or not file_info['path'].endswith('.jar'):
                            continue
                        mod_url = file_info.get('downloads', [''])[0]
                        if not mod_url:
                            if 'hashes' in file_info and 'sha1' in file_info['hashes']:
                                version_id = file_info.get('version_id', '')
                                mod_url = f"https://api.modrinth.com/v2/version/{version_id}/download"
                        if not mod_url:
                            failed += 1
                            continue

                        dest_path = os.path.join(mods_dir, os.path.basename(file_info['path']))
                        headers = {'User-Agent': 'TurboLauncher/1.0'}
                        r = requests.get(mod_url, headers=headers, timeout=30)
                        if r.status_code == 200:
                            with open(dest_path, 'wb') as f:
                                f.write(r.content)
                            downloaded += 1
                            if not hide_notifications and pack_uid is not None:
                                progress = int(downloaded / total_files * 100) if total_files > 0 else 0
                                # ОБНОВЛЯЕМ ТОЛЬКО ПО ID
                                update_progress(
                                    pack_uid,
                                    t("notif_modrinth_progress", current=downloaded, total=total_files),
                                    progress
                                )
                        else:
                            failed += 1
                    except Exception:
                        failed += 1

                archive.close()
                if not hide_notifications and pack_uid is not None:
                    if failed == 0:
                        # Завершаем прогресс по ID
                        complete_progress(
                            pack_uid,
                            t("notif_mod_installed"),
                            success=True
                        )
                    else:
                        complete_progress(
                            pack_uid,
                            f"{t('notif_mod_installed')}\n⚠️ {failed} модов не удалось скачать.",
                            success=False,
                            color=(220, 180, 60)
                        )

            except Exception as e:
                if not hide_notifications:
                    show_notification(t("notif_error"), f"{t('notif_mrpack_fail')}: {str(e)}", color=(220, 60, 60))
                return

        # ===== 3. .zip (Ресурспаки, шейдеры, сборки) =====
        elif ext == '.zip':
            try:
                with zipfile.ZipFile(file_path, 'r') as archive:
                    namelist = archive.namelist()
                    if "pack.mcmeta" in namelist and any("assets/" in n.lower() for n in namelist):
                        target_dir = os.path.join(game_dir, "resourcepacks")
                        os.makedirs(target_dir, exist_ok=True)
                        dest_path = os.path.join(target_dir, filename)
                        shutil.copy2(file_path, dest_path)
                        if not hide_notifications:
                            show_notification(t("notif_resourcepack", name=filename))
                        return
                    if any("shaders/" in n.lower() for n in namelist):
                        target_dir = os.path.join(game_dir, "shaderpacks")
                        os.makedirs(target_dir, exist_ok=True)
                        dest_path = os.path.join(target_dir, filename)
                        shutil.copy2(file_path, dest_path)
                        if not hide_notifications:
                            show_notification(t("notif_shaderpack", name=filename))
                        return

                mods_dir = os.path.join(game_dir, "mods")
                os.makedirs(mods_dir, exist_ok=True)
                dest_path = os.path.join(mods_dir, filename)
                shutil.copy2(file_path, dest_path)
                if not hide_notifications:
                    show_notification(t("notif_modpack", name=filename))

            except Exception as e:
                if not hide_notifications:
                    show_notification(t("notif_error"), f"{t('notif_zip_error')}: {str(e)}", color=(220, 60, 60))
                return

        # ===== 4. Неподдерживаемый формат =====
        else:
            if not hide_notifications:
                show_notification(t("notif_error"), t("notif_format_error", ext=ext), color=(220, 60, 60))
            return

    # Запускаем в отдельном потоке
    threading.Thread(target=_worker, daemon=True).start()
CONFIG_FILE = os.path.join(GAME_DIR, "launcher_config.json")
JAVA_DIR = os.path.join(GAME_DIR, "runtime")

os.makedirs(JAVA_DIR, exist_ok=True)

_java_cache = {}
MIRRORS = [
    "https://launchermeta.mojang.com",
    "https://piston-meta.mojang.com",
    "https://bmclapi2.bangbang93.com"
]

BMCLAPI = "https://launchermeta.mojang.com"
for mirror in MIRRORS:
    try:
        test = requests.get(f"{mirror}/mc/game/version_manifest.json",
                            timeout=5,
                            headers={'User-Agent': 'Mozilla/5.0'})
        if test.status_code == 200:
            BMCLAPI = mirror
            print(f"    Рабочее зеркало: {BMCLAPI}")
            break
    except Exception as e:
        print(f"Зеркало {mirror} не отвечает: {e}")
        continue

os.environ["MCL_API_BASEURL"] = BMCLAPI

FABRIC_MIRRORS = [
    "https://bmclapi2.bangbang93.com",
    "https://meta.fabricmc.net",
    "https://meta2.fabricmc.net",
    "https://meta3.fabricmc.net",
]

import minecraft_launcher_lib.fabric
import minecraft_launcher_lib.forge

cancel_requested = False
minecraft_process = None
installer_process = None

LAST_FABRIC_VERSION_FILE = os.path.join(GAME_DIR, "last_fabric_version.txt")
LAST_FORGE_VERSION_FILE = os.path.join(GAME_DIR, "last_forge_version.txt")

MODS_DB = {
    "1.21.11": {
    "fabric-api": "0.141.3+1.21.11",  # ← или любую >= 0.140.0
    "sodium": "mc1.21.11-0.8.7-fabric",
    "iris": "1.10.7+1.21.11-fabric"
    },
    "1.21.10": {
        "fabric-api": "0.134.1+1.21.10",
        "sodium": "mc1.21.10-0.7.3-fabric",
        "iris": "1.9.7+1.21.10-fabric"
    },
    "1.21.9": {
        "fabric-api": "0.134.1+1.21.9",
        "sodium": "mc1.21.10-0.7.3-fabric",
        "iris": "1.9.7+1.21.10-fabric"
    },
    "1.21.8": {
        "fabric-api": "0.136.1+1.21.8",
        "sodium": "mc1.21.8-0.7.3-fabric",
        "iris": "1.9.6+1.21.8-fabric"
    },
    "1.21.6": {
        "fabric-api": "0.128.2+1.21.6",
        "sodium": "mc1.21.8-0.7.3-fabric",
        "iris": "1.9.6+1.21.8-fabric"
    },
    "1.21.5": {
        "fabric-api": "0.134.1+1.21.5",
        "sodium": "mc1.21.5-0.6.13-fabric",
        "iris": "1.8.11+1.21.5-fabric"
    },
    "1.21.4": {
        "fabric-api": "0.119.4+1.21.4",
        "sodium": "mc1.21.4-0.6.13-fabric",
        "iris": "1.8.8+1.21.4-fabric"
    },
    "1.21.3": {
        "fabric-api": "0.134.1+1.21.3",
        "sodium": "mc1.21.3-0.6.13-fabric",
        "iris": "1.8.11+1.21.3-fabric"
    },
    "1.21.2": {
        "fabric-api": "0.134.1+1.21.2",
        "sodium": "mc1.21.2-0.6.13-fabric",
        "iris": "1.8.11+1.21.2-fabric"
    },
    "1.21.1": {
        "fabric-api": "0.134.1+1.21.1",
        "sodium": "mc1.21.1-0.6.13-fabric",
        "iris": "1.8.12+1.21.1-fabric"
    },
    "1.21": {
        "fabric-api": "0.134.1+1.21",
        "sodium": "mc1.21-0.6.13-fabric",
        "iris": "1.8.12+1.21-fabric"
    },
    "1.20.6": {
        "fabric-api": "0.91.1+1.20.6",
        "sodium": "mc1.20.6-0.5.11-fabric",
        "iris": "1.7.2+1.20.6"
    },
    "1.20.5": {
        "fabric-api": "0.134.1+1.20.5",
        "sodium": "mc1.20.5-0.5.11-fabric",
        "iris": "1.8.11+1.20.5-fabric"
    },
    "1.20.4": {
        "fabric-api": "0.134.1+1.20.4",
        "sodium": "mc1.20.4-0.5.8-fabric",
        "iris": "1.8.11+1.20.4-fabric"
    },
    "1.20.3": {
        "fabric-api": "0.134.1+1.20.3",
        "sodium": "mc1.20.3-0.5.8-fabric",
        "iris": "1.8.11+1.20.3-fabric"
    },
    "1.20.2": {
        "fabric-api": "0.134.1+1.20.2",
        "sodium": "mc1.20.2-0.5.5-fabric",
        "iris": "1.8.11+1.20.2-fabric"
    },
    "1.20.1": {
        "fabric-api": "0.134.1+1.20.1",
        "sodium": "mc1.20.1-0.5.13-fabric",
        "iris": "1.8.11+1.20.1-fabric"
    },
    "1.20": {
        "fabric-api": "0.134.1+1.20",
        "sodium": "mc1.20-0.5.11-fabric",
        "iris": "1.8.11+1.20-fabric"
    },
    "1.19.4": {
        "fabric-api": "0.134.1+1.19.4",
        "sodium": "mc1.19.4-0.4.10-fabric",
        "iris": "1.5.2"
    },
    "1.19.3": {
        "fabric-api": "0.76.1+1.19.3",
        "sodium": "mc1.19.3-0.4.9-fabric",
        "iris": "1.5.2"
    },
    "1.19.2": {
        "fabric-api": "0.76.1+1.19.2",
        "sodium": "mc1.19.2-0.4.4-fabric",
        "iris": "1.5.2"
    },
    "1.19.1": {
        "fabric-api": "0.76.1+1.19.1",
        "sodium": "mc1.19.2-0.4.4-fabric",
        "iris": "1.5.2"
    },
    "1.19": {
        "fabric-api": "0.76.1+1.19",
        "sodium": "mc1.19-0.4.2-fabric",
        "iris": "1.5.2"
    },
    "1.18.2": {
        "fabric-api": "0.76.1+1.18.2",
        "sodium": "mc1.18.2-0.4.1-fabric",
        "iris": "1.5.2"
    },
    "1.18.1": {
        "fabric-api": "0.76.1+1.18.1",
        "sodium": "mc1.18.1-0.4.0-alpha6-fabric",
        "iris": "1.5.2"
    },
    "1.18": {
        "fabric-api": "0.76.1+1.18",
        "sodium": "mc1.18-0.4.0-alpha5-fabric",
        "iris": "1.5.2"
    },
    "1.17.1": {
        "fabric-api": "0.76.1+1.17.1",
        "sodium": "mc1.17.1-0.3.4-fabric",
        "iris": "1.5.2"
    },
    "1.17": {
        "fabric-api": "0.76.1+1.17",
        "sodium": "mc1.17.1-0.3.4-fabric",
        "iris": "1.5.2"
    },
    "1.16.5": {
        "fabric-api": "0.76.1+1.16.5",
        "sodium": "mc1.16.5-0.2.0-fabric",
        "iris": "1.5.2"
    }
}

def get_java_major_version(java_path="java"):
    try:
        result = subprocess.run([java_path, "-version"], capture_output=True, text=True, timeout=10, **no_window_kwargs())
        output = result.stderr + result.stdout
        match = re.search(r'version "?(1\.8|1\.8\.0|8|11|17|21|22|23|24|25)_?\d*', output)
        if match:
            ver_str = match.group(1)
            if ver_str.startswith("1.8"):
                return 8
            else:
                return int(ver_str)
        match = re.search(r'version (\d+)', output)
        if match:
            return int(match.group(1))
    except Exception as e:
        winerror = getattr(e, "winerror", None)
        if winerror == 740:
            # 740 = "требуется повышение прав": просто пропускаем этот путь
            print(f"  Java пропущена (нужны права администратора): {java_path}")
        else:
            print(f"Ошибка определения версии Java ({java_path}): {e}")
    return None


# Кеш найденных путей к Java, чтобы не перебирать диск каждый раз
_java_path_cache = set()
java_path_cached = ""  # Глобальная переменная для сохранённого пути


def find_system_java(min_version=8, max_version=17):
    global java_path_cached

    # 0. САМЫЙ ПРИОРИТЕТНЫЙ ПУТЬ — скачанная и сохранённая Java
    if java_path_cached and os.path.exists(java_path_cached):
        ver = get_java_major_version(java_path_cached)
        if ver and min_version <= ver <= max_version:
            print(f"  Использую сохранённую Java: {java_path_cached}")
            return java_path_cached
        else:
            # Если путь существует, но версия не подходит — удаляем из конфига
            java_path_cached = ""
            save_settings()

    # 1. Проверяем кеш быстрых путей
    for cached_path in list(_java_path_cache):
        if os.path.exists(cached_path):
            ver = get_java_major_version(cached_path)
            if ver and min_version <= ver <= max_version:
                return cached_path
        else:
            _java_path_cache.remove(cached_path)

    # 2. Быстрый поиск по заданным путям
    quick_paths = []

    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        java_exe = os.path.join(java_home, "bin", "java.exe" if platform.system() == "Windows" else "java")
        quick_paths.append(java_exe)

    if platform.system() == "Windows":
        quick_paths.extend([
            "C:\\Program Files\\Java\\jdk-17\\bin\\java.exe",
            "C:\\Program Files\\Java\\jdk-11\\bin\\java.exe",
            "C:\\Program Files\\Java\\jdk-8\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jdk-17\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jdk-11\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jdk-8\\bin\\java.exe",
            "C:\\Program Files\\Microsoft\\jdk-17.0.12\\bin\\java.exe",
            "C:\\Program Files\\Microsoft\\jdk-21.0.4\\bin\\java.exe",
        ])
    else:
        quick_paths.extend([
            "/usr/bin/java",
            "/usr/lib/jvm/java-17-openjdk/bin/java",
            "/usr/lib/jvm/java-11-openjdk/bin/java",
            "/usr/lib/jvm/java-8-openjdk/bin/java",
        ])

    for path in quick_paths:
        if os.path.exists(path):
            ver = get_java_major_version(path)
            if ver and min_version <= ver <= max_version:
                _java_path_cache.add(path)
                return path

    # 3. Полный обход диска (только если ничего не найдено)
    print("  Быстрые пути не дали результата, начинаю полный обход диска (это займёт несколько секунд)...")

    possible_roots = [
        os.environ.get("JAVA_HOME", ""),
        "C:\\Program Files\\Java",
        "C:\\Program Files (x86)\\Java",
        "C:\\Program Files\\Microsoft\\jdk-*",
        os.path.expanduser("~")
    ]

    if platform.system() == "Windows":
        import glob
        expanded_roots = []
        for root in possible_roots:
            if "*" in root:
                expanded_roots.extend(glob.glob(root))
            elif root and os.path.exists(root):
                expanded_roots.append(root)
        possible_roots = expanded_roots

    found = None
    for root in possible_roots:
        if not root or not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if "java.exe" in filenames and "bin" in dirpath:
                java_path = os.path.join(dirpath, "java.exe")
                ver = get_java_major_version(java_path)
                if ver and min_version <= ver <= max_version:
                    found = java_path
                    break
        if found:
            break

    if found:
        _java_path_cache.add(found)
        print(f"  Найдена Java в: {found}")
        return found

    print("  Java не найдена даже при полном обходе диска.")
    return None

def download_java(version=8, set_status=None):
    global cancel_requested
    os.makedirs(JAVA_DIR, exist_ok=True)
    system = platform.system().lower()
    arch = platform.machine().lower()
    if "arm" in arch or "aarch64" in arch:
        arch = "aarch64"
    elif "64" in arch:
        arch = "x64"
    else:
        arch = "x86"
    java_folder = os.path.join(JAVA_DIR, f"java{version}")
    java_bin = os.path.join(java_folder, "bin", "java.exe" if system == "windows" else "java")
    if os.path.exists(java_bin):
        print(f"    Java {version} уже скачана в {java_folder}")
        return java_bin

    # Специальная обработка для Java 25 (нужна для Minecraft 26.1+)
    if version == 25:
        return download_microsoft_java(version, set_status)

    if version == 8:
        feature_version = 8
    elif version in [11, 17, 21]:
        feature_version = version
    else:
        feature_version = 17

    os_type = "windows" if system == "windows" else "linux" if system == "linux" else "mac"
    api_url = f"https://api.adoptium.net/v3/assets/latest/{feature_version}/hotspot"
    params = {
        "architecture": arch,
        "image_type": "jre",
        "os": os_type,
        "vendor": "eclipse"
    }
    try:
        if set_status:
            set_status(t("st_java_info", version=version))
        resp = requests.get(api_url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f" Ошибка получения данных Java: {resp.status_code}")
            return None
        data = resp.json()
        if not data:
            print(" Нет доступных сборок Java")
            return None
        binary = data[0]["binary"]
        download_url = binary["package"]["link"]
        print(f"  Скачивание Java {version} с {download_url}")
        temp_archive = os.path.join(JAVA_DIR, f"java{version}_temp.zip")
        if os.path.exists(temp_archive):
            os.remove(temp_archive)
        r = requests.get(download_url, stream=True, timeout=120)
        if r.status_code != 200:
            print(f" Ошибка скачивания Java: {r.status_code}")
            return None
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(temp_archive, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if cancel_requested:
                    f.close()
                    os.remove(temp_archive)
                    return None
                f.write(chunk)
                downloaded += len(chunk)
                if set_status:
                    percent = downloaded / total_size * 100 if total_size else 0
                    set_status(t("st_java_downloading", version=version, percent=percent))
        if set_status:
            set_status(t("st_java_unpacking", version=version))
        with zipfile.ZipFile(temp_archive, 'r') as zip_ref:
            top_level = None
            for name in zip_ref.namelist():
                if '/' in name:
                    top_level = name.split('/')[0]
                    break
            if top_level:
                extract_path = os.path.join(JAVA_DIR, "temp_extract")
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                zip_ref.extractall(extract_path)
                if os.path.exists(java_folder):
                    shutil.rmtree(java_folder)
                shutil.move(os.path.join(extract_path, top_level), java_folder)
                shutil.rmtree(extract_path)
            else:
                zip_ref.extractall(java_folder)
        os.remove(temp_archive)
        print(f"    Java {version} установлена в {java_folder}")
        return java_bin
    except Exception as e:
        print(f" Ошибка при скачивании Java: {e}")
        traceback.print_exc()
        return None

def download_microsoft_java(version=25, set_status=None):
    """Скачивает Microsoft OpenJDK для Java 25 (нужна для Minecraft 26.1+)"""
    global cancel_requested
    system = platform.system().lower()
    arch = platform.machine().lower()

    if "arm" in arch or "aarch64" in arch:
        arch = "aarch64"
    elif "64" in arch:
        arch = "x64"
    else:
        arch = "x86"

    java_folder = os.path.join(JAVA_DIR, f"java{version}")
    java_bin = os.path.join(java_folder, "bin", "java.exe" if system == "windows" else "java")

    if os.path.exists(java_bin):
        print(f"    Java {version} уже скачана в {java_folder}")
        return java_bin

    # URL для Microsoft OpenJDK 25
    if system == "windows":
        if arch == "x64":
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-windows-x64.zip"
        elif arch == "aarch64":
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-windows-aarch64.zip"
        else:
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-windows-x64.zip"
        file_ext = ".zip"
    elif system == "linux":
        if arch == "x64":
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-linux-x64.tar.gz"
        elif arch == "aarch64":
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-linux-aarch64.tar.gz"
        else:
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-linux-x64.tar.gz"
        file_ext = ".tar.gz"
    elif system == "mac":
        if arch == "aarch64":
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-mac-aarch64.tar.gz"
        else:
            download_url = "https://aka.ms/download-jdk/microsoft-jdk-25.0.2-mac-x64.tar.gz"
        file_ext = ".tar.gz"
    else:
        print(f" Неподдерживаемая ОС: {system}")
        return None

    try:
        if set_status:
            set_status(t("st_java_downloading_ms", version=version))

        temp_archive = os.path.join(JAVA_DIR, f"java{version}_temp{file_ext}")
        if os.path.exists(temp_archive):
            os.remove(temp_archive)

        print(f"  Скачивание Java {version} с {download_url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(download_url, stream=True, timeout=180, headers=headers)

        if r.status_code != 200:
            print(f" Ошибка скачивания Java: {r.status_code}")
            return None

        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(temp_archive, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if cancel_requested:
                    f.close()
                    os.remove(temp_archive)
                    return None
                f.write(chunk)
                downloaded += len(chunk)
                if set_status:
                    percent = downloaded / total_size * 100 if total_size else 0
                    set_status(t("st_java_downloading", version=version, percent=percent))

        if set_status:
            set_status(t("st_java_unpacking", version=version))

        # Распаковка в зависимости от типа файла
        if file_ext == '.zip':
            with zipfile.ZipFile(temp_archive, 'r') as zip_ref:
                # Находим корневую папку
                top_level = None
                for name in zip_ref.namelist():
                    if '/' in name:
                        top_level = name.split('/')[0]
                        break

                extract_path = os.path.join(JAVA_DIR, "temp_extract")
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                zip_ref.extractall(extract_path)

                if top_level:
                    source_dir = os.path.join(extract_path, top_level)
                    if os.path.exists(java_folder):
                        shutil.rmtree(java_folder)
                    shutil.move(source_dir, java_folder)
                    shutil.rmtree(extract_path)
                else:
                    if os.path.exists(java_folder):
                        shutil.rmtree(java_folder)
                    shutil.move(extract_path, java_folder)
        else:
            # .tar.gz
            import tarfile
            with tarfile.open(temp_archive, 'r:gz') as tar:
                # Находим корневую папку
                top_level = None
                for member in tar.getmembers():
                    if '/' in member.name:
                        top_level = member.name.split('/')[0]
                        break

                extract_path = os.path.join(JAVA_DIR, "temp_extract")
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                tar.extractall(extract_path)

                if top_level:
                    source_dir = os.path.join(extract_path, top_level)
                    if os.path.exists(java_folder):
                        shutil.rmtree(java_folder)
                    shutil.move(source_dir, java_folder)
                    shutil.rmtree(extract_path)
                else:
                    if os.path.exists(java_folder):
                        shutil.rmtree(java_folder)
                    shutil.move(extract_path, java_folder)

        # Очистка
        if os.path.exists(temp_archive):
            os.remove(temp_archive)

        # Проверяем, что java бинарник существует
        if os.path.exists(java_bin):
            print(f"    Java {version} установлена в {java_folder}")
            return java_bin
        else:
            print(f" Не найден java бинарник после распаковки: {java_bin}")
            return None

    except Exception as e:
        print(f" Ошибка при скачивании Microsoft Java: {e}")
        traceback.print_exc()
        return None


def get_java_executable(minecraft_version, set_status=None):
    global java_path_cached

    if minecraft_version in _java_cache:
        cached = _java_cache[minecraft_version]
        if os.path.exists(cached) or cached == "java":
            if set_status:
                set_status(t("st_java_from_cache"))
            return cached

    # Определяем версию
    try:
        if minecraft_version.startswith('1.'):
            parts = minecraft_version.split('.')
            if len(parts) >= 2:
                minor = int(parts[1])
                if minor < 17:
                    required_java = 8
                elif minor < 21:
                    required_java = 17
                else:
                    required_java = 21
            else:
                required_java = 17
        else:
            try:
                major_version = int(minecraft_version.split('.')[0])
                if major_version >= 26:
                    required_java = 25
                elif major_version >= 24:
                    required_java = 21
                else:
                    required_java = 21
            except:
                required_java = 25
    except:
        required_java = 8

    print(f"  Для Minecraft {minecraft_version} требуется Java {required_java}")

    # Проверяем локальную Java
    local_java = os.path.join(JAVA_DIR, f"java{required_java}", "bin",
                              "java.exe" if platform.system() == "Windows" else "java")
    if os.path.exists(local_java):
        print(f"    Найдена локальная Java {required_java}")
        _java_cache[minecraft_version] = local_java
        return local_java

    # Ищем на диске (с кэшем)
    sys_java = find_system_java_cached(min_version=required_java, max_version=required_java)
    if sys_java:
        print(f"    Найдена системная Java {required_java}")
        _java_cache[minecraft_version] = sys_java
        return sys_java

    # НЕ НАЙДЕНО - СКАЧИВАЕМ
    print(f" Java {required_java} не найдена, скачивание...")
    if set_status:
        set_status(t("st_java_downloading_required", version=required_java))
    downloaded = download_java(required_java, set_status)
    if downloaded:
        _java_cache[minecraft_version] = downloaded
        java_path_cached = downloaded
        save_settings()
        return downloaded

    print(" Не удалось скачать Java")
    return "java"
def clear_mods_folder():
    mods_dir = os.path.join(GAME_DIR, "mods")
    if not os.path.exists(mods_dir):
        return
    for file in os.listdir(mods_dir):
        if file.endswith(".jar"):
            file_path = os.path.join(mods_dir, file)
            for attempt in range(3):
                try:
                    os.remove(file_path)
                    print(f"  Удалён мод: {file}")
                    break
                except Exception as e:
                    if attempt == 2:
                        print(f" Не удалось удалить {file}: {e}")
                    else:
                        time.sleep(0.5)

def get_last_fabric_version():
    if os.path.exists(LAST_FABRIC_VERSION_FILE):
        with open(LAST_FABRIC_VERSION_FILE, 'r') as f:
            return f.read().strip()
    return None

def set_last_fabric_version(version):
    with open(LAST_FABRIC_VERSION_FILE, 'w') as f:
        f.write(version)

def get_last_forge_version():
    if os.path.exists(LAST_FORGE_VERSION_FILE):
        with open(LAST_FORGE_VERSION_FILE, 'r') as f:
            return f.read().strip()
    return None

def set_last_forge_version(version):
    with open(LAST_FORGE_VERSION_FILE, 'w') as f:
        f.write(version)

def download_mod(mod_name: str, minecraft_version: str, game_dir: str, set_status) -> bool:
    """
    Скачивает мод с Modrinth.
    Приоритет:
      1. Точная версия из статической базы MODS_DB.
      2. Fallback на прямые ссылки для известных версий.
      3. Динамический поиск с пагинацией.
    """
    try:
        mod_ids = {
            "sodium": "AANobbMI",
            "iris": "YL57xq9U",
            "fabric-api": "P7dR8mSH"
        }

        if mod_name not in mod_ids:
            print(f" Неизвестный мод: {mod_name}")
            return False

        mod_id = mod_ids[mod_name]
        mods_dir = os.path.join(game_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)

        # ===== 1. Пытаемся взять версию из статической базы =====
        target_version = None
        if minecraft_version in MODS_DB and mod_name in MODS_DB[minecraft_version]:
            target_version = MODS_DB[minecraft_version][mod_name]
            print(f"  Статическая база: для {mod_name} указана версия {target_version}")

        # Функция для получения всех версий (пагинация)
        def fetch_all_versions():
            all_versions = []
            offset = 0
            limit = 100
            attempt = 0
            while True:
                params = {
                    "loaders": json.dumps(["fabric"]),
                    "limit": limit,
                    "offset": offset
                }
                try:
                    resp = requests.get(f"https://api.modrinth.com/v2/project/{mod_id}/version",
                                        params=params, timeout=15)
                    if resp.status_code != 200:
                        print(f"  Ошибка {resp.status_code} при offset={offset}")
                        break
                    data = resp.json()
                    if not data:
                        break
                    all_versions.extend(data)
                    if len(data) < limit:
                        break
                    offset += limit
                except Exception as e:
                    print(f"  Ошибка при запросе: {e}")
                    break
            return all_versions

        # Функция для проверки, подходит ли файл (сначала loaders, потом имя)
        def is_fabric_file(file):
            if "loaders" in file and "fabric" in file["loaders"]:
                return True
            if "fabric" in file["filename"].lower():
                return True
            return False

        # Функция для выбора лучшего файла из версии
        def select_best_file(version):
            for f in version["files"]:
                if "loaders" in f and "fabric" in f["loaders"]:
                    return f
            for f in version["files"]:
                if "fabric" in f["filename"].lower():
                    return f
            return version["files"][0]

        # ==== Попытка скачать по статической базе ====
        if target_version:
            all_versions = fetch_all_versions()
            exact_version = None
            for v in all_versions:
                if v.get("version_number") == target_version:
                    exact_version = v
                    break
            if exact_version:
                best_file = select_best_file(exact_version)
                if best_file:
                    print(f"    Найдена точная версия {target_version} из базы")
                    download_url = best_file["url"]
                    filename = best_file["filename"]
                    mod_path = os.path.join(mods_dir, filename)
                    if os.path.exists(mod_path):
                        print(f"    {mod_name} уже установлен (версия {filename})")
                        return True
                    set_status(t("st_mod_downloading", mod=mod_name))
                    print(f"  Скачивание {mod_name} (версия {filename}): {download_url}")
                    r = requests.get(download_url, stream=True, timeout=60)
                    if r.status_code == 200:
                        with open(mod_path, 'wb') as f:
                            for chunk in r.iter_content(8192):
                                if cancel_requested:
                                    f.close()
                                    os.remove(mod_path)
                                    return False
                                f.write(chunk)
                        print(f"    {mod_name} сохранён: {mod_path}")
                        return True
                    else:
                        print(f" Ошибка скачивания, код {r.status_code}")
                else:
                    print(f" Точная версия {target_version} не имеет подходящего файла")
            else:
                print(f" Точная версия {target_version} не найдена в API")

        # ===== 2. Fallback на прямые ссылки для известных версий =====
        fallback_sodium = {
            "1.21.4": "https://cdn.modrinth.com/data/AANobbMI/versions/c3YkZvne/sodium-fabric-0.6.13%2Bmc1.21.4.jar",
            "1.21.5": "https://cdn.modrinth.com/data/AANobbMI/versions/DA250htH/sodium-fabric-0.6.13%2Bmc1.21.5.jar",
            "1.21.6": "https://cdn.modrinth.com/data/AANobbMI/versions/7pwil2dy/sodium-fabric-0.7.3%2Bmc1.21.8.jar",
            "1.21.8": "https://cdn.modrinth.com/data/AANobbMI/versions/7pwil2dy/sodium-fabric-0.7.3%2Bmc1.21.8.jar",
            "1.21.9": "https://cdn.modrinth.com/data/AANobbMI/versions/AQpu5aS1/sodium-fabric-0.7.3%2Bmc1.21.9.jar",
            "1.21.10": "https://cdn.modrinth.com/data/AANobbMI/versions/sFfidWgd/sodium-fabric-0.7.3%2Bmc1.21.10.jar",
            "1.21.11": "https://cdn.modrinth.com/data/AANobbMI/versions/ZPWbiWXz/sodium-fabric-0.8.6%2Bmc1.21.11.jar",
        }

        fallback_iris = {
            "1.21.4": "https://cdn.modrinth.com/data/YL57xq9U/versions/Ca054sTe/iris-fabric-1.8.8%2Bmc1.21.4.jar",
            "1.21.5": "https://cdn.modrinth.com/data/YL57xq9U/versions/U6evbjd0/iris-fabric-1.8.11%2Bmc1.21.5.jar",
            "1.21.6": "https://cdn.modrinth.com/data/YL57xq9U/versions/Rhzf61g1/iris-fabric-1.9.6%2Bmc1.21.8.jar",
            "1.21.8": "https://cdn.modrinth.com/data/YL57xq9U/versions/Rhzf61g1/iris-fabric-1.9.6%2Bmc1.21.8.jar",
            "1.21.9": "https://cdn.modrinth.com/data/YL57xq9U/versions/2fEZLvCV/iris-fabric-1.9.7%2Bmc1.21.9.jar",
            "1.21.10": "https://cdn.modrinth.com/data/YL57xq9U/versions/a98UkgML/iris-fabric-1.9.7%2Bmc1.21.10.jar",
            "1.21.11": "https://cdn.modrinth.com/data/YL57xq9U/versions/TSXvi2yD/iris-fabric-1.10.6%2Bmc1.21.11.jar",
        }

        fallback_fabric_api = {
            # при необходимости можно добавить
        }

        fallback_map = {
            "sodium": fallback_sodium,
            "iris": fallback_iris,
            "fabric-api": fallback_fabric_api
        }

        if mod_name in fallback_map and minecraft_version in fallback_map[mod_name]:
            url = fallback_map[mod_name][minecraft_version]
            filename = os.path.basename(url)
            mod_path = os.path.join(mods_dir, filename)
            if os.path.exists(mod_path):
                print(f"    {mod_name} уже установлен (fallback)")
                return True
            set_status(t("st_mod_downloading_fallback", mod=mod_name))
            try:
                r = get_download_session().get(url, stream=True, timeout=60)
                if r.status_code == 200:
                    with open(mod_path, 'wb') as f:
                        for chunk in r.iter_content(8192):
                            if cancel_requested:
                                f.close()
                                os.remove(mod_path)
                                return False
                            f.write(chunk)
                    print(f"    {mod_name} сохранён (fallback): {mod_path}")
                    return True
                else:
                    print(f" Ошибка скачивания fallback, код {r.status_code}")
            except Exception as e:
                print(f" Ошибка при fallback: {e}")

        # ===== 3. Динамический поиск =====
        print(f"  Динамический поиск для {mod_name}...")
        all_versions = fetch_all_versions()
        if not all_versions:
            print(f" Не удалось получить версии {mod_name}")
            return False

        all_versions.sort(key=lambda v: v.get("date_published", ""), reverse=True)
        compatible = [v for v in all_versions if minecraft_version in v.get("game_versions", [])]
        print(f"  Найдено {len(compatible)} версий, совместимых с Minecraft {minecraft_version}")

        if not compatible:
            print(f" Нет версий {mod_name} для Minecraft {minecraft_version}")
            return False

        selected_version = None
        for v in compatible:
            for f in v["files"]:
                if is_fabric_file(f):
                    selected_version = v
                    break
            if selected_version:
                break
        if not selected_version:
            selected_version = compatible[0]
            print(f" ВНИМАНИЕ: ни одна версия не содержит очевидно Fabric-файл, выбрана {selected_version['version_number']}")

        best_file = select_best_file(selected_version)
        download_url = best_file["url"]
        filename = best_file["filename"]
        mod_path = os.path.join(mods_dir, filename)

        if os.path.exists(mod_path):
            print(f"    {mod_name} уже установлен (версия {filename})")
            return True

        set_status(t("st_mod_downloading", mod=mod_name))
        print(f"  Скачивание {mod_name} (версия {filename}): {download_url}")
        for attempt in range(3):
            try:
                r = requests.get(download_url, stream=True, timeout=60)
                if r.status_code == 200:
                    break
                else:
                    print(f"  Попытка {attempt+1}: код {r.status_code}")
            except Exception as e:
                print(f"Ошибка скачивания: {e}")
                if attempt < 2:
                    time.sleep(2)
                else:
                    return False
        else:
            return False

        with open(mod_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if cancel_requested:
                    f.close()
                    os.remove(mod_path)
                    return False
                f.write(chunk)

        print(f"    {mod_name} сохранён: {mod_path}")
        return True

    except Exception as e:
        print(f" Ошибка скачивания {mod_name}: {e}")
        traceback.print_exc()
        return False

def install_fabric_mods(minecraft_version: str, game_dir: str, set_status) -> bool:
    """
    Устанавливает моды динамически для любой версии Minecraft (1.16.5+)
    Автоматически ищет и скачивает совместимые версии с Modrinth
    """
    # Проверяем, поддерживает ли версия моды (только Fabric 1.16.5+)
    try:
        if minecraft_version.startswith('1.'):
            parts = minecraft_version.split('.')
            minor = int(parts[1])
            if minor < 16:
                set_status(t("st_mods_unsupported", version=minecraft_version))
                print(f"  Пропускаем установку модов для {minecraft_version}")
                return True
            elif minor == 16:
                patch = int(parts[2]) if len(parts) > 2 else 0
                if patch < 5:
                    set_status(t("st_mods_may_not_work", version=minecraft_version))
                    print(f"  Версия {minecraft_version} имеет ограниченную поддержку")
    except:
        pass

    mods_dir = os.path.join(game_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)
    results = {}

    # ID модов на Modrinth
    MODS_INFO = {
        "fabric-api": {"id": "P7dR8mSH", "required": True},
        "sodium": {"id": "AANobbMI", "required": False},
        "iris": {"id": "YL57xq9U", "required": False}
    }

    # Флаг - был ли использован MODS_DB для хотя бы одного мода
    used_static_db = False

    # ===== 1. СНАЧАЛА ПРОБУЕМ ВЗЯТЬ ВЕРСИИ ИЗ СТАТИЧЕСКОЙ БАЗЫ MODS_DB =====
    if minecraft_version in MODS_DB:
        used_static_db = True
        print(f"  Используем статическую базу MODS_DB для версии {minecraft_version}")

        for mod_name, mod_info in MODS_INFO.items():
            mod_id = mod_info["id"]
            required = mod_info["required"]

            if mod_name not in MODS_DB[minecraft_version]:
                if required:
                    set_status(t("st_mod_missing_db_version", mod=mod_name, version=minecraft_version))
                    print(f"  {mod_name} отсутствует в статической базе")
                    return False
                else:
                    print(f"  {mod_name} пропущен (нет в статической базе)")
                    results[mod_name] = False
                    continue

            target_version = MODS_DB[minecraft_version][mod_name]
            print(f"  Статическая база: {mod_name} -> {target_version}")

            # Скачиваем по точной версии через download_mod
            success = download_mod(mod_name, minecraft_version, game_dir, set_status)
            results[mod_name] = success

            if not success and required:
                set_status(t("st_mod_download_failed", mod=mod_name, version=target_version))
                return False
    else:
        print(f"  Версия {minecraft_version} не найдена в MODS_DB, переходим к динамическому поиску")

    # ===== 2. ЕСЛИ ВЕРСИИ НЕТ В MODS_DB — ДИНАМИЧЕСКИЙ ПОИСК =====
    if not used_static_db:
        print(f"  Запускаем динамический поиск модов для {minecraft_version}")

        def fetch_mod_versions(mod_id):
            """Получает все версии мода с Modrinth"""
            all_versions = []
            offset = 0
            limit = 100

            while True:
                try:
                    params = {
                        "loaders": json.dumps(["fabric"]),
                        "limit": limit,
                        "offset": offset
                    }
                    resp = requests.get(f"https://api.modrinth.com/v2/project/{mod_id}/version",
                                        params=params, timeout=15)
                    if resp.status_code != 200:
                        break
                    data = resp.json()
                    if not data:
                        break
                    all_versions.extend(data)
                    if len(data) < limit:
                        break
                    offset += limit
                except Exception as e:
                    print(f"  Ошибка получения версий: {e}")
                    # Modrinth иногда отвечает таймаутом: без повтора мод молча выпадает
                    if not all_versions and attempt < MODRINTH_RETRIES:
                        attempt += 1
                        print(f"  Повтор запроса к Modrinth ({attempt}/{MODRINTH_RETRIES})...")
                        time.sleep(1.5)
                        continue
                    break
            return all_versions

        def is_version_compatible(version, mc_version):
            """Проверяет, совместима ли версия мода с Minecraft"""
            game_versions = version.get("game_versions", [])

            # Прямое совпадение
            if mc_version in game_versions:
                return True

            # Для версий 26.x (1.26.x)
            if mc_version.startswith("26."):
                alt_version = f"1.{mc_version}"
                if alt_version in game_versions:
                    return True

            # Совпадение по мажорной версии (например, все 1.21.x)
            if '.' in mc_version:
                major_minor = '.'.join(mc_version.split('.')[:2])
                for gv in game_versions:
                    if gv.startswith(major_minor):
                        return True

            return False

        def is_fabric_file(file_data):
            """Проверяет, подходит ли файл для Fabric"""
            if "loaders" in file_data and "fabric" in file_data["loaders"]:
                return True
            if "fabric" in file_data["filename"].lower():
                return True
            return False

        def download_mod_dynamic(mod_name, mod_id, mc_version):
            """Скачивает подходящую версию мода динамически"""
            print(f"  Поиск {mod_name} для Minecraft {mc_version}...")

            # Получаем все версии
            all_versions = fetch_mod_versions(mod_id)
            if not all_versions:
                print(f"  Не удалось получить версии {mod_name}")
                return False

            # Сортируем по дате (новые сначала)
            all_versions.sort(key=lambda v: v.get("date_published", ""), reverse=True)

            # Ищем совместимые версии
            compatible = []
            for version in all_versions:
                if is_version_compatible(version, mc_version):
                    compatible.append(version)

            print(f"  Найдено {len(compatible)} совместимых версий")

            if not compatible:
                return False

            # Выбираем стабильную версию (не alpha/beta)
            selected = None
            for version in compatible:
                ver_str = version.get("version_number", "").lower()
                if "alpha" not in ver_str and "beta" not in ver_str:
                    selected = version
                    break

            if not selected:
                selected = compatible[0]
                print(f"  Внимание: выбрана нестабильная версия {selected['version_number']}")
            else:
                print(f"  Выбрана версия {selected['version_number']}")

            # Выбираем подходящий файл
            selected_file = None
            for f in selected["files"]:
                if is_fabric_file(f):
                    selected_file = f
                    break

            if not selected_file:
                selected_file = selected["files"][0]

            download_url = selected_file["url"]
            filename = selected_file["filename"]
            mod_path = os.path.join(mods_dir, filename)

            # Проверяем, не установлен ли уже
            if os.path.exists(mod_path):
                print(f"  {mod_name} уже установлен ({filename})")
                return True

            # Скачиваем
            set_status(t("st_mod_downloading", mod=mod_name))
            print(f"  Скачивание: {filename}")

            for attempt in range(3):
                try:
                    r = requests.get(download_url, stream=True, timeout=60)
                    if r.status_code == 200:
                        with open(mod_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if cancel_requested:
                                    f.close()
                                    if os.path.exists(mod_path):
                                        os.remove(mod_path)
                                    return False
                                f.write(chunk)
                        file_size = os.path.getsize(mod_path)
                        print(f"  {mod_name} сохранён ({file_size} байт)")
                        return True
                    else:
                        print(f"  Попытка {attempt + 1}: код {r.status_code}")
                except Exception as e:
                    print(f"  Попытка {attempt + 1}: ошибка: {e}")
                    if attempt < 2:
                        time.sleep(2)
            return False

        # === УСТАНОВКА МОДОВ ДИНАМИЧЕСКИ ===
        set_status(t("st_mods_search_install"))

        for mod_name, mod_info in MODS_INFO.items():
            mod_id = mod_info["id"]
            required = mod_info["required"]

            success = download_mod_dynamic(mod_name, mod_id, minecraft_version)
            results[mod_name] = success

            if not success and required:
                set_status(t("st_mod_not_installed", mod=mod_name))
                print(f"  {mod_name} обязателен, но не установлен")
                return False

            if success:
                print(f"  {mod_name}  установлен")
            else:
                print(f"  {mod_name}  пропущен")

    # === ПРОВЕРКА СОВМЕСТИМОСТИ SODIUM И IRIS ===
    sodium_ok = results.get("sodium", False)
    iris_ok = results.get("iris", False)

    if not sodium_ok and iris_ok:
        set_status(t("st_removing_iris"))
        for f in os.listdir(mods_dir):
            if f.startswith("iris-"):
                try:
                    os.remove(os.path.join(mods_dir, f))
                    print(f"  Удалён Iris: {f}")
                except:
                    pass
        results["iris"] = False

    # === ИТОГ ===
    installed_mods = [name for name, installed in results.items() if installed]

    if installed_mods:
        set_status(t("st_mods_installed", mods=', '.join(installed_mods)))
        print(f"\n  Установлено модов: {len(installed_mods)}/{len(MODS_INFO)}")
        print(f"  Список: {', '.join(installed_mods)}")
    else:
        set_status(t("st_mods_none"))
        print("  Не установлено ни одного мода")

    return results.get("fabric-api", False)
def fetch_fabric_data(endpoint: str, set_status, is_meta: bool = True):
    global cancel_requested
    for mirror in FABRIC_MIRRORS:
        if cancel_requested:
            return None
        base = mirror.rstrip('/')
        urls_to_try = [
            f"{base}/{endpoint}",
            f"{base}/fabric-meta/{endpoint}"
        ]
        for url in urls_to_try:
            if cancel_requested:
                return None
            try:
                print(f"  Попытка: {url}")
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    if is_meta:
                        data = resp.json()
                        if data:
                            print(f"    Данные получены с {url}")
                            return data
                    else:
                        return url
                else:
                    print(f"  Зеркало {mirror} вернуло код {resp.status_code} для {url}")
            except Exception as e:
                print(f"  Зеркало {mirror} ошибка для {url}: {e}")
                continue
    return None

def update_notification_title(new_title):
    """Обновляет заголовок текущего уведомления с прогрессом"""
    for notif in notification_queue:
        if notif.progress is not None:  # Находим уведомление с прогрессом
            notif.title = new_title
            return True
    return False
def install_fabric_custom(minecraft_version: str, game_dir: str, set_status) -> bool:
    global cancel_requested, installer_process

    # ===== ПРОВЕРЯЕМ, УСТАНОВЛЕН ЛИ УЖЕ FABRIC =====
    versions_dir = os.path.join(game_dir, "versions")
    for folder in os.listdir(versions_dir):
        if folder.startswith("fabric-loader-") and folder.endswith(f"-{minecraft_version}"):
            print(f"  Fabric Loader уже установлен: {folder}")
            set_status(t("st_fabric_already"))
            return True

    # ===== НАЧАЛО УСТАНОВКИ - ОДНО УВЕДОМЛЕНИЕ =====
    fabric_uid = show_progress(
        text=t("notif_installing_fabric", version=minecraft_version),
        title="Поиск Java...",
        progress=5
    )

    # ===== СНАЧАЛА НАХОДИМ ИЛИ СКАЧИВАЕМ JAVA =====
    set_status(t("st_java_searching"))
    java_path = get_java_executable(minecraft_version, set_status)

    if not java_path:
        set_status(t("st_java_not_found"))
        print("  Не удалось найти Java для установки Fabric")
        complete_progress(
            fabric_uid,
            t("notif_java_error"),
            success=False
        )
        return False

    print(f"  Используется Java: {java_path}")
    update_notification_title("Java найдена")  # <-- МЕНЯЕМ ЗАГОЛОВОК
    update_progress(
        fabric_uid,
        t("notif_installing_fabric", version=minecraft_version),
        20
    )

    try:
        if cancel_requested:
            set_status(t("st_install_cancelled"))
            complete_progress(
                fabric_uid,
                t("notif_canceled"),
                success=False
            )
            return False

        update_notification_title("Проверка Vanilla...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
        update_progress(
            fabric_uid,
            t("notif_installing_fabric", version=minecraft_version),
            30
        )

        set_status(t("st_vanilla_checking"))
        vanilla_installed = os.path.exists(os.path.join(versions_dir, minecraft_version))
        if not vanilla_installed:
            set_status(t("st_vanilla_installing", version=minecraft_version))
            update_notification_title(f"Установка Vanilla {minecraft_version}...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
            update_progress(
                fabric_uid,
                t("notif_installing_fabric", version=minecraft_version),
                35
            )
            try:
                minecraft_launcher_lib.install.install_minecraft_version(minecraft_version, game_dir,
                                                                         callback={"setStatus": _translated_install_status})
            except Exception as e:
                print(f"  Ошибка установки Vanilla: {e}")
                set_status(t("st_vanilla_install_error", error=str(e)[:30]))
                complete_progress(
                    fabric_uid,
                    t("notif_vanilla_error"),
                    success=False
                )
                return False
            if cancel_requested:
                set_status(t("st_install_cancelled"))
                complete_progress(
                    fabric_uid,
                    t("notif_canceled"),
                    success=False
                )
                return False

        update_notification_title("Получение Fabric Loader...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
        update_progress(
            fabric_uid,
            t("notif_installing_fabric", version=minecraft_version),
            50
        )

        set_status(t("st_fabric_loader_versions"))
        loader_data = fetch_fabric_data("v2/versions/loader", set_status, is_meta=True)
        if not loader_data:
            set_status(t("st_fabric_loader_failed"))
            complete_progress(
                fabric_uid,
                t("notif_loader_error"),
                success=False
            )
            return False

        latest_loader = None
        for loader in loader_data:
            if "gameVersion" in loader and str(loader["gameVersion"]) == minecraft_version:
                latest_loader = loader["version"]
                break
        if not latest_loader:
            latest_loader = loader_data[0]["version"]

        set_status(t("st_fabric_loader_version", version=latest_loader))
        print(f"    Loader версия: {latest_loader}")

        update_notification_title("Получение установщика...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
        update_progress(
            fabric_uid,
            t("notif_installing_fabric", version=minecraft_version),
            60
        )

        set_status(t("st_installer_version_fetch"))
        installer_data = fetch_fabric_data("v2/versions/installer", set_status, is_meta=True)
        if not installer_data:
            set_status(t("st_installer_version_failed"))
            complete_progress(
                fabric_uid,
                t("notif_installer_error"),
                success=False
            )
            return False
        installer_version = installer_data[0]["version"]
        set_status(t("st_installer_version", version=installer_version))
        print(f"    Установщик версии: {installer_version}")

        update_notification_title("Скачивание установщика...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
        update_progress(
            fabric_uid,
            t("notif_installing_fabric", version=minecraft_version),
            70
        )

        set_status(t("st_installer_downloading"))
        installer_path = os.path.join(game_dir, f"fabric-installer-{installer_version}.jar")
        downloaded = False
        if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1000000:
            print(f"    Установщик уже существует: {installer_path}")
            downloaded = True

        if not downloaded:
            download_sources = [
                f"https://maven.fabricmc.net/net/fabricmc/fabric-installer/{installer_version}/fabric-installer-{installer_version}.jar",
                f"https://bmclapi2.bangbang93.com/maven/net/fabricmc/fabric-installer/{installer_version}/fabric-installer-{installer_version}.jar",
                f"https://github.com/FabricMC/fabric-installer/releases/download/{installer_version}/fabric-installer-{installer_version}.jar"
            ]
            for source_url in download_sources:
                if cancel_requested:
                    set_status(t("st_install_cancelled"))
                    complete_progress(
                        fabric_uid,
                        t("notif_canceled"),
                        success=False
                    )
                    return False
                print(f"  Попытка скачивания с {source_url}")
                for attempt in range(3):
                    if cancel_requested:
                        set_status(t("st_install_cancelled"))
                        complete_progress(
                            fabric_uid,
                            t("notif_canceled"),
                            success=False
                        )
                        return False
                    try:
                        r = requests.get(source_url, stream=True, timeout=30)
                        if r.status_code == 200:
                            with open(installer_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if cancel_requested:
                                        f.close()
                                        if os.path.exists(installer_path):
                                            os.remove(installer_path)
                                        set_status(t("st_install_cancelled"))
                                        complete_progress(
                                            fabric_uid,
                                            t("notif_canceled"),
                                            success=False
                                        )
                                        return False
                                    f.write(chunk)
                            print(f"    Установщик скачан с {source_url} (попытка {attempt + 1})")
                            downloaded = True
                            break
                        else:
                            print(f"  Попытка {attempt + 1}: код {r.status_code}")
                    except Exception as e:
                        print(f"  Попытка {attempt + 1}: ошибка: {e}")
                        time.sleep(2)
                if downloaded:
                    break

        if not downloaded:
            set_status(t("st_installer_download_failed"))
            complete_progress(
                fabric_uid,
                t("notif_download_error"),
                success=False
            )
            return False

        if cancel_requested:
            if os.path.exists(installer_path):
                os.remove(installer_path)
            set_status(t("st_install_cancelled"))
            complete_progress(
                fabric_uid,
                t("notif_canceled"),
                success=False
            )
            return False

        update_notification_title("Запуск установщика Fabric...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
        update_progress(
            fabric_uid,
            t("notif_installing_fabric", version=minecraft_version),
            85
        )

        set_status(t("st_fabric_installer_running"))

        if java_path == "java":
            command = [
                "java", "-jar", installer_path,
                "client",
                "-dir", game_dir,
                "-mcversion", minecraft_version,
                "-loader", latest_loader,
                "-noprofile", "-snapshot"
            ]
        else:
            command = [
                java_path, "-jar", installer_path,
                "client",
                "-dir", game_dir,
                "-mcversion", minecraft_version,
                "-loader", latest_loader,
                "-noprofile", "-snapshot"
            ]

        print(f"  Запуск команды: {' '.join(command)}")

        use_shell = (java_path == "java" and platform.system() == "Windows")
        installer_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=use_shell,
            **no_window_kwargs()
        )

        # Читаем вывод установщика: иначе он заполняет pipe и зависает навсегда
        installer_output = []

        def _read_stream(pipe):
            try:
                for raw in pipe:
                    line = raw.rstrip()
                    if line:
                        installer_output.append(line)
                        print(f"    [fabric installer] {line}")
            except Exception:
                pass

        threading.Thread(target=_read_stream, args=(installer_process.stdout,), daemon=True).start()
        threading.Thread(target=_read_stream, args=(installer_process.stderr,), daemon=True).start()
        install_started = time.time()

        while installer_process.poll() is None:
            if cancel_requested:
                installer_process.terminate()
                installer_process.wait()
                if os.path.exists(installer_path):
                    os.remove(installer_path)
                set_status(t("st_install_cancelled"))
                installer_process = None
                complete_progress(
                    fabric_uid,
                    t("notif_canceled"),
                    success=False
                )
                return False
            if time.time() - install_started > INSTALLER_TIMEOUT:
                print(f"  Установщик не ответил за {INSTALLER_TIMEOUT} сек — прерываю и чищу")
                try:
                    installer_process.terminate()
                    installer_process.wait(timeout=10)
                except Exception:
                    try:
                        installer_process.kill()
                    except Exception:
                        pass
                installer_process = None
                if os.path.exists(installer_path):
                    os.remove(installer_path)
                set_status(t("st_installer_start_error"))
                complete_progress(fabric_uid, t("notif_download_error"), success=False)
                return False
            time.sleep(0.1)

        stdout, stderr = installer_process.communicate()
        returncode = installer_process.returncode
        installer_process = None

        if cancel_requested:
            if os.path.exists(installer_path):
                os.remove(installer_path)
            set_status(t("st_install_cancelled"))
            complete_progress(
                fabric_uid,
                t("notif_canceled"),
                success=False
            )
            return False

        if returncode != 0:
            print(f" Ошибка при запуске установщика (код {returncode})")
            print("STDERR:", stderr)
            print("STDOUT:", stdout)
            set_status(t("st_installer_start_error"))
            complete_progress(
                fabric_uid,
                t("notif_run_error"),
                success=False
            )
            return False
        else:
            print("    Установщик выполнен успешно")

        if cancel_requested:
            set_status(t("st_install_cancelled"))
            complete_progress(
                fabric_uid,
                t("notif_canceled"),
                success=False
            )
            return False

        update_notification_title("Проверка установки...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
        update_progress(
            fabric_uid,
            t("notif_installing_fabric", version=minecraft_version),
            95
        )

        # Ищем созданную версию Fabric
        fabric_version_id = None
        for folder in os.listdir(versions_dir):
            if folder.startswith("fabric-loader-") and folder.endswith(f"-{minecraft_version}"):
                fabric_version_id = folder
                break

        if not fabric_version_id:
            print(f" Не удалось найти Fabric версию после установки!")
            set_status(t("st_fabric_version_not_found"))
            complete_progress(
                fabric_uid,
                t("notif_not_found_error"),
                success=False
            )
            return False

        # Копируем jar если нужно
        fabric_version_dir = os.path.join(game_dir, "versions", fabric_version_id)
        fabric_jar_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.jar")
        fabric_json_path = os.path.join(fabric_version_dir, f"{fabric_version_id}.json")
        vanilla_jar_path = os.path.join(game_dir, "versions", minecraft_version, f"{minecraft_version}.jar")

        if not os.path.exists(fabric_jar_path):
            if os.path.exists(vanilla_jar_path):
                update_notification_title("Копирование jar файла...")  # <-- МЕНЯЕМ ЗАГОЛОВОК
                update_progress(
                    fabric_uid,
                    t("notif_installing_fabric", version=minecraft_version),
                    98
                )
                print(f" Fabric jar не найден, копируем vanilla jar в {fabric_jar_path}")
                shutil.copy2(vanilla_jar_path, fabric_jar_path)
            else:
                print(f" Vanilla jar тоже не найден: {vanilla_jar_path}")
                set_status(t("st_vanilla_jar_missing"))
                complete_progress(
                    fabric_uid,
                    t("notif_jar_error"),
                    success=False
                )
                return False

        if not os.path.exists(fabric_json_path):
            print(" JSON файл Fabric не найден!")
            set_status(t("st_fabric_json_missing"))
            complete_progress(
                fabric_uid,
                t("notif_json_error"),
                success=False
            )
            return False

        try:
            if os.path.exists(installer_path):
                os.remove(installer_path)
                print("  Установщик удалён")
        except Exception as e:
            print(f" Не удалось удалить установщик: {e}")

        set_status(t("st_fabric_installed"))

        # ✅ ВСЕ УСПЕШНО!
        complete_progress(
            fabric_uid,
            t("notif_fabric_success", version=minecraft_version),
            success=True
        )
        return True

    except Exception as e:
        print(f" Критическая ошибка в install_fabric_custom: {e}")
        traceback.print_exc()
        set_status(t("st_error", error=str(e)[:30]))
        complete_progress(
            fabric_uid,
            t("notif_critical_error"),
            success=False
        )
        return False
def get_forge_versions_from_bmclapi(mc_version):
    """Получает список версий Forge с BMCLAPI"""
    try:
        url = f"https://bmclapi2.bangbang93.com/forge/minecraft/{mc_version}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                return [item.get('version', '') for item in data if item.get('version')]
    except Exception as e:
        print(f"Ошибка get_forge_versions_from_bmclapi: {e}")
    return []

def get_forge_versions_from_maven(mc_version):
    """Получает список версий Forge с Maven"""
    try:
        url = f"https://bmclapi2.bangbang93.com/maven/net/minecraftforge/forge/maven-metadata.xml"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            versions = []
            for v in root.findall(".//version"):
                v_text = v.text
                if v_text and v_text.startswith(mc_version):
                    versions.append(v_text.replace(f"{mc_version}-", ""))
            return sorted(versions, reverse=True)
    except Exception as e:
        print(f"Ошибка get_forge_versions_from_maven: {e}")
    return []

def get_forge_versions(mc_version):
    """Получает список версий Forge для указанной версии Minecraft"""
    versions = get_forge_versions_from_bmclapi(mc_version)
    if versions:
        return versions
    versions = get_forge_versions_from_maven(mc_version)
    if versions:
        return versions
    # Fallback - статическая база
    forge_db = {
        "1.21.11": ["61.0.2", "61.0.1"],
        "1.21.10": ["60.1.0", "60.0.1"],
        "1.21.9": ["59.0.5", "59.0.4"],
        "1.21.8": ["58.1.0", "58.0.1"],
        "1.21.7": ["57.0.3", "57.0.2"],
        "1.21.6": ["56.0.9", "56.0.8"],
        "1.21.5": ["55.0.23", "55.0.22"],
        "1.21.4": ["54.1.0", "54.0.1"],
        "1.21.3": ["53.0.25", "53.0.24"],
        "1.21.2": ["53.0.20", "53.0.19"],
        "1.21.1": ["52.1.8", "52.0.16", "52.0.14"],
        "1.21": ["52.0.16", "52.0.14"],
        "1.20.6": ["50.1.14", "50.1.12"],
        "1.20.5": ["50.0.32", "50.0.31"],
        "1.20.4": ["49.1.0", "49.0.51"],
        "1.20.3": ["49.0.49"],
        "1.20.2": ["48.1.0", "48.0.33"],
        "1.20.1": ["47.3.11", "47.3.0", "47.2.30"],
        "1.20": ["46.0.14", "46.0.13"],
        "1.19.4": ["45.3.0", "45.2.21"],
        "1.19.3": ["44.1.23", "44.1.22"],
        "1.19.2": ["43.4.0", "43.3.8"],
        "1.19.1": ["42.0.9"],
        "1.19": ["41.1.0", "41.0.110"],
        "1.18.2": ["40.2.21", "40.2.14"],
        "1.18.1": ["39.1.2"],
        "1.18": ["38.0.17"],
        "1.17.1": ["37.1.1", "37.1.0"],
        "1.17": ["36.2.39"],
        "1.16.5": ["36.2.39", "36.2.34", "36.2.23"],
        "1.16.4": ["35.1.37"],
        "1.16.3": ["34.1.42"],
        "1.16.2": ["33.0.61"],
        "1.16.1": ["32.0.108"],
        "1.16": ["32.0.108"],
        "1.15.2": ["31.2.57"],
        "1.15.1": ["30.0.51"],
        "1.15": ["29.0.4"],
        "1.14.4": ["28.2.26"],
        "1.14.3": ["27.0.60"],
        "1.14.2": ["26.0.63"],
        "1.14.1": ["25.0.22"],
        "1.14": ["24.0.43"],
        "1.13.2": ["25.0.219"],
        "1.13.1": ["24.0.210"],
        "1.13": ["23.0.212"],
        "1.12.2": ["14.23.5.2860"],
        "1.12.1": ["14.22.1.2485"],
        "1.12": ["14.21.1.2443"],
        "1.11.2": ["13.20.1.2425"],
        "1.11": ["13.19.1.2199"],
        "1.10.2": ["12.18.3.2511"],
        "1.10": ["12.18.1.2082"],
        "1.9.4": ["12.17.0.2317"],
        "1.9": ["12.16.1.1887"],
        "1.8.9": ["11.15.1.2318"],
        "1.8.8": ["11.15.0.1655"],
        "1.8": ["11.14.4.1577"],
        "1.7.10": ["10.13.4.1614"]
    }
    return forge_db.get(mc_version, [])
# PATCH: dedup_forge
def download_forge_installer(mc_version, forge_version, dest_path, set_status):
    global cancel_requested
    forge_mirrors = [
        f"https://bmclapi2.bangbang93.com/maven/net/minecraftforge/forge/{mc_version}-{forge_version}/forge-{mc_version}-{forge_version}-installer.jar",
        f"https://maven.minecraftforge.net/net/minecraftforge/forge/{mc_version}-{forge_version}/forge-{mc_version}-{forge_version}-installer.jar",
        f"https://files.minecraftforge.net/maven/net/minecraftforge/forge/{mc_version}-{forge_version}/forge-{mc_version}-{forge_version}-installer.jar",
        f"https://github.com/MinecraftForge/MinecraftForge/raw/maven/net/minecraftforge/forge/{mc_version}-{forge_version}/forge-{mc_version}-{forge_version}-installer.jar"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Java/1.8.0'}

    for i, url in enumerate(forge_mirrors):
        if cancel_requested:
            set_status(t("st_download_cancelled"))
            return False
        set_status(t("st_forge_downloading_mirror", version=f"{mc_version}-{forge_version}", mirror=i + 1))
        print(f"Попытка зеркала {i+1}: {url}")
        if "com/maven" not in url:
            url = url.replace("commaven", "com/maven")

        try:
            session = get_session(url)
            r = session.get(url, headers=headers, stream=True, timeout=60)
            if r.status_code == 200:
                with open(dest_path, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if cancel_requested:
                            f.close()
                            os.remove(dest_path)
                            set_status(t("st_download_cancelled"))
                            return False
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            set_status(t("st_download_mb", mb=downloaded // 1024 // 1024))
                size = os.path.getsize(dest_path)
                if size > 2000000:
                    set_status(t("st_downloaded_from_mirror", mirror=i + 1))
                    print(f"    Forge установщик загружен с зеркала {i + 1}, размер {size} байт")
                    return True
                else:
                    print(f" Файл слишком мал ({size} байт) с зеркала {i+1}")
                    set_status(t("st_file_too_small", size=size))
            else:
                print(f"  Зеркало {i + 1}: код {r.status_code}")
        except Exception as e:
            print(f"  Зеркало {i + 1}: ошибка - {str(e)[:100]}")
            continue

    set_status(t("st_forge_mirrors_failed"))
    print(" Все зеркала Forge не сработали")
    return False


def ensure_launcher_profiles(game_dir):
    """Установщик Forge требует launcher_profiles.json в игровом каталоге,
    иначе падает с ошибкой "There is no Minecraft launcher profile" (код 1)."""
    path = os.path.join(game_dir, "launcher_profiles.json")
    if os.path.exists(path):
        return True
    try:
        data = {
            "authenticationDatabase": {},
            "clientToken": "",
            "launcherVersion": {"format": 21, "name": "2.1.1", "profilesFormat": 2},
            "profiles": {},
            "selectedUser": "",
            "settings": {"enableAdvanced": False, "enableSnapshots": False},
            "version": 3
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("  Создан launcher_profiles.json (нужен установщику Forge)")
        return True
    except Exception as e:
        print(f"  Не удалось создать launcher_profiles.json: {e}")
        return False


def install_forge(mc_version, game_dir, set_status):
    global cancel_requested, installer_process

    # ===== НАЧАЛО УСТАНОВКИ =====
    # Сохраняем UID уведомления о прогрессе
    forge_uid = show_progress(
        text=t("notif_installing_forge", version=mc_version),
        title=t("notif_java_check"),
        progress=5
    )

    # ===== СНАЧАЛА НАХОДИМ ИЛИ СКАЧИВАЕМ JAVA =====
    set_status(t("st_java_searching_forge"))
    java_path = get_java_executable(mc_version, set_status)

    # Проверяем, что Java найдена
    if not java_path or not os.path.exists(java_path):
        set_status(t("st_java_not_found_forge"))
        print("  Не удалось найти Java для установки Forge")
        complete_progress(
            forge_uid,
            t("notif_java_error"),
            success=False
        )
        return False

    print(f"  Используется Java для Forge: {java_path}")

    update_progress(
        forge_uid,
        t("notif_java_ready"),
        20
    )

    # Проверяем, что Java работает
    try:
        result = subprocess.run([java_path, "-version"], capture_output=True, text=True, timeout=10, **no_window_kwargs())
        if result.returncode != 0:
            set_status(t("st_java_broken"))
            complete_progress(
                forge_uid,
                t("notif_java_error"),
                success=False
            )
            return False
        print(f"  Java OK: {result.stderr.splitlines()[0] if result.stderr else 'Java работает'}")
    except Exception as e:
        print(f"  Ошибка проверки Java: {e}")
        set_status(t("st_java_check_error"))
        complete_progress(
            forge_uid,
            t("notif_java_error"),
            success=False
        )
        return False

    # Обновляем прогресс - поиск Forge
    update_progress(
        forge_uid,
        t("notif_forge_search"),
        35
    )

    # Получаем список версий Forge
    forge_versions = get_forge_versions(mc_version)
    if not forge_versions:
        set_status(t("st_forge_unavailable", version=mc_version))
        print(f" Forge нет для {mc_version}")
        complete_progress(
            forge_uid,
            t("notif_forge_not_found", version=mc_version),
            success=False
        )
        return False

    forge_version = forge_versions[0]
    set_status(t("st_forge_found", version=forge_version))
    print(f"    Найден Forge {forge_version}")

    update_progress(
        forge_uid,
        "Скачивание установщика Forge...",
        50
    )

    installer_path = os.path.join(game_dir, f"forge_installer_{mc_version}.jar")
    if os.path.exists(installer_path) and os.path.getsize(installer_path) < 1000000:
        os.remove(installer_path)

    if not os.path.exists(installer_path):
        if not download_forge_installer(mc_version, forge_version, installer_path, set_status):
            complete_progress(
                forge_uid,
                t("notif_download_error"),
                success=False
            )
            return False

    if cancel_requested:
        if os.path.exists(installer_path):
            os.remove(installer_path)
        set_status(t("st_install_cancelled"))
        complete_progress(
            forge_uid,
            t("notif_canceled"),
            success=False
        )
        return False

    update_progress(
        forge_uid,
        "Запуск установщика Forge...",
        75
    )

    set_status(t("st_forge_installing"))
    os.environ["FORGE_MAVEN_URL"] = "https://bmclapi2.bangbang93.com"

    try:
        # ИСПРАВЛЕНО: используем java_path вместо "java"
        print(f"  Запуск установщика Forge: {java_path} -jar {installer_path} --installClient {game_dir}")
        ensure_launcher_profiles(game_dir)

        # Вывод установщика раньше уходил в окно консоли (и терялся после его отключения)
        installer_output = []

        def _read_installer_output(pipe):
            try:
                for raw in pipe:
                    line = raw.rstrip()
                    if line:
                        installer_output.append(line)
                        print(f"    [forge installer] {line}")
            except Exception:
                pass

        installer_process = subprocess.Popen(
            [java_path, "-jar", installer_path, "--installClient", game_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            **no_window_kwargs()
        )
        threading.Thread(target=_read_installer_output, args=(installer_process.stdout,), daemon=True).start()
        install_started = time.time()

        while installer_process.poll() is None:
            if cancel_requested:
                installer_process.terminate()
                installer_process.wait()
                if os.path.exists(installer_path):
                    os.remove(installer_path)
                set_status(t("st_install_cancelled"))
                installer_process = None
                complete_progress(
                    forge_uid,
                    t("notif_canceled"),
                    success=False
                )
                return False
            if time.time() - install_started > INSTALLER_TIMEOUT:
                print(f"  Установщик не ответил за {INSTALLER_TIMEOUT} сек — прерываю и чищу")
                try:
                    installer_process.terminate()
                    installer_process.wait(timeout=10)
                except Exception:
                    try:
                        installer_process.kill()
                    except Exception:
                        pass
                installer_process = None
                if os.path.exists(installer_path):
                    os.remove(installer_path)
                set_status(t("st_installer_start_error"))
                complete_progress(forge_uid, t("notif_download_error"), success=False)
                return False
            time.sleep(0.1)

        returncode = installer_process.returncode
        installer_process = None

        if returncode != 0:
            tail = " | ".join(installer_output[-3:]) if installer_output else "вывод пуст"
            raise Exception(f"Установщик вернул код {returncode}: {tail}")

        set_status(t("st_forge_installed"))
        print("    Forge установлен!")

        if os.path.exists(installer_path):
            os.remove(installer_path)
            print("  Установщик Forge удалён")

        # ВСЕ УСПЕШНО!
        complete_progress(
            forge_uid,
            t("notif_forge_success", version=mc_version),
            success=True
        )
        return True

    except Exception as e:
        set_status(t("st_install_error", error=str(e)[:20]))
        print(f" Ошибка установки Forge: {e}")
        traceback.print_exc()
        complete_progress(
            forge_uid,
            t("notif_run_error"),
            success=False
        )
        return False

def is_forge_available(mc_version):
    return len(get_forge_versions(mc_version)) > 0


def is_vanilla_installed_fast(version, game_dir):
    """Быстрая проверка установлена ли Vanilla (без вызова API)"""
    version_dir = os.path.join(game_dir, "versions", version)
    version_json = os.path.join(version_dir, f"{version}.json")
    version_jar = os.path.join(version_dir, f"{version}.jar")

    if os.path.exists(version_json) and os.path.exists(version_jar):
        # Проверяем, что jar не повреждён (хотя бы 1 МБ)
        if os.path.getsize(version_jar) > 1000000:
            return True
    return False
ITEM_H = 38

def get_versions():
    versions = []
    for mirror in MIRRORS:
        try:
            url = f"{mirror}/mc/game/version_manifest.json"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            r = requests.get(url, timeout=15, headers=headers)
            if r.status_code == 200:
                data = r.json()
                versions = [v['id'] for v in data['versions'] if v['type'] == 'release']
                if versions:
                    print(f"    Список версий получен с {mirror}")
                    return versions
        except Exception as e:
            print(f"Ошибка получения версий с {mirror}: {e}")
            continue
    print(" Не удалось получить версии из интернета, используется встроенный список")
    return [
        "1.21.11", "1.21.10", "1.21.9", "1.21.8", "1.21.6", "1.21.5",
        "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21",
        "1.20.6", "1.20.5", "1.20.4", "1.20.3", "1.20.2", "1.20.1", "1.20",
        "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19",
        "1.18.2", "1.18.1", "1.18",
        "1.17.1", "1.17",
        "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
        "1.15.2", "1.15.1", "1.15",
        "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
        "1.13.2", "1.13.1", "1.13",
        "1.12.2", "1.12.1", "1.12",
        "1.11.2", "1.11",
        "1.10.2", "1.10",
        "1.9.4", "1.9",
        "1.8.9", "1.8.8", "1.8",
        "1.7.10"
    ]

all_versions = get_versions()
RELEASE_NAMES_CACHE = {}


def fetch_official_release_names():
    global RELEASE_NAMES_CACHE
    try:
        from bs4 import BeautifulSoup

        url = "https://minecraft.wiki/w/Java_Edition_version_history"
        headers = {'User-Agent': 'TurboLauncher/1.0'}

        print("  Автоматическая загрузка названий релизов...")
        resp = requests.get(url, timeout=15, headers=headers)

        if resp.status_code != 200:
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        tables = soup.find_all('table', class_='wikitable')
        temp_dict = {}
        last_name = "Hotfix"  # Дефолтное название

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue

                # 1-я колонка (название)
                name_text = cols[0].get_text(strip=True).replace("(Guide)", "").strip()

                # 2-я колонка (версия) — ОБЯЗАТЕЛЬНО ЧИСТИМ ОТ ПРОБЕЛОВ
                version_text = cols[1].get_text(strip=True).strip()

                # Если это реальная версия Minecraft
                if (version_text.startswith("1.") or version_text.startswith("26.")) and len(version_text) < 10:
                    # Проверяем, что название не пустое, не равно версии и длиннее 2 символов
                    if name_text and name_text != version_text and len(name_text) > 2:
                        last_name = name_text
                        temp_dict[version_text] = name_text
                    else:
                        # Если название пустое — ставим последнее запомненное или Hotfix
                        temp_dict[version_text] = last_name

        if temp_dict:
            RELEASE_NAMES_CACHE = temp_dict
            print(f"  Загружено {len(RELEASE_NAMES_CACHE)} названий релизов!")
        else:
            print("  Не удалось найти версии в таблице.")

    except Exception as e:
        print(f"  Ошибка автоматического парсинга: {e}")


threading.Thread(target=fetch_official_release_names, daemon=True).start()
def load_settings():
    global username, ram_gb, v_idx, fullscreen, delete_incompatible_mods, download_standard_mods, hide_notifications, java_path_cached
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                username = d.get("username", "Turbo_Player")
                ram_gb = d.get("ram", 4)
                v_idx = d.get("v_idx", 0)
                fullscreen = d.get("fullscreen", False)
                delete_incompatible_mods = d.get("delete_incompatible_mods", True)
                download_standard_mods = d.get("download_standard_mods", True)
                hide_notifications = d.get("hide_notifications", False)
                java_path_cached = d.get("java_path_cached", "")
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    else:
        username, ram_gb, v_idx, fullscreen = "Turbo_Player", 4, 0, False
        delete_incompatible_mods = True
        download_standard_mods = True
    return username, ram_gb, v_idx, fullscreen

delete_incompatible_mods = True
download_standard_mods = True
hide_notifications = False
username, ram_gb, v_idx, fullscreen = load_settings()

import atexit
import signal


def on_launcher_exit():
    global username, was_in_game
    print("  Лаунчер закрывается...")

    if was_in_game:
        try:
            update_online_count(username, False)
            print("    Игрок удалён из онлайна")
        except:
            pass
    else:
        print("    Игрок не заходил в игру, пропускаем")

    try:
        stop_discord_presence()
    except:
        pass

atexit.register(on_launcher_exit)

def signal_handler(signum, frame):
    on_launcher_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

import discord
from discord.ext import commands
import threading

BOT_TOKEN = ""

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot_ready = False

# Файл для хранения информации об игроках
PLAYER_INFO_FILE = os.path.join(GAME_DIR, "player_info.json")

# PATCH: gist_backend
def get_players_from_jsonbin():
    """Получает список игроков из GitHub Gist"""
    data = gist_read()
    if data:
        return data.get("players", [])
    return []


def get_launcher_version():
    """Получает версию лаунчера"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    return "1.0.0"

def save_player_info_to_file(username, mc_version, loader):
    """Сохраняет информацию об игроке"""
    try:
        player_data = {}
        if os.path.exists(PLAYER_INFO_FILE):
            with open(PLAYER_INFO_FILE, 'r', encoding='utf-8') as f:
                player_data = json.load(f)

        player_data[username] = {
            "minecraft_version": mc_version,
            "loader": loader,
            "last_play": time.time()
        }

        with open(PLAYER_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump(player_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения информации об игроке: {e}")

@bot.event
async def on_ready():
    global bot_ready
    bot_ready = True
    print(f'    Discord бот запущен как {bot.user}')
    print(f'  Команды бота: !list, !player_delete [ник], !player_check [ник]')

@bot.command(name='list')
async def list_players(ctx):
    """Показывает список игроков онлайн"""
    try:
        players = get_players_from_jsonbin()
        count = len(players)

        embed = discord.Embed(
            title="Игроки онлайн",
            color=0x00ff00
        )

        if count == 0:
            embed.description = "Никого нет в сети"
        else:
            player_list = "\n".join([f"• {p}" for p in players])
            embed.description = player_list
            embed.set_footer(text=f"Всего: {count} игроков")

        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f" Ошибка: {e}")

@bot.command(name='player_delete')
async def delete_player(ctx, nickname: str):
    """Удаляет игрока из онлайна (только админ)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send(" Только администраторы могут использовать эту команду!")
        return

    try:
        data = gist_read() or {"players": []}
        players = data.get("players", [])

        if True:
            if nickname in players:
                players.remove(nickname)
                new_data = {
                    "players": players,
                    "count": len(players),
                    "last_update": time.time()
                }
                put_ok = gist_write(new_data)

                if put_ok:
                    embed = discord.Embed(
                        title="    Игрок удалён",
                        description=f"**{nickname}** удалён из онлайна",
                        color=0x00ff00
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(" Ошибка обновления данных")
            else:
                await ctx.send(f" Игрок **{nickname}** не найден в онлайне")
        else:
            await ctx.send(" Ошибка получения данных")
    except Exception as e:
        await ctx.send(f" Ошибка: {e}")

@bot.command(name='player_check')
async def check_player(ctx, nickname: str = None):
    """Показывает информацию об игроке или версию лаунчера"""
    try:
        if nickname is None:
            launcher_version = get_launcher_version()
            players = get_players_from_jsonbin()

            embed = discord.Embed(
                title="  Turbo Launcher",
                description=f"**Версия лаунчера:** {launcher_version}",
                color=0x00ff00
            )
            embed.add_field(name=" Онлайн", value=f"{len(players)} игроков", inline=False)
            embed.set_footer(text="Turbo Launcher")
            await ctx.send(embed=embed)
            return

        players = get_players_from_jsonbin()
        is_online = nickname in players

        mc_version = "Неизвестно"
        loader = "Неизвестно"

        if os.path.exists(PLAYER_INFO_FILE):
            with open(PLAYER_INFO_FILE, 'r', encoding='utf-8') as f:
                player_data = json.load(f)
            if nickname in player_data:
                mc_version = player_data[nickname].get("minecraft_version", "Неизвестно")
                loader = player_data[nickname].get("loader", "Неизвестно")

        embed = discord.Embed(
            title=f"  Информация об игроке: {nickname}",
            color=0x00ff00 if is_online else 0xff0000
        )
        embed.add_field(name="  Статус", value="В сети" if is_online else "Не в сети", inline=True)
        embed.add_field(name="Версия Minecraft", value=mc_version, inline=True)
        embed.add_field(name="  Загрузчик", value=loader, inline=True)

        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f" Ошибка: {e}")

def run_discord_bot():
    """Запускает Discord бота в отдельном потоке"""
    try:
        bot.run(BOT_TOKEN, log_handler=None)  # без своего логгера: discord.py засорял лог трейсбеками реконнекта
    except Exception as e:
        # Если ошибка связана с сетью или DNS — просто игнорируем, не спамим в лог
        err_str = str(e)
        if "getaddrinfo failed" in err_str or "Cannot connect to host" in err_str:
            pass  # Молча уходим в офлайн, не ломая лаунчер
        else:
            print(f" Ошибка Discord бота: {e}")

# Запускаем бота, если токен указан
bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
bot_thread.start()
print("  Discord бот запускается...")
def save_settings():
    global username, ram_gb, v_idx, fullscreen, delete_incompatible_mods, download_standard_mods, hide_notifications, java_path_cached
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "username": username,
                "ram": ram_gb,
                "v_idx": v_idx,
                "fullscreen": fullscreen,
                "delete_incompatible_mods": delete_incompatible_mods,
                "download_standard_mods": download_standard_mods,
                "hide_notifications": hide_notifications,
                "java_path_cached": java_path_cached
            }, f, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")

status = t("st_ready")
is_running = False
current_tab = "ИГРАТЬ"
loaders = ["Vanilla", "Fabric", "Forge"]
l_idx = 0
show_dropdown = False
scroll_y = 0
active_input = False
dragging_ram = False
dragging_scroll = False

def monitor_game_process(proc):
    global is_running, minecraft_process, cancel_requested, was_in_game, status

    was_in_game = True  # Помечаем, что игрок реально был в игре
    update_online_count(username, True)

    # Обновляем Discord - показываем что играет через лаунчер
    update_discord_presence(
        "Играет через Turbo Launcher",
        f"Minecraft {all_versions[v_idx]}",
        start_time=int(time.time())
    )

    proc.wait()
    minecraft_process = None
    is_running = False
    cancel_requested = False
    print("    Игра завершена")
    update_online_count(username, False)

    # Возвращаем статус в окно лаунчера (раньше оставалось "В игре!" навсегда)
    status = t("st_ready")

    # Возвращаем статус в лаунчер
    update_discord_presence("В лаунчере", "")

def check_loader_compatibility(mc_version, loader):
    """
    Проверяет, совместим ли выбранный загрузчик с версией Minecraft
    Возвращает (is_compatible, suggested_loader)
    is_compatible = False -> отмена запуска
    is_compatible = True -> можно запускать с suggested_loader
    """
    try:
        if mc_version.startswith('1.'):
            parts = mc_version.split('.')
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
        else:
            # Новые версии (26.x и выше) — считаем совместимыми
            return True, loader
    except:
        return True, loader

    # ========== ПРОВЕРКА ДЛЯ FABRIC ==========
    if loader == "Fabric":
        # Fabric официально работает с 1.14+, но стабильно с 1.16.5
        if minor < 14:
            answer = messagebox.askyesno(
                " Fabric не поддерживается",
                f"Minecraft {mc_version} НЕ ПОДДЕРЖИВАЕТ Fabric!\n\n"
                f"• Fabric работает только с версиями 1.14 и выше\n"
                f"• Стабильная работа гарантирована с 1.16.5\n\n"
                f"Запустить с Vanilla вместо Fabric?",
                icon='warning'
            )
            if answer:
                return True, "Vanilla"
            else:
                return False, loader

        elif minor == 14 or minor == 15:
            answer = messagebox.askyesno(
                " Fabric может работать нестабильно",
                f"Minecraft {mc_version} имеет ОГРАНИЧЕННУЮ поддержку Fabric!\n\n"
                f"• Fabric API может работать, но моды (Sodium, Iris) — НЕТ\n"
                f"• Рекомендуется использовать 1.16.5 или выше\n\n"
                f"Продолжить с Fabric?",
                icon='warning'
            )
            if not answer:
                # Пользователь отказался, предлагаем Vanilla
                vanilla_answer = messagebox.askyesno(
                    "Запустить с Vanilla?",
                    f"Запустить Minecraft {mc_version} без модов (Vanilla)?",
                    icon='question'
                )
                if vanilla_answer:
                    return True, "Vanilla"
                else:
                    return False, loader
            return True, loader

        elif minor == 16 and patch < 5:
            answer = messagebox.askyesno(
                " Fabric может работать нестабильно",
                f"Minecraft {mc_version} имеет ОГРАНИЧЕННУЮ поддержку Fabric!\n\n"
                f"• Стабильная работа гарантирована с 1.16.5\n"
                f"• Моды (Sodium, Iris) могут не работать\n\n"
                f"Продолжить с Fabric?",
                icon='warning'
            )
            if not answer:
                vanilla_answer = messagebox.askyesno(
                    "Запустить с Vanilla?",
                    f"Запустить Minecraft {mc_version} без модов (Vanilla)?",
                    icon='question'
                )
                if vanilla_answer:
                    return True, "Vanilla"
                else:
                    return False, loader
            return True, loader

    # ========== ПРОВЕРКА ДЛЯ FORGE ==========
    if loader == "Forge":
        # Forge работает с 1.1+
        if minor < 1:
            answer = messagebox.askyesno(
                " Forge не поддерживается",
                f"Minecraft {mc_version} НЕ ПОДДЕРЖИВАЕТ Forge!\n\n"
                f"• Forge работает только с версиями 1.1 и выше\n\n"
                f"Запустить с Vanilla вместо Forge?",
                icon='warning'
            )
            if answer:
                return True, "Vanilla"
            else:
                return False, loader

        # Предупреждение для 1.13-1.15 (Forge может быть нестабилен)
        if 13 <= minor <= 15:
            answer = messagebox.askyesno(
                " Forge может работать нестабильно",
                f"Forge для Minecraft {mc_version} может работать нестабильно!\n\n"
                f"• Рекомендуется использовать 1.12.2 или 1.16.5+\n\n"
                f"Продолжить с Forge?",
                icon='warning'
            )
            if not answer:
                vanilla_answer = messagebox.askyesno(
                    "Запустить с Vanilla?",
                    f"Запустить Minecraft {mc_version} без Forge (Vanilla)?",
                    icon='question'
                )
                if vanilla_answer:
                    return True, "Vanilla"
                else:
                    return False, loader
            return True, loader

    return True, loader
def show_incompatible_warning():
    """Показывает предупреждение о возможных проблемах и возвращает True (продолжить)"""
    return messagebox.askokcancel(
        "Предупреждение о совместимости",
        "⚠️ ВНИМАНИЕ! ⚠️\n\n"
        "У вас включено: 'Скачивать стандартные моды'\n"
        "У вас выключено: 'Удалять несовместимые моды'\n\n"
        "ЭТО МОЖЕТ ВЫЗВАТЬ ПРОБЛЕМЫ!\n\n"
        "При смене версии Minecraft старые моды НЕ БУДУТ УДАЛЕНЫ,\n"
        "что может привести к конфликтам и вылетам игры.\n\n"
        "Рекомендуется включить 'Удалять несовместимые моды'.\n\n"
        "Вы уверены, что хотите продолжить?",
        icon='warning'
    )

_mojang_manifest_cache = None       # полный манифест Mojang
_mojang_authlib_cache = {}          # {"1.20.1": "4.0.43", ...}
_ely_versions_cache = None          # список версий Ely Authlib
_ely_jar_check_cache = {}           # {"4.0.43-ely.5": True/False}


def fetch_mojang_manifest():
    """Скачивает и кэширует version_manifest.json от Mojang."""
    global _mojang_manifest_cache
    if _mojang_manifest_cache is not None:
        return _mojang_manifest_cache

    try:
        url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            _mojang_manifest_cache = r.json()
            print(f"  Манифест Mojang загружен ({len(_mojang_manifest_cache['versions'])} версий)")
            return _mojang_manifest_cache
    except Exception as e:
        print(f"  Ошибка загрузки манифеста Mojang: {e}")
    return None


def fetch_mojang_authlib_version(mc_version, game_dir):
    """
    Возвращает версию com.mojang:authlib для указанной версии MC.
    Сначала пробует локальный version.json, потом качает с Mojang.
    """
    global _mojang_authlib_cache

    if mc_version in _mojang_authlib_cache:
        return _mojang_authlib_cache[mc_version]

    # 1. Локальный version.json (если MC уже установлена)
    local_json = os.path.join(game_dir, "versions", mc_version, f"{mc_version}.json")
    if os.path.exists(local_json):
        try:
            with open(local_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for lib in data.get('libraries', []):
                name = lib.get('name', '')
                if name.startswith('com.mojang:authlib:'):
                    ver = name.split(':')[-1]
                    _mojang_authlib_cache[mc_version] = ver
                    return ver
        except Exception:
            pass

    # 2. Через манифест Mojang
    manifest = fetch_mojang_manifest()
    if not manifest:
        return None

    version_url = None
    for v in manifest['versions']:
        if v['id'] == mc_version:
            version_url = v['url']
            break

    if not version_url:
        print(f"  Версия {mc_version} не найдена в манифесте Mojang")
        return None

    try:
        r = requests.get(version_url, timeout=15)
        if r.status_code != 200:
            return None
        version_data = r.json()

        for lib in version_data.get('libraries', []):
            name = lib.get('name', '')
            if name.startswith('com.mojang:authlib:'):
                ver = name.split(':')[-1]
                _mojang_authlib_cache[mc_version] = ver
                return ver
    except Exception as e:
        print(f"  Ошибка получения authlib версии: {e}")

    return None


def fetch_ely_authlib_versions():
    """Скачивает список всех версий Ely Authlib из maven-metadata.xml."""
    global _ely_versions_cache
    if _ely_versions_cache is not None:
        return _ely_versions_cache

    url = "https://maven.ely.by/releases/by/ely/authlib/maven-metadata.xml"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return []

        # Простой regex — не тащим lxml
        versions = re.findall(r'<version>([^<]+)</version>', r.text)
        _ely_versions_cache = versions
        print(f"  Загружено {len(versions)} версий Ely Authlib")
        return versions
    except Exception as e:
        print(f"  Ошибка загрузки списка Ely Authlib: {e}")
        return []


def parse_authlib_version(v):
    """
    '4.0.43-ely.5' -> (4, 0, 43, 5)
    '4.0.43'       -> (4, 0, 43, 0)
    """
    try:
        ely_part = 0
        if '-ely.' in v:
            base, ely_str = v.rsplit('-ely.', 1)
            ely_part = int(ely_str)
        else:
            base = v

        nums = [int(x) for x in base.split('.')]
        while len(nums) < 3:
            nums.append(0)

        return (nums[0], nums[1], nums[2], ely_part)
    except Exception:
        return (0, 0, 0, 0)


def find_ely_authlib_for_version(mojang_authlib_version):
    """
    Находит лучшую Ely Authlib для указанной версии Mojang Authlib.
    Логика: точное совпадение базы (4.0.43) → максимальный -ely.N.
    Если точного нет — ближайшее меньшее.
    """
    all_versions = fetch_ely_authlib_versions()
    if not all_versions:
        return None

    target = parse_authlib_version(mojang_authlib_version)[:3]

    # 1. Точное совпадение базы
    exact = []
    for v in all_versions:
        parsed = parse_authlib_version(v)
        if parsed[:3] == target:
            exact.append((parsed, v))

    if exact:
        exact.sort(key=lambda x: x[0][3], reverse=True)
        result = exact[0][1]
        print(f"  Ely Authlib для Mojang {mojang_authlib_version}: {result} (точное)")
        return result

    # 2. Ближайшее меньшее
    all_parsed = sorted(
        [(parse_authlib_version(v), v) for v in all_versions],
        key=lambda x: x[0][:3],
        reverse=True
    )
    for parsed, v in all_parsed:
        if parsed[:3] < target:
            print(f"  Ely Authlib для Mojang {mojang_authlib_version}: {v} (ближайшее меньшее)")
            return v

    # 3. Fallback — самая старая
    if all_parsed:
        oldest = all_parsed[-1][1]
        print(f"  Ely Authlib для Mojang {mojang_authlib_version}: {oldest} (fallback)")
        return oldest

    return None


def check_ely_authlib_exists(version):
    """Проверяет, что JAR реально доступен в Maven Ely. Кэширует."""
    if version in _ely_jar_check_cache:
        return _ely_jar_check_cache[version]

    url = f"https://maven.ely.by/releases/by/ely/authlib/{version}/authlib-{version}.jar"
    try:
        r = requests.head(url, timeout=10)
        exists = r.status_code == 200
        _ely_jar_check_cache[version] = exists
        return exists
    except Exception:
        _ely_jar_check_cache[version] = False
        return False


def get_ely_authlib_version(mc_version, game_dir):
    """
    Главная функция: возвращает подходящую Ely Authlib для версии MC
    или None, если не найдено / не нужно.
    """
    mojang_ver = fetch_mojang_authlib_version(mc_version, game_dir)
    if not mojang_ver:
        print(f"  Не удалось определить Mojang Authlib для {mc_version}")
        return None

    print(f"  Minecraft {mc_version} требует Mojang Authlib {mojang_ver}")

    ely_ver = find_ely_authlib_for_version(mojang_ver)
    if not ely_ver:
        return None

    # Проверяем, что JAR реально есть
    if not check_ely_authlib_exists(ely_ver):
        print(f"  {ely_ver} недоступен в Maven, ищем другой...")

        # Пробуем остальные Ely-версии с той же базой
        target = parse_authlib_version(mojang_ver)[:3]
        all_versions = fetch_ely_authlib_versions()
        candidates = sorted(
            [v for v in all_versions if parse_authlib_version(v)[:3] == target],
            key=lambda v: parse_authlib_version(v)[3],
            reverse=True
        )
        for cand in candidates:
            if check_ely_authlib_exists(cand):
                print(f"  Использую {cand} (fallback)")
                return cand

        return None

    return ely_ver
def get_ely_uuid_and_skin(username):
    """Получает UUID и скин игрока через официальное API Ely.by (совместимое с Mojang API)"""
    try:
        import requests
        import json

        print(f"  Запрос UUID для {username} через Ely.by API...")

        # 1. Получаем UUID по нику (как в Mojang API)
        resp = requests.get(f"https://authserver.ely.by/api/users/profiles/minecraft/{username}", timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            uuid = data.get("id")
            name = data.get("name")
            print(f"    Найден UUID: {uuid} для {name}")

            # 2. Получаем скин через стандартный Mojang API (Ely.by его поддерживает)
            skin_resp = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}", timeout=10)

            if skin_resp.status_code == 200:
                skin_data = skin_resp.json()
                properties = skin_data.get("properties", [])
                for prop in properties:
                    if prop.get("name") == "textures":
                        import base64
                        textures = json.loads(base64.b64decode(prop.get("value")).decode('utf-8'))
                        skin_url = textures.get("textures", {}).get("SKIN", {}).get("url")
                        if skin_url:
                            print(f"    Найден скин: {skin_url}")
                            return uuid, skin_url
            else:
                print(f"    Скин не найден (код {skin_resp.status_code})")

            return uuid, None
        elif resp.status_code == 204:
            print(f"    Игрок {username} не найден в Ely.by")
        else:
            print(f"    Ошибка API: {resp.status_code}")

    except Exception as e:
        print(f"    Ошибка: {e}")

    return None, None


def force_ely_skin_download(game_dir, username):
    """Скачивает скин Ely.by через правильное API"""
    try:
        import requests
        import json

        # ПРАВИЛЬНОЕ API (skinsystem, а не api.ely.by!)
        url = f"https://skinsystem.ely.by/textures/{username}"
        print(f"    Запрос скина: {url}")

        resp = requests.get(url, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            skin_url = data.get("SKIN", {}).get("url")

            if skin_url:
                print(f"    Скин найден: {skin_url}")

                # Скачиваем скин
                skin_dir = os.path.join(game_dir, "skins")
                os.makedirs(skin_dir, exist_ok=True)
                skin_path = os.path.join(skin_dir, f"{username}.png")

                # Скачиваем изображение
                img_data = requests.get(skin_url, timeout=10).content
                with open(skin_path, 'wb') as f:
                    f.write(img_data)

                print(f"    Скин сохранён: {skin_path}")
                return [f"-Dminecraft.player.skin={skin_path}"]
            else:
                print(f"    В ответе нет SKIN.url")
        else:
            print(f"    Скин не найден (код {resp.status_code})")

    except Exception as e:
        print(f"    Ошибка: {e}")

    return []


# Строки, которые minecraft_launcher_lib отдаёт в callback["setStatus"]
INSTALL_STATUS_KEYS = {
    "Download Libraries": "st_install_download_libraries",
    "Download Assets": "st_install_download_assets",
    "Install java runtime": "st_install_java_runtime",
    "Installation complete": "st_install_complete",
}

def _translated_install_status(text):
    """Переводит английские статусы установки из minecraft_launcher_lib."""
    global status
    key = INSTALL_STATUS_KEYS.get(text)
    status = t(key) if key else text




# ===== Хелперы ручной установки (перенесено из beta.py) =====
import hashlib  # нужен verify_sha1 (перенесён из beta.py)


_download_session = None
_download_session_lock = threading.Lock()


def get_download_session():
    """Общая сессия requests: keep-alive и пул соединений. Без неё каждый файл
    открывает новое соединение, и тысячи ассетов качаются часами."""
    global _download_session
    if _download_session is None:
        with _download_session_lock:
            if _download_session is None:
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=2)
                session.mount("https://", adapter)
                session.mount("http://", adapter)
                _download_session = session
    return _download_session


def download_batch(items, label, on_progress=None, max_workers=16, report_interval=0.2):
    """Качает файлы параллельно. items = [(url, dest, sha1, name), ...].

    Прогресс отдаётся плавно: учитываются и завершённые файлы, и доля текущих,
    обновление не чаще report_interval секунд (иначе полоса дёргается пачками).
    Возвращает (скачано, список неудач)."""
    import concurrent.futures

    total = len(items)
    if total == 0:
        return 0, []

    lock = threading.RLock()
    state = {"done": 0, "last_report": 0.0}
    partials = {}
    failed = []

    def report(force=False):
        if on_progress is None:
            return
        now = time.time()
        if not force and now - state["last_report"] < report_interval:
            return
        state["last_report"] = now
        with lock:
            value = state["done"] + sum(partials.values())
        on_progress(min(value, float(total)), total, "")

    def worker(item):
        url, dest, sha1, name = item
        if cancel_requested:
            return
        key = threading.current_thread().name

        def chunk_progress(done_bytes, total_bytes, _label):
            with lock:
                partials[key] = (done_bytes / total_bytes) if total_bytes else 0.0
            report()

        ok = download_file(url, dest, sha1, None, name, progress_cb=chunk_progress)
        with lock:
            partials[key] = 0.0
            state["done"] += 1
            if not ok and not cancel_requested:
                failed.append((name, url))
        report(force=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, max(1, total))) as executor:
        list(executor.map(worker, items))

    return state["done"], failed


def verify_sha1(file_path, expected_sha1):
    """Проверяет SHA1 файла."""
    if not os.path.exists(file_path):
        return False
    if not expected_sha1:
        return True
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha1.update(chunk)
        return sha1.hexdigest().lower() == expected_sha1.lower()
    except Exception:
        return False


def download_file(url, dest_path, expected_sha1=None, set_status=None, label="", progress_cb=None):
    """Скачивает файл с проверкой cancel_requested и SHA1."""
    global cancel_requested

    if expected_sha1 and verify_sha1(dest_path, expected_sha1):
        return True

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = dest_path + ".tmp"

    try:
        r = get_download_session().get(url, stream=True, timeout=60)
        if r.status_code != 200:
            print(f"  [{label}] сервер вернул код {r.status_code}: {url[:90]}")
            return False

        total = int(r.headers.get('content-length', 0))
        downloaded = 0

        with open(tmp_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if cancel_requested:
                    f.close()
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    return False
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb is not None:
                        progress_cb(downloaded, total, label)
                    elif set_status and total > 0:
                        percent = downloaded / total * 100
                        set_status(f"{label}: {percent:.1f}%")

        if expected_sha1 and not verify_sha1(tmp_path, expected_sha1):
            size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
            print(f"  [{label}] SHA1 не совпал (ожидали {expected_sha1[:12]}..., скачано {size} байт)")
            os.remove(tmp_path)
            return False

        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.replace(tmp_path, dest_path)
        return True

    except Exception as e:
        print(f"  [{label}] ошибка скачивания: {type(e).__name__}: {e}")
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        return False
def cleanup_tmp_files(game_dir):
    """Удаляет все .tmp файлы в libraries и assets."""
    for root_dir in (os.path.join(game_dir, "libraries"), os.path.join(game_dir, "assets")):
        if not os.path.exists(root_dir):
            continue
        for dirpath, _, filenames in os.walk(root_dir):
            for fname in filenames:
                if fname.endswith(".tmp"):
                    try:
                        os.remove(os.path.join(dirpath, fname))
                    except Exception:
                        pass


def cleanup_vanilla(version, game_dir, also_loader=None):
    """Удаляет папку Vanilla + ядро-мод (если указан)."""
    version_dir = os.path.join(game_dir, "versions", version)
    if os.path.exists(version_dir):
        shutil.rmtree(version_dir, ignore_errors=True)
        print(f"  Аварийная очистка: удалена версия {version}")

    if also_loader:
        loader_dir = os.path.join(game_dir, "versions", also_loader)
        if os.path.exists(loader_dir):
            shutil.rmtree(loader_dir, ignore_errors=True)
            print(f"  Аварийная очистка: удалён ядро-мод {also_loader}")

    cleanup_tmp_files(game_dir)


def cleanup_java(version, game_dir):
    """Удаляет скачанную Java указанной версии и её временные архивы."""
    runtime_dir = os.path.join(game_dir, "runtime")
    java_dir = os.path.join(runtime_dir, f"java{version}")

    if os.path.exists(java_dir):
        shutil.rmtree(java_dir, ignore_errors=True)
        print(f"  Аварийная очистка: удалена Java {version}")

    if os.path.exists(runtime_dir):
        for f in os.listdir(runtime_dir):
            if f.startswith(f"java{version}_temp"):
                try:
                    os.remove(os.path.join(runtime_dir, f))
                    print(f"  Аварийная очистка: удалён {f}")
                except Exception:
                    pass


def cleanup_ely_authlib(version, game_dir):
    """Удаляет скачанную Ely Authlib указанной версии."""
    if not version:
        return
    authlib_dir = os.path.join(game_dir, "libraries", "by", "ely", "authlib", version)
    if os.path.exists(authlib_dir):
        shutil.rmtree(authlib_dir, ignore_errors=True)
        print(f"  Аварийная очистка: удалена Ely Authlib {version}")


def cleanup_mods(mod_names, game_dir):
    """Удаляет указанные моды из папки mods."""
    mods_dir = os.path.join(game_dir, "mods")
    if not os.path.exists(mods_dir):
        return
    for f in os.listdir(mods_dir):
        for mod_name in mod_names:
            if f.lower().startswith(mod_name.lower()):
                try:
                    os.remove(os.path.join(mods_dir, f))
                    print(f"  Аварийная очистка: удалён мод {f}")
                except Exception:
                    pass

def run_launch_logic():
    global status, is_running, cancel_requested, minecraft_process, installer_process, l_idx
    try:
        is_running = True
        cancel_requested = False
        ver = all_versions[v_idx]
        loader = loaders[l_idx]

        save_player_info_to_file(username, ver, loader)
        print(f"  Информация для Discord сохранена: {username} -> {ver}, {loader}")


        launch_uid = show_progress(
            text=t("notif_launching", version=ver, loader=loader),
            title="Запуск",
            progress=0
        )
        install_uid = None

        java_future = None

        # ===== ПРОВЕРКА СОВМЕСТИМОСТИ ЗАГРУЗЧИКА =====
        is_compatible, suggested_loader = check_loader_compatibility(ver, loader)

        if not is_compatible:
            status = t("st_cancelled_incompatible")
            is_running = False
            # <--- ИЗМЕНЕНО: Передаём launch_uid вместо text
            complete_progress(
                launch_uid,
                t("notif_incompatible"),
                success=False
            )
            return

        if suggested_loader != loader:
            l_idx = loaders.index(suggested_loader)
            loader = suggested_loader
            status = t("st_auto_switched", loader=loader, version=ver)
            print(f"  Переключено на {loader} для совместимости с {ver}")

        def set_status(t):
            global status
            status = t

        print(f"\n  Запуск: версия {ver}, загрузчик {loader}")

        if ver is None:
            status = t("st_version_not_selected")
            is_running = False
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_version_not_selected"),
                success=False
            )
            return

        if loader == "Forge" and not is_forge_available(ver):
            status = t("st_forge_unavailable", version=ver)
            print(f" Forge нет для {ver}")
            is_running = False
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_forge_not_found", version=ver),
                success=False
            )
            return

        if cancel_requested:
            status = t("st_cancelled")
            is_running = False
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_canceled"),
                success=False
            )
            return

        # <--- ИЗМЕНЕНО: Передаём launch_uid первым аргументом
        update_progress(
            launch_uid,
            t("notif_launching", version=ver, loader=loader),
            10
        )

        set_status(t("st_searching"))
        installed = minecraft_launcher_lib.utils.get_installed_versions(GAME_DIR)
        print(f"Установленные версии: {[v['id'] for v in installed]}")

        target_id = None

        if loader == "Fabric":
            for v in installed:
                if v['id'].startswith("fabric-loader-") and v['id'].endswith(f"-{ver}"):
                    target_id = v['id']
                    break
        elif loader == "Forge":
            for v in installed:
                if v['id'].startswith(f"{ver}-forge"):
                    target_id = v['id']
                    break
        else:
            for v in installed:
                if v['id'] == ver:
                    target_id = v['id']
                    break

        # ===== ЗАЩИТА ОТ НЕПОЛНОЙ УСТАНОВКИ =====
        # Папка версии могла остаться после прерванной закачки: JSON есть, а client
        # jar нет. get_installed_versions() такую версию видит, установка
        # пропускалась, и игра падала с "Could not find or load main class".
        if target_id is not None and not is_vanilla_installed_fast(ver, GAME_DIR):
            print(f"  Установка {ver} неполная (нет {ver}.jar) — запускаю установку заново")
            target_id = None

        # ===== ЕСЛИ ВЕРСИЯ НЕ УСТАНОВЛЕНА - НАЧИНАЕМ УСТАНОВКУ =====
        if target_id is None:
            print(f" {loader} для {ver} не найден, начинаем установку")

            # Закрываем уведомление о запуске и показываем установку
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_installing", loader=loader, version=ver),
                success=True
            )

            # Показываем новое уведомление об установке (сохраняем UID!)
            if loader == "Vanilla":
                install_uid = show_progress(
                    text=t("notif_installing", loader=loader, version=ver),
                    title=t("notif_install_title"),
                    progress=20
                )

            # Определяем, есть ли уже ядро-мод для этой версии (для аварийной очистки)
            loader_id_to_cleanup = None
            _versions_dir = os.path.join(GAME_DIR, "versions")
            if os.path.exists(_versions_dir):
                if loader == "Fabric":
                    for _folder in os.listdir(_versions_dir):
                        if _folder.startswith("fabric-loader-") and _folder.endswith(f"-{ver}"):
                            loader_id_to_cleanup = _folder
                            break
                elif loader == "Forge":
                    for _folder in os.listdir(_versions_dir):
                        if _folder.startswith(f"{ver}-forge"):
                            loader_id_to_cleanup = _folder
                            break


            install_ok = False
            try:
                if not is_vanilla_installed_fast(ver, GAME_DIR):
                    # ===== РУЧНАЯ УСТАНОВКА VANILLA С ОТМЕНОЙ И АВАРИЙНОЙ ОЧИСТКОЙ =====
                    print(f"  Vanilla {ver} не установлена, начинаю установку...")

                    if loader == "Vanilla":
                        update_progress(
                            launch_uid,
                            t("notif_installing", loader=loader, version=ver),
                            30
                        )

                    set_status(t("st_vanilla_installing", version=ver))

                    versions_dir = os.path.join(GAME_DIR, "versions", ver)
                    os.makedirs(versions_dir, exist_ok=True)

                    version_json_path = os.path.join(versions_dir, f"{ver}.json")
                    client_jar_path = os.path.join(versions_dir, f"{ver}.jar")

                    # ===== 1. Манифест =====
                    set_status(t("st_manifest_fetching"))
                    try:
                        manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
                        r = requests.get(manifest_url, timeout=15)
                        manifest = r.json()
                    except Exception as e:
                        print(f"  Не удалось получить манифест: {e}")
                        status = t("st_install_failed_version", version=ver)
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_vanilla_error"), success=False)
                        return

                    if cancel_requested:
                        status = t("st_cancelled")
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_canceled"), success=False)
                        return

                    version_url = None
                    for v in manifest['versions']:
                        if v['id'] == ver:
                            version_url = v['url']
                            break

                    if not version_url:
                        print(f"  Версия {ver} не найдена в манифесте")
                        status = t("st_install_failed_version", version=ver)
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_vanilla_error"), success=False)
                        return

                    # ===== 2. version.json =====
                    set_status(t("st_version_json_fetching", version=ver))
                    if cancel_requested:
                        status = t("st_cancelled")
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_canceled"), success=False)
                        return

                    try:
                        r = requests.get(version_url, timeout=15)
                        version_data = r.json()
                    except Exception as e:
                        print(f"  Не удалось скачать version.json: {e}")
                        status = t("st_install_failed_version", version=ver)
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_vanilla_error"), success=False)
                        return

                    with open(version_json_path, 'w', encoding='utf-8') as f:
                        json.dump(version_data, f, indent=2)

                    if cancel_requested:
                        status = t("st_cancelled")
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_canceled"), success=False)
                        return

                    # ===== 3. client.jar =====
                    client_info = version_data.get('downloads', {}).get('client', {})
                    client_url = client_info.get('url')
                    client_sha1 = client_info.get('sha1')

                    if client_url:
                        set_status(t("st_client_jar_downloading"))

                        def _client_progress(done, total_bytes, label):
                            percent = (done / total_bytes * 100.0) if total_bytes else 0.0
                            text = "%s %d%%" % (t("st_client_jar_downloading"), int(percent))
                            set_status(text)
                            update_progress(
                                install_uid if install_uid is not None else launch_uid,
                                text,
                                min(20 + 10.0 * percent / 100.0, 30)
                            )

                        if not download_file(client_url, client_jar_path, client_sha1, None, "client.jar",
                                             progress_cb=_client_progress):
                            if cancel_requested:
                                status = t("st_cancelled")
                                is_running = False
                                cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                                complete_progress(launch_uid, t("notif_canceled"), success=False)
                                return
                            print(f"  ОШИБКА: client.jar не скачан!")
                            status = t("st_install_failed_version", version=ver)
                            is_running = False
                            cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                            complete_progress(launch_uid, t("notif_vanilla_error"), success=False)
                            return

                    if cancel_requested:
                        status = t("st_cancelled")
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_canceled"), success=False)
                        return

                    # ===== 4. libraries =====
                    libraries = version_data.get('libraries', [])
                    total_libs = len(libraries)
                    libs_dir = os.path.join(GAME_DIR, "libraries")
                    notification_uid = install_uid if install_uid is not None else launch_uid

                    lib_tasks = []
                    for lib in libraries:
                        artifact = lib.get('downloads', {}).get('artifact', {})
                        if not artifact:
                            continue
                        lib_url = artifact.get('url')
                        lib_path = artifact.get('path')
                        if not lib_url or not lib_path:
                            continue
                        lib_tasks.append((lib_url, os.path.join(libs_dir, lib_path), artifact.get('sha1'),
                                          os.path.basename(lib_path)))

                    def _libs_progress(count, total, _name):
                        overall = 30 + 30.0 * count / max(1, total)
                        text = "%s %d%%" % (t("st_libraries_downloading", current=int(count), total=total),
                                            int(overall))
                        set_status(text)
                        update_progress(notification_uid, text, min(overall, 60))

                    print(f"  Скачивание библиотек: {len(lib_tasks)} файлов, 16 потоков")
                    _libs_done, _libs_failed = download_batch(lib_tasks, "libraries", _libs_progress, 16)
                    print(f"  Библиотеки готовы: {_libs_done}, ошибок: {len(_libs_failed)}")

                    # ===== 4b. Нативы: скачиваем classifiers и распаковываем =====
                    # Без них старые версии (<=1.18) падают с "Failed to locate library: lwjgl.dll"
                    native_entries = []
                    for lib in libraries:
                        downloads = lib.get('downloads', {})
                        classifiers = downloads.get('classifiers') or {}
                        natives_map = lib.get('natives') or {}
                        if not classifiers or not natives_map:
                            continue
                        if platform.system() == "Windows":
                            key = natives_map.get('windows')
                        elif platform.system() == "Darwin":
                            key = natives_map.get('osx')
                        else:
                            key = natives_map.get('linux')
                        if not key:
                            continue
                        key = key.replace("${arch}", "64" if sys.maxsize > 2 ** 32 else "32")
                        info = classifiers.get(key)
                        if not info or not info.get('url'):
                            continue
                        dest = os.path.join(libs_dir, info.get('path') or os.path.basename(info['url']))
                        native_entries.append((info['url'], dest, info.get('sha1'), key, lib.get('extract') or {}))

                    if native_entries:
                        natives_dir = os.path.join(versions_dir, "natives")
                        os.makedirs(natives_dir, exist_ok=True)
                        native_tasks = [(u, d, s, n) for (u, d, s, n, _e) in native_entries]
                        print(f"  Скачивание нативов: {len(native_tasks)} файлов, 16 потоков")
                        _nat_done, _nat_failed = download_batch(native_tasks, "natives", None, 16)
                        unpacked = 0
                        for url, dest, sha1, name, extract in native_entries:
                            if not os.path.exists(dest):
                                continue
                            excluded = [r.split("/")[-1] for r in ((extract or {}).get('exclude') or [])]
                            try:
                                with zipfile.ZipFile(dest) as archive:
                                    for member in archive.namelist():
                                        if member.endswith("/"):
                                            continue
                                        base = member.split("/")[-1]
                                        if not base or base.startswith("META-INF"):
                                            continue
                                        if any(base.startswith(rule) for rule in excluded):
                                            continue
                                        with archive.open(member) as src, open(os.path.join(natives_dir, base), "wb") as dst:
                                            shutil.copyfileobj(src, dst)
                                        unpacked += 1
                            except Exception as e:
                                print(f"  [{name}] не удалось распаковать нативы: {e}")
                        print(f"  Нативы готовы: {unpacked} файлов в {natives_dir}")

                    if cancel_requested:
                        status = t("st_cancelled")
                        is_running = False
                        cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                        complete_progress(launch_uid, t("notif_canceled"), success=False)
                        return


                    # ===== 5. assets =====
                    asset_index_info = version_data.get('assetIndex', {})
                    asset_index_url = asset_index_info.get('url')
                    asset_index_id = asset_index_info.get('id', ver)

                    if asset_index_url:
                        set_status(t("st_assets_index_downloading"))

                        if cancel_requested:
                            status = t("st_cancelled")
                            is_running = False
                            cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                            complete_progress(launch_uid, t("notif_canceled"), success=False)
                            return

                        try:
                            r = requests.get(asset_index_url, timeout=15)
                            assets_index_data = r.json()
                        except Exception as e:
                            print(f"  Не удалось скачать asset index: {e}")
                            assets_index_data = None

                        if assets_index_data:
                            indexes_dir = os.path.join(GAME_DIR, "assets", "indexes")
                            os.makedirs(indexes_dir, exist_ok=True)
                            with open(os.path.join(indexes_dir, f"{asset_index_id}.json"), 'w', encoding='utf-8') as f:
                                json.dump(assets_index_data, f, indent=2)

                            objects = assets_index_data.get('objects', {})
                            total_assets = len(objects)
                            objects_dir = os.path.join(GAME_DIR, "assets", "objects")

                            asset_tasks = []
                            for asset_name, asset_info in objects.items():
                                asset_hash = asset_info.get('hash')
                                if not asset_hash:
                                    continue
                                sub_dir = asset_hash[:2]
                                dest = os.path.join(objects_dir, sub_dir, asset_hash)
                                if os.path.exists(dest):
                                    continue
                                asset_url = f"https://resources.download.minecraft.net/{sub_dir}/{asset_hash}"
                                asset_tasks.append((asset_url, dest, None, asset_hash))

                            def _assets_progress(count, total, _name):
                                overall = 60 + 35.0 * count / max(1, total)
                                text = "%s %d%%" % (t("st_assets_downloading", current=int(count), total=total),
                                                    int(overall))
                                set_status(text)
                                update_progress(notification_uid, text, min(overall, 95))

                            print(f"  Скачивание ресурсов: {len(asset_tasks)} файлов, 16 потоков")
                            _assets_done, _assets_failed = download_batch(asset_tasks, "assets", _assets_progress, 16)
                            print(f"  Ресурсы готовы: {_assets_done}, ошибок: {len(_assets_failed)}")

                            if cancel_requested:
                                status = t("st_cancelled")
                                is_running = False
                                cleanup_vanilla(ver, GAME_DIR, also_loader=loader_id_to_cleanup)
                                complete_progress(launch_uid, t("notif_canceled"), success=False)
                                return


                    # ===== 6. Конфиг логирования (client-*.xml) =====
                    # Он подставляется в аргументы запуска (-Dlog4j.configurationFile)
                    log_cfg = ((version_data.get('logging') or {}).get('client') or {}).get('file') or {}
                    if log_cfg.get('url'):
                        log_dir = os.path.join(GAME_DIR, "assets", "log_configs")
                        os.makedirs(log_dir, exist_ok=True)
                        log_dest = os.path.join(log_dir, log_cfg.get('id') or os.path.basename(log_cfg['url']))
                        if not os.path.exists(log_dest):
                            if download_file(log_cfg['url'], log_dest, log_cfg.get('sha1'), None, "log_config"):
                                print(f"  Конфиг логирования сохранён: {os.path.basename(log_dest)}")

                    set_status(t("st_install_complete"))
                    print(f"  Vanilla {ver} установлена")
                else:
                    print(f"  Vanilla {ver} уже установлена (быстрая проверка)")
                if cancel_requested:
                    status = t("st_cancelled")
                    is_running = False
                    # <--- ИЗМЕНЕНО
                    complete_progress(
                        launch_uid,
                        t("notif_canceled"),
                        success=False
                    )
                    return
                install_ok = True
            finally:
                # Закрываем уведомление установки в любом случае
                if install_uid is not None:
                    complete_progress(
                        install_uid,
                        t("notif_installed", loader="Vanilla", version=ver) if install_ok
                        else t("notif_canceled"),
                        success=install_ok
                    )
                    install_uid = None
            # ===== ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА JAVA (только для Fabric/Forge) =====
            import concurrent.futures
            if loader in ["Fabric", "Forge"]:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    java_future = executor.submit(get_java_executable, ver, None)

                    if loader == "Fabric":
                        set_status(t("st_fabric_installing"))
                        if not install_fabric_custom(ver, GAME_DIR, set_status):
                            if not cancel_requested:
                                status = t("st_fabric_install_failed", version=ver)
                            is_running = False
                            # <--- ИЗМЕНЕНО
                            complete_progress(
                                launch_uid,
                                t("notif_install_error", loader=loader),
                                success=False
                            )
                            return

                        if java_future:
                            java_future.result()

                        installed = minecraft_launcher_lib.utils.get_installed_versions(GAME_DIR)
                        print(f"После установки: {[v['id'] for v in installed]}")
                        found = False
                        for v in installed:
                            if v['id'].startswith("fabric-loader-") and v['id'].endswith(f"-{ver}"):
                                target_id = v['id']
                                found = True
                                break
                        if not found:
                            versions_dir = os.path.join(GAME_DIR, "versions")
                            for folder in os.listdir(versions_dir):
                                if folder.startswith("fabric-loader-") and folder.endswith(f"-{ver}"):
                                    target_id = folder
                                    found = True
                                    break
                        if not found:
                            print(" Не удалось найти Fabric версию после установки!")
                            status = t("st_fabric_not_found_after", version=ver)
                            is_running = False
                            # <--- ИЗМЕНЕНО
                            complete_progress(
                                launch_uid,
                                t("notif_not_found_error"),
                                success=False
                            )
                            return

                    elif loader == "Forge":
                        set_status(t("st_forge_installing"))
                        if not install_forge(ver, GAME_DIR, set_status):
                            if not cancel_requested:
                                status = t("st_forge_install_failed", version=ver)
                            is_running = False
                            # <--- ИЗМЕНЕНО
                            complete_progress(
                                launch_uid,
                                t("notif_install_error", loader=loader),
                                success=False
                            )
                            return

                        if java_future:
                            java_future.result()

                        installed = minecraft_launcher_lib.utils.get_installed_versions(GAME_DIR)
                        print(f"После установки: {[v['id'] for v in installed]}")
                        for v in installed:
                            if v['id'].startswith(f"{ver}-forge"):
                                target_id = v['id']
                                break
                        if target_id is None:
                            status = t("st_forge_not_found_after", version=ver)
                            is_running = False
                            # <--- ИЗМЕНЕНО
                            complete_progress(
                                launch_uid,
                                t("notif_not_found_error"),
                                success=False
                            )
                            return
            else:
                # Vanilla - просто устанавливаем
                target_id = ver

                # Если была установка Vanilla - завершаем уведомление
                if loader == "Vanilla":
                    # <--- ИЗМЕНЕНО
                    complete_progress(
                        launch_uid,
                        f"Vanilla {ver} установлена",
                        success=True
                    )
                    # Показываем запуск (используем ОДНО уведомление)
                    # <--- ИЗМЕНЕНО: Создаём новое уведомление с новым UID
                    launch_uid = show_progress(
                        text=t("notif_launching", version=ver, loader=loader),
                        title="Запуск",
                        progress=70
                    )

        if target_id is None:
            status = t("st_target_id_none")
            print(" target_id is None")
            is_running = False
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_critical_error"),
                success=False
            )
            return

        # ===== ПОСЛЕ УСТАНОВКИ FABRIC/FORGE - ОБНОВЛЯЕМ УВЕДОМЛЕНИЕ =====
        if loader in ["Fabric", "Forge"]:
            # Просто обновляем прогресс у существующего уведомления
            # <--- ИЗМЕНЕНО
            update_progress(
                launch_uid,
                t("notif_launching", version=ver, loader=loader),
                70
            )

        # <--- ИЗМЕНЕНО
        update_progress(
            launch_uid,
            t("notif_launching", version=ver, loader=loader),
            70
        )

        # Фикс для Forge 1.21.11
        if ver == "1.21.11" and loader == "Forge":
            set_status(t("st_forge_fix_applying"))
            versions_dir = os.path.join(GAME_DIR, "versions")
            forge_folders = [f for f in os.listdir(versions_dir) if 'forge' in f.lower() and '1.21.11' in f]
            if forge_folders:
                forge_dir = os.path.join(versions_dir, forge_folders[0])
                vanilla_dir = os.path.join(versions_dir, "1.21.11")
                vanilla_jar = os.path.join(vanilla_dir, "1.21.11.jar")
                forge_jar = os.path.join(forge_dir, f"{forge_folders[0]}.jar")
                if os.path.exists(vanilla_jar) and not os.path.exists(forge_jar):
                    shutil.copy2(vanilla_jar, forge_jar)
                    set_status(t("st_forge_fix_applied"))
                    print("    Фикс Forge 1.21.11 применён")

        # Дополнительная проверка для Fabric
        if loader == "Fabric":
            fabric_jar_path = os.path.join(GAME_DIR, "versions", target_id, f"{target_id}.jar")
            vanilla_jar_path = os.path.join(GAME_DIR, "versions", ver, f"{ver}.jar")
            if not os.path.exists(fabric_jar_path) and os.path.exists(vanilla_jar_path):
                print(f" Fabric jar отсутствует, копируем из vanilla в {fabric_jar_path}")
                os.makedirs(os.path.dirname(fabric_jar_path), exist_ok=True)
                shutil.copy2(vanilla_jar_path, fabric_jar_path)

        # ===== УПРАВЛЕНИЕ МОДАМИ =====
        # <--- ИЗМЕНЕНО
        update_progress(
            launch_uid,
            t("notif_launching", version=ver, loader=loader),
            80
        )

        mods_dir = os.path.join(GAME_DIR, "mods")
        if loader == "Fabric":
            if download_standard_mods and not delete_incompatible_mods:
                if not show_incompatible_warning():
                    status = t("st_cancelled_by_user")
                    is_running = False
                    # <--- ИЗМЕНЕНО
                    complete_progress(
                        launch_uid,
                        t("notif_cancelled_user"),
                        success=False
                    )
                    return

            if download_standard_mods:
                last_version = get_last_fabric_version()
                need_download = False

                if delete_incompatible_mods and last_version != ver:
                    print(f"  Версия Fabric изменилась: было {last_version}, стало {ver}. Очистка mods (включена).")
                    clear_mods_folder()
                    need_download = True
                elif not delete_incompatible_mods and last_version != ver:
                    print(f"  Версия Fabric изменилась: было {last_version}, стало {ver}, но удаление модов отключено.")
                    need_download = True
                else:
                    if os.path.exists(mods_dir):
                        jar_files = [f for f in os.listdir(mods_dir) if f.endswith(".jar")]
                        if len(jar_files) == 0:
                            print(" Папка mods пуста, скачиваем моды.")
                            need_download = True
                        else:
                            print(f"    Найдено {len(jar_files)} модов, пропускаем скачивание.")
                            need_download = False
                    else:
                        need_download = True

                if need_download:
                    if delete_incompatible_mods:
                        if os.path.exists(mods_dir):
                            for file in os.listdir(mods_dir):
                                if file.endswith(".jar"):
                                    try:
                                        os.remove(os.path.join(mods_dir, file))
                                        print(f"  Удалён старый мод: {file}")
                                    except:
                                        pass
                    else:
                        print("  Старые моды НЕ удалены (галочка выключена)")

                    # <--- ИЗМЕНЕНО
                    update_progress(
                        launch_uid,
                        t("notif_launching", version=ver, loader=loader),
                        85
                    )
                    set_status(t("st_mods_downloading_fabric"))
                    success = install_fabric_mods(ver, GAME_DIR, set_status)
                    if success:
                        set_status(t("st_mods_fabric_ready"))
                        set_last_fabric_version(ver)
                    else:
                        set_status(t("st_mods_install_error"))
                        print("  ОШИБКА: не удалось установить моды")
                        # <--- ИЗМЕНЕНО
                        complete_progress(
                            launch_uid,
                            "Ошибка установки модов",
                            success=False
                        )
                        return
                else:
                    set_status(t("st_mods_verified"))
            else:
                set_status(t("st_mods_disabled"))
                print("  Скачивание стандартных модов отключено пользователем")
        elif loader == "Vanilla":
            # Vanilla: моды не работают — всегда чистим
            print("  Vanilla: очистка папки mods")
            clear_mods_folder()
            if os.path.exists(LAST_FABRIC_VERSION_FILE):
                os.remove(LAST_FABRIC_VERSION_FILE)
            if os.path.exists(LAST_FORGE_VERSION_FILE):
                os.remove(LAST_FORGE_VERSION_FILE)

        elif loader == "Forge":
            last_forge = get_last_forge_version()
            if last_forge != ver:
                print(f"  Forge: версия изменилась (было {last_forge}, стало {ver})")
                if delete_incompatible_mods:
                    print("  Forge: удаление модов (чекбокс включён)")
                    clear_mods_folder()
                else:
                    print("  Forge: моды сохранены (чекбокс выключен)")
                set_last_forge_version(ver)
            else:
                print(f"  Forge: версия не изменилась ({ver}), моды не трогаем")
            if os.path.exists(LAST_FABRIC_VERSION_FILE):
                os.remove(LAST_FABRIC_VERSION_FILE)

        version_dir = os.path.join(GAME_DIR, "versions", target_id)
        if not os.path.exists(version_dir):
            status = t("st_version_folder_missing", version=target_id)
            print(f" Папка версии {target_id} не найдена")
            is_running = False
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_folder_not_found"),
                success=False
            )
            return

        if cancel_requested:
            status = t("st_cancelled")
            is_running = False
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_canceled"),
                success=False
            )
            return

        # <--- ИЗМЕНЕНО
        update_progress(
            launch_uid,
            t("notif_launching", version=ver, loader=loader),
            90
        )

        # ===== ОПРЕДЕЛЯЕМ ТРЕБУЕМУЮ JAVA =====
        if java_future:
            java_executable = java_future.result()
        else:
            java_executable = get_java_executable(ver, set_status)

        if not java_executable:
            set_status(t("st_java_suitable_not_found"))
            is_running = False
            # <--- ИЗМЕНЕНО
            complete_progress(
                launch_uid,
                t("notif_java_not_found"),
                success=False
            )
            return

        # Определяем, нужна ли Java 8 (для старых версий)
        is_java8 = False
        if ver.startswith('1.'):
            minor = int(ver.split('.')[1])
            if minor < 17:
                is_java8 = True

        cpu_count = os.cpu_count() or 4

        def is_modern_version(version_str):
            try:
                if not version_str.startswith('1.'):
                    return True
                parts = version_str.split('.')
                if len(parts) >= 2 and parts[0] == '1':
                    major = int(parts[1])
                    return major >= 17
            except:
                pass
            return False

        # ===== ЗАГРУЗКА СКИНА ELY.BY (альтернативный метод) =====
        set_status(t("st_skin_loading"))
        skin_args = force_ely_skin_download(GAME_DIR, username)
        if skin_args:
            print("    Скин Ely.by загружен (альтернативный метод)")

        # ===== УМНЫЙ АВТОВЫБОР GC С УЧЁТОМ JAVA 8 =====
        old_versions = ["1.3.2", "1.4.7", "1.5.2", "1.6.4", "1.7.10", "1.8", "1.8.8", "1.8.9"]
        cpu_count = os.cpu_count() or 4
        gc_threads = min(4, max(2, cpu_count // 2))

        # Молодая память
        if ram_gb >= 8:
            young_gen = max(2, ram_gb // 4)
        else:
            young_gen = max(1, ram_gb // 3)

        # ===== ВЫБОР GC (Java 8 не поддерживает ZGC) =====
        gc_args = ["-XX:+UseG1GC", "-XX:MaxGCPauseMillis=50"]

        if is_java8 or ver in old_versions:
            gc_args = ["-XX:+UseG1GC", "-XX:MaxGCPauseMillis=40"]
            print(f"    G1GC (Java 8 или старая версия {ver})")
        else:
            java_version = None
            if java_executable and java_executable != "java":
                try:
                    result = subprocess.run([java_executable, "-version"], capture_output=True, text=True, timeout=5, **no_window_kwargs())
                    output = result.stderr + result.stdout
                    match = re.search(r'version "?(\d+)', output)
                    if match:
                        java_version = int(match.group(1))
                except:
                    pass

            if ram_gb >= 8 and cpu_count >= 4:
                gc_args = ["-XX:+UseZGC", "-XX:ZCollectionInterval=1", "-XX:ZAllocationSpikeTolerance=2"]
                if java_version and java_version >= 21:
                    gc_args.insert(1, "-XX:+ZGenerational")
                    print(f"    ZGC Generational (Java {java_version}, {ram_gb}GB, {cpu_count} ядер)")
                else:
                    print(
                        f"    ZGC (Java {java_version if java_version else '?'}, без Generational, {ram_gb}GB, {cpu_count} ядер)")
            elif ram_gb >= 4:
                gc_args = ["-XX:+UseZGC", "-XX:ZCollectionInterval=2"]
                if java_version and java_version >= 21:
                    gc_args.insert(1, "-XX:+ZGenerational")
                    print(f"    ZGC Generational (Java {java_version}, {ram_gb}GB)")
                else:
                    print(f"    ZGC (Java {java_version if java_version else '?'}, без Generational, {ram_gb}GB)")
            else:
                gc_args = ["-XX:+UseG1GC", "-XX:MaxGCPauseMillis=50", "-XX:G1NewSizePercent=30"]
                print(f"    G1GC (слабый ПК: {ram_gb}GB)")

        # БАЗОВЫЕ ОПТИМИЗАЦИИ ДЛЯ ВСЕХ
        jvm_args = skin_args + [
            f"-Xmx{ram_gb}G",
            f"-Xms{ram_gb}G",
            f"-Xmn{young_gen}G",
            "-XX:+AlwaysPreTouch",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+ParallelRefProcEnabled",
            f"-XX:ParallelGCThreads={cpu_count}",
            f"-XX:ConcGCThreads={gc_threads}",
            "-XX:CICompilerCount=2",
            "-XX:+DisableExplicitGC",
            "-XX:+UseStringDeduplication",
            "-XX:MaxTenuringThreshold=6",
            "-XX:SurvivorRatio=8",
            "-XX:+OptimizeStringConcat",
            "-XX:+UseCompressedOops",
            "-XX:+UseCompressedClassPointers",
            "-Dfile.encoding=UTF-8",
            "-Djava.awt.headless=false",
        ] + gc_args

        # LargePages если есть права админа
        if is_admin():
            jvm_args.append("-XX:+UseLargePages")
            print("    LargePages включён")

        print(f"    RAM: {ram_gb}GB | Ядер: {cpu_count} | Young: {young_gen}GB")

        # ===== АРГУМЕНТЫ ОКНА =====
        print(f"fullscreen = {fullscreen}")

        if fullscreen:
            game_args = ["--fullscreen"]
        elif ver in old_versions:
            game_args = []
            print(f" Для версии {ver} убраны аргументы --width/--height")
        else:
            game_args = ["--width", "854", "--height", "480"]

        # ===== ELY AUTHLIB — ПОДМЕНА СТАНДАРТНОЙ AUTHLIB =====
        set_status(t("st_authlib_checking"))
        ely_authlib_version = get_ely_authlib_version(ver, GAME_DIR)
        if ely_authlib_version:
            try:
                ely_authlib_dir = os.path.join(GAME_DIR, "libraries", "by", "ely", "authlib", ely_authlib_version)
                ely_authlib_jar = os.path.join(ely_authlib_dir, f"authlib-{ely_authlib_version}.jar")
                if not os.path.exists(ely_authlib_jar):
                    os.makedirs(ely_authlib_dir, exist_ok=True)
                    url = f"https://maven.ely.by/releases/by/ely/authlib/{ely_authlib_version}/authlib-{ely_authlib_version}.jar"
                    print(f"  Скачивание ely-authlib {ely_authlib_version}...")
                    r = requests.get(url, stream=True, timeout=30)
                    if r.status_code == 200:
                        with open(ely_authlib_jar, 'wb') as f:
                            for chunk in r.iter_content(8192):
                                f.write(chunk)
                        print(f"    Ely Authlib скачан")
                    else:
                        print(f"    Ошибка скачивания ely-authlib: {r.status_code}")
                        ely_authlib_jar = None
                if ely_authlib_jar and os.path.exists(ely_authlib_jar):
                    version_json_path = os.path.join(GAME_DIR, "versions", target_id, f"{target_id}.json")
                    if os.path.exists(version_json_path):
                        with open(version_json_path, 'r', encoding='utf-8') as f:
                            version_data = json.load(f)
                        if 'libraries' in version_data:
                            version_data['libraries'] = [
                                lib for lib in version_data['libraries']

                                if not (lib.get('name', '').startswith('com.mojang:authlib')
                                        or lib.get('name', '').startswith('by.ely:authlib'))
                            ]
                        version_data['libraries'].insert(0, {
                            "name": f"by.ely:authlib:{ely_authlib_version}",
                            "url": "https://maven.ely.by/releases"
                        })
                        has_jna = any(
                            lib.get('name', '').startswith('net.java.dev.jna:jna') for lib in version_data['libraries'])
                        if not has_jna:
                            version_data['libraries'].insert(1, {"name": "net.java.dev.jna:jna:5.12.1"})
                        with open(version_json_path, 'w', encoding='utf-8') as f:
                            json.dump(version_data, f, indent=2)
                        print(f"  Ely Authlib {ely_authlib_version} добавлен в version.json для {target_id}")
            except Exception as e:
                print(f"  Ошибка при установке Ely Authlib: {e}")
                traceback.print_exc()
        else:
            print(f"  Ely Authlib не используется для версии {ver} (слишком старая или отключена)")

        options = {
            "username": username,
            "uuid": get_consistent_uuid(username),
            "token": "0",
            "jvmArguments": jvm_args,
            "gameArguments": game_args,
            "executablePath": java_executable
        }

        set_status(t("st_preparing_launch"))
        cmd = minecraft_launcher_lib.command.get_minecraft_command(target_id, GAME_DIR, options)
        print(f"Команда запуска: {' '.join(cmd)}")

        if fullscreen and "--fullscreen" not in cmd:
            cmd.append("--fullscreen")
            print("    --fullscreen добавлен принудительно")

        # ===== ЗАПУСК =====
        if os.name == 'nt':
            log_file = os.path.join(GAME_DIR, "minecraft_latest.log")
            print(f"  Лог сохраняется в: {log_file}")

            minecraft_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **no_window_kwargs()
            )

            def read_output(pipe, log_f):
                for line_bytes in pipe:
                    if cancel_requested:
                        break
                    try:
                        line = line_bytes.decode('utf-8', errors='replace').strip()
                    except:
                        line = str(line_bytes)[:200]
                    if line:
                        print(f"{line}")
                        with open(log_f, 'a', encoding='utf-8') as f:
                            f.write(f"{line}\n")

            threading.Thread(target=read_output, args=(minecraft_process.stdout, log_file), daemon=True).start()
            threading.Thread(target=read_output, args=(minecraft_process.stderr, log_file), daemon=True).start()
            threading.Thread(target=monitor_game_process, args=(minecraft_process,), daemon=True).start()

            pygame.time.wait(3000)

            if minecraft_process is None or minecraft_process.poll() is not None:  # ИСПРАВЛЕНО: монитор мог уже обнулить процесс
                print(" Игра закрылась сразу!")
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        last_lines = f.readlines()[-20:]
                        print("\n  ПОСЛЕДНИЕ 20 СТРОК ЛОГА:")
                        print("-" * 50)
                        for line in last_lines:
                            print(line.strip())
                        print("-" * 50)
                except Exception as e:
                    print(f"Не удалось прочитать лог: {e}")
                status = t("st_game_closed_instantly")
                is_running = False
                minecraft_process = None
                # <--- ИЗМЕНЕНО
                complete_progress(
                    launch_uid,
                    t("notif_game_closed"),
                    success=False
                )
            else:
                print(f"    Игра запущена, PID: {minecraft_process.pid}")
                set_status(t("st_in_game"))
                update_online_count(username, True)
                # ✅ ИГРА ЗАПУЩЕНА! - ФИНАЛЬНОЕ УВЕДОМЛЕНИЕ
                # <--- ИЗМЕНЕНО
                complete_progress(
                    launch_uid,
                    "Игра запущена",
                    success=True
                )
                # ДОПОЛНИТЕЛЬНОЕ УВЕДОМЛЕНИЕ С ПРИЯТНОЙ ИГРОЙ
                show_success(
                    text="Приятной игры! 🎮",
                    title="Успех"
                )

    except Exception as e:
        print(traceback.format_exc())
        status = t("st_error", error=str(e)[:30])
        is_running = False
        cancel_requested = False
        minecraft_process = None
        installer_process = None
        # <--- ИЗМЕНЕНО
        complete_progress(
            launch_uid,
            t("notif_critical_error"),
            success=False
        )
class LanguageSwitcher:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        # Кнопки внутри овала
        self.buttons = {
            "ru": pygame.Rect(x + 5, y + 3, 35, height - 6),
            "en": pygame.Rect(x + width - 40, y + 3, 35, height - 6)
        }
        self.anim_progress = 0
        self.target_progress = 0
        self.anim_speed = 0.15
        self.hover_ru = False
        self.hover_en = False

    def update(self, dt):
        self.target_progress = 1 if current_lang == "en" else 0
        self.anim_progress += (self.target_progress - self.anim_progress) * self.anim_speed * dt
        self.anim_progress = max(0, min(1, self.anim_progress))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()
            self.hover_ru = self.buttons["ru"].collidepoint(mx, my)
            self.hover_en = self.buttons["en"].collidepoint(mx, my)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for lang, btn_rect in self.buttons.items():
                if btn_rect.collidepoint(event.pos):
                    return lang
        return None

    def draw(self, screen):
        # Только овал! Без квадратов!
        # Фоновый овал
        pygame.draw.rect(screen, (25, 30, 25), self.rect, border_radius=40)
        pygame.draw.rect(screen, (50, 70, 50), self.rect, 1, border_radius=40)

        # Скользящий индикатор (тоже овальный)
        indicator_width = self.buttons["ru"].width
        indicator_x = self.buttons["ru"].x + self.anim_progress * (self.buttons["en"].x - self.buttons["ru"].x)
        indicator_rect = pygame.Rect(indicator_x, self.buttons["ru"].y, indicator_width, self.buttons["ru"].height)

        # Зелёный индикатор
        pygame.draw.rect(screen, (0, 200, 80), indicator_rect, border_radius=20)

        # Текст кнопок
        ru_color = (255, 255, 255) if current_lang == "ru" else (150, 150, 150)
        en_color = (255, 255, 255) if current_lang == "en" else (150, 150, 150)

        # Эффект при наведении
        if self.hover_ru and current_lang != "ru":
            ru_color = (100, 255, 100)
        if self.hover_en and current_lang != "en":
            en_color = (100, 255, 100)

        ru_text = font_small.render("RU", True, ru_color)
        en_text = font_small.render("EN", True, en_color)

        screen.blit(ru_text, (self.buttons["ru"].centerx - ru_text.get_width() // 2,
                              self.buttons["ru"].centery - ru_text.get_height() // 2))
        screen.blit(en_text, (self.buttons["en"].centerx - en_text.get_width() // 2,
                              self.buttons["en"].centery - en_text.get_height() // 2))


# ===== СИСТЕМА УВЕДОМЛЕНИЙ (ОРИГИНАЛЬНАЯ, РАБОТАЮЩАЯ) =====
class Notification:
    def __init__(self, text, title="Turbo Launcher", color=(60, 180, 60), progress=None):
        self.text = text
        self.title = title
        self.color = color
        self.progress = progress
        self.display_progress = float(progress) if progress is not None else 0.0
        self.uid = id(self)  # <--- УНИКАЛЬНЫЙ ID (гарантированно неповторимый)

        self.y_offset = -120
        self.target_y = 20
        self.speed = 9
        self.lifetime = 180
        self.closing = False
notification_queue = []


def show_notification(text, title="Turbo Launcher", color=(60, 180, 60), progress=None):
    notification_queue.append(Notification(text, title, color, progress))


# ===== УТИЛИТАРНЫЕ ФУНКЦИИ ДЛЯ ВЫЗОВОВ =====
def show_success(text, title="Успешно"):
    show_notification(text, title, color=(60, 180, 60))


def show_error(text, title="Ошибка"):
    show_notification(text, title, color=(220, 60, 60))


def show_warning(text, title="Предупреждение"):
    show_notification(text, title, color=(220, 180, 60))


def show_info(text, title="Информация"):
    show_notification(text, title, color=(60, 180, 220))


def show_progress(text, title="Прогресс", progress=0):
    """Показывает уведомление с прогресс-баром и возвращает его ID"""
    show_notification(text, title, color=(60, 180, 60), progress=progress)
    return notification_queue[-1].uid  # Возвращаем ID только что созданного уведомления


def complete_progress(uid, final_text, success=True, color=(60, 180, 60)):
    """Завершает прогресс и превращает уведомление в обычное (с таймером)"""
    for notif in notification_queue:
        if notif.uid == uid:
            notif.progress = 100  # Сначала заливаем полоску до конца (для визуала)
            notif.display_progress = 100.0
            notif.text = final_text  # Меняем текст
            notif.color = color  # Меняем цвет

            # === ГЛАВНОЕ ИЗМЕНЕНИЕ ===
            notif.progress = None  # Убираем прогресс -> превращаем в обычное уведомление
            notif.lifetime = 180  # Даём ему 3 секунды на обычном таймере

            return True
    return False

def update_progress(uid, text, progress):
    """Обновляет прогресс и текст у конкретного уведомления по его ID"""
    for notif in notification_queue:
        if notif.uid == uid:
            notif.text = text
            notif.progress = progress
            return True
    return False
import platform
import ctypes
from ctypes import wintypes


def enable_dark_titlebar_if_supported():
    """
    Включает тёмный заголовок окна на Windows 10 (1809+) и Windows 11.
    На Windows 7/8/8.1 и на Linux/Mac — ничего не делает, не падает.
    """
    # Проверяем, что это Windows
    if platform.system() != "Windows":
        return

    # Проверяем версию Windows
    # sys.getwindowsversion() возвращает (major, minor, build, platform, service_pack)
    win_ver = sys.getwindowsversion()

    # Windows 10 = major 10, build >= 17763
    # Windows 11 = major 10, build >= 22000
    # Всё, что ниже — Windows 7/8/8.1, там API не работает
    if win_ver.major < 10:
        print(f"  Windows {win_ver.major}.{win_ver.minor}: тёмный заголовок не поддерживается")
        return

    if win_ver.major == 10 and win_ver.build < 17763:
        print(f"  Windows 10 build {win_ver.build}: тёмный заголовок не поддерживается (нужен 17763+)")
        return

    # Всё ок — пробуем включить
    try:
        hwnd = pygame.display.get_wm_info()["window"]

        DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # Windows 10 1809+ / Windows 11
        value = ctypes.c_int(1)  # 1 = включить

        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(value),
            ctypes.sizeof(value)
        )

        # Fallback для старых сборок Windows 10
        if result != 0:
            DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                wintypes.DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE_OLD),
                ctypes.byref(value),
                ctypes.sizeof(value)
            )

        print(f"  Тёмный заголовок включён (Windows {win_ver.major} build {win_ver.build})")

    except Exception as e:
        # Если что-то пошло не так — просто игнорируем, окно останется светлым
        print(f"  Не удалось включить тёмный заголовок: {e}")
pygame.init()
start_discord_presence()
WIDTH, HEIGHT = 940, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.DROPFILE)

pygame.display.set_caption("Turbo Launcher")
enable_dark_titlebar_if_supported()

# Загрузка иконки с обработкой ошибок
try:
    icon_path = resource_path("turbolauncher.png")
    if os.path.exists(icon_path):
        icon = pygame.image.load(icon_path)
        pygame.display.set_icon(icon)
    else:
        from tkinter import messagebox
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Предупреждение/Warning",
            "Файл иконки не найден!\n\n"
            "Лаунчер будет работать без иконки.\n\n"
            "Icon file not found!\n"
            "Launcher will work without icon."
        )
        root.destroy()
except PermissionError:
    from tkinter import messagebox
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    result = messagebox.askyesno(
        "Ошибка запуска/Launch error",
        "Недостаточно прав для доступа к иконке.\n\n"
        "Запустить лаунчер от имени администратора или продолжить без иконки?\n\n"
        "Run as administrator or continue without icon?",
        icon='warning'
    )
    root.destroy()
    if result and platform.system() == "Windows":
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
except Exception:
    pass

checkbox_notif_rect = pygame.Rect(460, 180, 20, 20)
# Типы курсоров
CURSOR_NORMAL = pygame.SYSTEM_CURSOR_ARROW  # обычная стрелка
CURSOR_HAND = pygame.SYSTEM_CURSOR_HAND  # рука (указательный палец)
CURSOR_IBEAM = pygame.SYSTEM_CURSOR_IBEAM  # текстовый курсор (I-beam)
CURSOR_WAIT = pygame.SYSTEM_CURSOR_WAIT  # песочные часы/загрузка

def update_cursor(mx, my):
    """Обновляет вид курсора в зависимости от того, на что наведён курсор"""
    global show_dropdown, active_input, current_tab_index

    # Поле ввода ника (текстовый курсор)
    if current_tab_index == 0:
        nick_rect = pygame.Rect(40, 90, 240, 45)
        if nick_rect.collidepoint(mx, my):
            pygame.mouse.set_cursor(CURSOR_IBEAM)
            return

    # Кнопка "ИГРАТЬ/ОТМЕНА"
    play_rect = pygame.Rect(WIDTH // 2 - 110, 505, 220, 60)
    if play_rect.collidepoint(mx, my):
        pygame.mouse.set_cursor(CURSOR_HAND)
        return

    # Кнопка выбора версии
    v_btn_rect = pygame.Rect(play_rect.x - 220, 505, 210, 60)
    if v_btn_rect.collidepoint(mx, my):
        pygame.mouse.set_cursor(CURSOR_HAND)
        return

    # Кнопка выбора ядра
    l_rect = pygame.Rect(play_rect.right + 10, 505, 140, 60)
    if l_rect.collidepoint(mx, my):
        pygame.mouse.set_cursor(CURSOR_HAND)
        return

    # Кнопка-папка
    folder_rect = pygame.Rect(850, 512, 40, 40)
    if folder_rect.collidepoint(mx, my):
        pygame.mouse.set_cursor(CURSOR_HAND)
        return

    # Вкладки
    if pygame.Rect(40, 0, 150, 60).collidepoint(mx, my) or pygame.Rect(200, 0, 150, 60).collidepoint(mx, my):
        pygame.mouse.set_cursor(CURSOR_HAND)
        return

    # Переключатель языка
    if hasattr(lang_switcher, 'buttons'):
        if lang_switcher.buttons["ru"].collidepoint(mx, my) or lang_switcher.buttons["en"].collidepoint(mx, my):
            pygame.mouse.set_cursor(CURSOR_HAND)
            return

    # ===== ЧЕКБОКСЫ В НАСТРОЙКАХ (КООРДИНАТЫ ДОЛЖНЫ СОВПАДАТЬ С draw_settings_tab) =====
    if current_tab_index == 1:
        # Fullscreen (x=30, y=170)
        if 30 <= mx <= 50 and 170 <= my <= 190:
            pygame.mouse.set_cursor(CURSOR_HAND)
            return
        # Удалять несовместимые моды (x=30, y=210)
        if 30 <= mx <= 50 and 210 <= my <= 230:
            pygame.mouse.set_cursor(CURSOR_HAND)
            return
        # Скачивать стандартные моды (x=30, y=250)
        if 30 <= mx <= 50 and 250 <= my <= 270:
            pygame.mouse.set_cursor(CURSOR_HAND)
            return
        # Скрыть уведомления (x=30, y=290)
        if 30 <= mx <= 50 and 290 <= my <= 310:
            pygame.mouse.set_cursor(CURSOR_HAND)
            return

    # Ползунок RAM
    if current_tab_index == 1:
        slider_area = pygame.Rect(30, 80, 400, 60)
        if slider_area.collidepoint(mx, my):
            pygame.mouse.set_cursor(CURSOR_HAND)
            return

    # Выпадающий список версий
    if show_dropdown:
        dropdown_bg = pygame.Rect(v_btn_rect.x, v_btn_rect.y - 255, v_btn_rect.width, 250)
        if dropdown_bg.collidepoint(mx, my):
            pygame.mouse.set_cursor(CURSOR_HAND)
            return

    # По умолчанию - обычная стрелка
    pygame.mouse.set_cursor(CURSOR_NORMAL)
# Создаём переключатель языка (в правом верхнем углу)
lang_switcher = LanguageSwitcher(WIDTH - 95, 15, 85, 32)

try:
    TOTAL_RAM = int(psutil.virtual_memory().total / (1024 ** 3))
except:
    TOTAL_RAM = 8

slider_x = 70 + (ram_gb - 1) * (400 // (TOTAL_RAM - 1 if TOTAL_RAM > 1 else 1))

CLR_BG, CLR_TOPBAR, CLR_PANEL = (15, 15, 18), (25, 25, 28), (35, 35, 38)
CLR_CHECKBOX = (60, 60, 65)
CLR_ACCENT, CLR_CANCEL = (60, 180, 60), (220, 60, 60)
CLR_SCROLL_BG, CLR_SCROLL_BAR = (40, 40, 45), (80, 80, 85)
WHITE, GRAY = (245, 245, 245), (140, 140, 145)

# Пути к файлам шрифтов
TITLE_FONT_PATH = "minecraft_title_cyrillic.ttf"
TEXT_FONT_PATH = "minecraft.ttf"

try:
    font_bold = pygame.font.Font(TITLE_FONT_PATH, 24)
    font_reg = pygame.font.Font(TEXT_FONT_PATH, 19)
    font_small = pygame.font.Font(TEXT_FONT_PATH, 16)
    font_tiny = pygame.font.Font(TEXT_FONT_PATH, 12)
except FileNotFoundError as e:
    print(f" Не найден файл шрифта: {e}. Используются системные шрифты.")
    font_bold = pygame.font.SysFont("Segoe UI", 24, bold=True)
    font_reg = pygame.font.SysFont("Segoe UI", 19, bold=True)
    font_small = pygame.font.SysFont("Segoe UI", 16)
    font_tiny = pygame.font.SysFont("Segoe UI", 12)  # ДОБАВЛЕНО: в ветке except его забыли, из-за этого был NameError

glow_alpha = 0.0
glow_speed = 0.05
button_hovered = False
button_idle_pulse = 0.0
button_idle_dir = 0.02
dropdown_anim = 0.0
dropdown_anim_speed = 0.1
dropdown_target = 0
spinner_angle = 0
spinner_active = False
progress = 0.0
progress_display = 0.0   # плавно догоняет progress, чтобы нижняя полоса не прыгала
progress_active = False

# Звёзды
stars = []
for _ in range(70):
    stars.append({
        'x': random.randint(0, WIDTH),
        'y': random.randint(0, HEIGHT),
        'speed': random.uniform(0.1, 0.8),
        'size': random.randint(1, 3),
        'twinkle': random.uniform(0.5, 1.5)
    })

scroll_velocity = 0
scroll_drag = 0.9
scroll_drag_offset = 0
hover_scale = 0.0
hover_speed = 0.1

tab_texts = [t("tab_play"), t("tab_settings")]
tab_text_surfs = [font_reg.render(text, True, WHITE) for text in tab_texts]
tab_text_widths = [s.get_width() for s in tab_text_surfs]

padding = 10
tab_bar_width = 90
tab_bar_height = 3
tab_bar_y = 46

tab_centers = [40 + i * 160 + 30 + w / 2 for i, w in enumerate(tab_text_widths)]
target_positions = [center - tab_bar_width / 2 for center in tab_centers]

current_tab_index = 0
current_tab = tab_texts[current_tab_index]
tab_bar_x = target_positions[current_tab_index]
target_tab_x = tab_bar_x
tab_animation_speed = 0.1

transition_active = False
transition_progress = 0.0
transition_direction = 1
from_tab_index = 0
to_tab_index = 0
transition_speed = 0.10

content_surface_play = pygame.Surface((860, 340), pygame.SRCALPHA)
content_surface_settings = pygame.Surface((860, 340), pygame.SRCALPHA)

def draw_play_tab(surface):
    surface.fill((0, 0, 0, 0))
    pygame.draw.rect(surface, CLR_PANEL, (0, 0, 240, 45), border_radius=8)
    if active_input:
        pygame.draw.rect(surface, CLR_ACCENT, (0, 0, 240, 45), 2, border_radius=8)

    # Если поле активно — рисуем текст с курсором в правильной позиции
    pygame.draw.rect(surface, CLR_PANEL, (0, 0, 240, 45), border_radius=8)
    if active_input:
        pygame.draw.rect(surface, CLR_ACCENT, (0, 0, 240, 45), 2, border_radius=8)

    if active_input:
        # Текст ДО курсора
        if cursor_pos > 0:
            before_text = font_small.render(username[:cursor_pos], True, WHITE)
            surface.blit(before_text, (15, 12))
            cursor_x = 15 + before_text.get_width()
        else:
            cursor_x = 15

        # Мигающий курсор (вертикальная палочка)
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_surf = font_small.render("|", True, WHITE)
            surface.blit(cursor_surf, (cursor_x, 12))

        # Текст ПОСЛЕ курсора
        if cursor_pos < len(username):
            after_text = font_small.render(username[cursor_pos:], True, WHITE)
            surface.blit(after_text, (cursor_x + 5, 12))  # 5 пикселей = ширина курсора

    else:
        # Неактивен — просто показываем весь ник
        display_name = username if username else t("nickname_placeholder")
        surf_nick = font_small.render(display_name, True, WHITE)
        surface.blit(surf_nick, (15, 12))
    # Подпись "Никнейм" сверху
    surface.blit(font_small.render(t("nickname"), True, GRAY), (0, -25))

    # Основной блок
    pygame.draw.rect(surface, (30, 30, 33), (0, 60, 860, 280), border_radius=12)

    surface.blit(font_bold.render(f"Minecraft {all_versions[v_idx]}", True, WHITE), (30, 100))
    surface.blit(
        font_small.render(f"{t('loader')}: {loaders[l_idx]} | {t('ram')}: {ram_gb} {t('gb')}", True, CLR_ACCENT),
        (30, 150))
    surface.blit(font_small.render(f"{t('status')}: {status}", True, GRAY), (30, 300))

def draw_checkbox(surface, x, y, checked):
    # Рисуем фон чекбокса
    pygame.draw.rect(surface, CLR_CHECKBOX, (x, y, 20, 20), border_radius=4)
    # Если включен - рисуем галочку ПОВЕРХ фона
    # Раньше тут был blit несуществующей картинки checkbox_checked (NameError)
    if checked:
        pygame.draw.lines(surface, CLR_ACCENT, False,
                          [(x + 4, y + 10), (x + 9, y + 15), (x + 16, y + 5)], 3)


def draw_settings_tab(surface):
    surface.fill((0, 0, 0, 0))
    pygame.draw.rect(surface, (30, 30, 33), (0, 0, 860, 340), border_radius=12)

    surface.blit(font_reg.render(f"{t('ram')}: {ram_gb} {t('gb')}", True, WHITE), (30, 50))
    pygame.draw.rect(surface, CLR_PANEL, (30, 95, 400, 10), border_radius=5)
    pygame.draw.rect(surface, CLR_ACCENT, (30, 95, slider_x - 70, 10), border_radius=5)
    pygame.draw.rect(surface, WHITE, (slider_x - 50, 80, 24, 40), border_radius=6)

    surface.blit(font_small.render(f"{t('total_ram')}: {TOTAL_RAM} {t('gb')}", True, GRAY), (30, 140))

    # ===== ЧЕКБОКСЫ (ОПУЩЕНЫ НА 20px ОТ ПРЕДЫДУЩЕГО ВАРИАНТА) =====

    # Fullscreen
    y = 170  # <-- БЫЛО 150, СТАЛО 170 (опустили на 20)
    pygame.draw.rect(surface, CLR_CHECKBOX, (30, y, 20, 20), border_radius=4)
    if fullscreen:
        pygame.draw.line(surface, CLR_ACCENT, (34, y + 10), (39, y + 15), 3)
        pygame.draw.line(surface, CLR_ACCENT, (39, y + 15), (46, y + 5), 3)
    surface.blit(font_small.render(t("fullscreen"), True, WHITE), (60, y))

    # Удалять несовместимые моды
    y += 40
    pygame.draw.rect(surface, CLR_CHECKBOX, (30, y, 20, 20), border_radius=4)
    if delete_incompatible_mods:
        pygame.draw.line(surface, CLR_ACCENT, (34, y + 10), (39, y + 15), 3)
        pygame.draw.line(surface, CLR_ACCENT, (39, y + 15), (46, y + 5), 3)
    surface.blit(font_small.render(t("delete_incompatible_mods"), True, WHITE), (60, y))
    surface.blit(font_small.render(t("delete_incompatible_mods_hint"), True, GRAY), (60, y + 18))

    # Скачивать стандартные моды
    y += 40
    pygame.draw.rect(surface, CLR_CHECKBOX, (30, y, 20, 20), border_radius=4)
    if download_standard_mods:
        pygame.draw.line(surface, CLR_ACCENT, (34, y + 10), (39, y + 15), 3)
        pygame.draw.line(surface, CLR_ACCENT, (39, y + 15), (46, y + 5), 3)
    surface.blit(font_small.render(t("download_standard_mods"), True, WHITE), (60, y))
    surface.blit(font_small.render(t("download_standard_mods_hint"), True, GRAY), (60, y + 18))

    # Скрыть уведомления
    y += 40
    pygame.draw.rect(surface, CLR_CHECKBOX, (30, y, 20, 20), border_radius=4)
    if hide_notifications:
        pygame.draw.line(surface, CLR_ACCENT, (34, y + 10), (39, y + 15), 3)
        pygame.draw.line(surface, CLR_ACCENT, (39, y + 15), (46, y + 5), 3)
    surface.blit(font_small.render(t("hide_notifications"), True, WHITE), (60, y))
    surface.blit(font_small.render(t("hide_notifications_hint"), True, GRAY), (60, y + 18))

    # Версия лаунчера
    version_text = "v1.2.0"
    version_surf = font_small.render(version_text, True, (80, 80, 80))

    surface.blit(version_surf, (860 - version_surf.get_width() - 15, 340 - version_surf.get_height() - 15))
def extract_progress(status_text):
    match = re.search(r'(\d+(?:\.\d+)?)%', status_text)
    if match:
        return float(match.group(1)) / 100.0
    return None

clock = pygame.time.Clock()
running = True
scroll_target = None
scroll_speed = 0.1
active_input = False
cursor_pos = 0          # Позиция курсора внутри текста
backspace_timer = 0     # Таймер для автоповтора
backspace_delay = 300   # Задержка перед началом автоповтора (мс)
backspace_interval = 50 # Интервал между удалениями при зажатии (мс)
shift_held = False      # Для выделения текста (пока не используется)

while running:
    dt = clock.tick(144) / 16.67
    mx, my = pygame.mouse.get_pos()

    # ===== ОБНОВЛЯЕМ ВИД КУРСОРА =====
    update_cursor(mx, my)


    def is_version_installed(version_id):
        """Проверяет, установлена ли версия (существует ли папка с ней)"""
        version_dir = os.path.join(GAME_DIR, "versions", version_id)
        return os.path.isdir(version_dir)
    # Прямоугольники интерфейса
    play_rect = pygame.Rect(WIDTH // 2 - 110, 505, 220, 60)
    v_btn_rect = pygame.Rect(play_rect.x - 220, 505, 210, 60)
    l_rect = pygame.Rect(play_rect.right + 10, 505, 140, 60)
    nick_rect = pygame.Rect(40, 90, 240, 45)
    folder_rect = pygame.Rect(850, 512, 40, 40)
    dropdown_bg = pygame.Rect(v_btn_rect.x, v_btn_rect.y - 255, v_btn_rect.width, 250)
    checkbox_rect = pygame.Rect(70, 260, 20, 20)  # Fullscreen
    checkbox_delete_rect = pygame.Rect(70, 300, 20, 20)  # Удалять несовместимые моды
    checkbox_download_rect = pygame.Rect(70, 340, 20, 20)  # Скачивать стандартные моды
    checkbox_notif_rect = pygame.Rect(70, 380, 20, 20)  # Скрыть уведомления

    # Скролл дропдауна
    visible_h = 248
    total_h = len(all_versions) * ITEM_H
    max_scroll = min(0, visible_h - total_h)
    sb_area = pygame.Rect(dropdown_bg.right - 16, dropdown_bg.y + 2, 14, dropdown_bg.height - 4)
    thumb_h = max(30, int((visible_h / (total_h if total_h > 0 else 1)) * sb_area.height))
    scroll_perc = scroll_y / max_scroll if max_scroll != 0 else 0
    thumb_rect = pygame.Rect(sb_area.x, sb_area.y + (scroll_perc * (sb_area.height - thumb_h)), 14, thumb_h)

    # Обработка перетаскивания ползунка
    if dragging_scroll:
        new_thumb_y = my - scroll_drag_offset
        new_thumb_y = max(sb_area.y, min(sb_area.y + sb_area.height - thumb_h, new_thumb_y))
        new_perc = (new_thumb_y - sb_area.y) / (sb_area.height - thumb_h)
        scroll_y = max_scroll * new_perc
        scroll_target = None
    else:
        if scroll_target is not None:
            scroll_y += (scroll_target - scroll_y) * scroll_speed * dt
            if abs(scroll_target - scroll_y) < 1:
                scroll_y = scroll_target
                scroll_target = None
        else:
            scroll_y += scroll_velocity
            scroll_velocity *= scroll_drag
            scroll_y = max(max_scroll, min(0, scroll_y))

    # Ползунок RAM
    if dragging_ram and current_tab_index == 1:
        slider_x = max(70, min(mx, 470))
        ram_gb = int(1 + (slider_x - 70) / (400 // (TOTAL_RAM - 1 if TOTAL_RAM > 1 else 1)))
        save_settings()

    # Анимация переключения вкладок
    if transition_active:
        transition_progress += transition_speed * dt
        if transition_progress >= 1.0:
            transition_progress = 1.0
            transition_active = False
            current_tab_index = to_tab_index
            current_tab = tab_texts[current_tab_index]

    if transition_active:
        start_x = target_positions[from_tab_index]
        end_x = target_positions[to_tab_index]
        tab_bar_x = start_x + (end_x - start_x) * transition_progress
    else:
        tab_bar_x = target_positions[current_tab_index]

    # Анимация дропдауна
    if show_dropdown:
        dropdown_target = 1
    else:
        dropdown_target = 0

    # Плавное движение с той же скоростью, что была
    dropdown_anim += (dropdown_target - dropdown_anim) * 0.15 * dt

    # ===== ВОЛШЕБНАЯ СТРОКА =====
    # Как только мы прошли 99% пути, мгновенно прыгаем в конец (тормоз исчезает)
    if abs(dropdown_anim - dropdown_target) < 0.50 * dt:
        dropdown_anim = dropdown_target

    # Ограничиваем, чтобы не вылететь за границы
    dropdown_anim = max(0, min(1, dropdown_anim))
    # Пульсация кнопки
    if not is_running and not play_rect.collidepoint(mx, my) and not show_dropdown:
        button_idle_pulse += button_idle_dir * dt
        if button_idle_pulse > 1 or button_idle_pulse < 0:
            button_idle_dir *= -1
    else:
        button_idle_pulse = 0

    # Прогресс
    progress_val = extract_progress(status)
    progress_active = progress_val is not None
    if progress_active:
        progress = progress_val
        # Плавно догоняем цель: статус обновляется рывками, а полоса должна ехать ровно
        if progress_display < progress:
            step = max(0.0015, (progress - progress_display) * 0.06)
            progress_display = min(progress, progress_display + step)
        else:
            progress_display = progress
    else:
        progress_display = 0.0

    # Движение звёзд
    for star in stars:
        star['y'] += star['speed'] * dt
        if star['y'] > HEIGHT:
            star['y'] = 0
            star['x'] = random.randint(0, WIDTH)

    # Обновляем поверхности вкладок
    draw_play_tab(content_surface_play)
    draw_settings_tab(content_surface_settings)

    screen.fill(CLR_BG)

    # Звёзды
    for star in stars:
        twinkle = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() * 0.002 + star['x'])
        color_val = int(150 * twinkle)
        color = (color_val, color_val, color_val)
        pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), star['size'])

    # Верхняя панель с вкладками
    pygame.draw.rect(screen, CLR_TOPBAR, (0, 0, WIDTH, 60))
    for i, tab in enumerate([t("tab_play"), t("tab_settings")]):
        tx = 40 + i * 160
        t_col = WHITE if (not transition_active and ((i == 0 and current_tab == t("tab_play")) or (
                    i == 1 and current_tab == t("tab_settings")))) or pygame.Rect(tx, 0, 150, 60).collidepoint(mx,
                                                                                                               my) else GRAY
        screen.blit(tab_text_surfs[i], (tx + 30, 18))

    # Полоска под вкладкой
    pygame.draw.rect(screen, CLR_ACCENT, (tab_bar_x, tab_bar_y, tab_bar_width, tab_bar_height), border_radius=2)

    # Рисуем переключатель языка
    lang_switcher.update(dt)
    lang_switcher.draw(screen)

    # Нижняя панель
    pygame.draw.rect(screen, (22, 22, 25), (0, 480, WIDTH, 120))

    # Кнопка ИГРАТЬ/ОТМЕНА
    if play_rect.collidepoint(mx, my):
        hover_scale = min(1.0, hover_scale + hover_speed * dt)
    else:
        hover_scale = max(0.0, hover_scale - hover_speed * dt)

    if is_running:
        base_color = CLR_CANCEL
    else:
        base_color = CLR_ACCENT

    scale = 1.0 + 0.02 * button_idle_pulse + 0.08 * hover_scale
    scaled_rect = pygame.Rect(0, 0, int(play_rect.w * scale), int(play_rect.h * scale))
    scaled_rect.center = play_rect.center
    pygame.draw.rect(screen, base_color, scaled_rect, border_radius=18)
    btn_text = t("cancel") if is_running else t("play")
    btn_surf = font_bold.render(btn_text, True, WHITE)
    screen.blit(btn_surf, (scaled_rect.centerx - btn_surf.get_width() // 2,
                           scaled_rect.centery - btn_surf.get_height() // 2))

    # Прогресс-бар
    if progress_active:
        bar_y = 478
        bar_height = 4
        bar_width = int(WIDTH * progress_display)
        pygame.draw.rect(screen, CLR_PANEL, (0, bar_y, WIDTH, bar_height))
        pygame.draw.rect(screen, CLR_ACCENT, (0, bar_y, bar_width, bar_height))

    # Кнопка выбора версии
    pygame.draw.rect(screen, CLR_PANEL, v_btn_rect, border_radius=18)
    screen.blit(font_small.render(all_versions[v_idx][:18], True, WHITE), (v_btn_rect.x + 15, 523))

    # Кнопка выбора ядра
    pygame.draw.rect(screen, CLR_PANEL, l_rect, border_radius=18)
    l_txt = loaders[l_idx]
    screen.blit(font_small.render(l_txt, True, WHITE), (l_rect.centerx - font_small.size(l_txt)[0] // 2, 523))

    # Кнопка-папка
    pygame.draw.rect(screen, CLR_PANEL, folder_rect, border_radius=6)
    body_rect = pygame.Rect(folder_rect.x + 4, folder_rect.y + 6, folder_rect.w - 2, folder_rect.h - 10)
    pygame.draw.rect(screen, WHITE, body_rect, border_radius=3)
    handle_rect = pygame.Rect(folder_rect.x + 18, folder_rect.y + 2, 22, 5)
    pygame.draw.rect(screen, WHITE, handle_rect, border_radius=2)

    # Отрисовка содержимого вкладок
    if transition_active:
        offset_from = -transition_direction * (transition_progress * WIDTH)
        offset_to = transition_direction * ((1 - transition_progress) * WIDTH)
        if from_tab_index == 0:
            screen.blit(content_surface_play, (40 + offset_from, 90))
        else:
            screen.blit(content_surface_settings, (40 + offset_from, 90))
        if to_tab_index == 0:
            screen.blit(content_surface_play, (40 + offset_to, 90))
        else:
            screen.blit(content_surface_settings, (40 + offset_to, 90))
    else:
        if current_tab_index == 0:
            screen.blit(content_surface_play, (40, 90))
        else:
            screen.blit(content_surface_settings, (40, 90))

    # Подписи под кнопками
    screen.blit(font_small.render(t("version"), True, GRAY), (v_btn_rect.x, 485))
    screen.blit(font_small.render(t("loader"), True, GRAY), (l_rect.x, 485))

    # Анимированный дропдаун
    if dropdown_anim > 0:
        t_anim = dropdown_anim
        eased_t = 1 - (1 - t_anim) ** 2
        scale_drop = 0.8 + 0.2 * eased_t
        alpha = int(255 * t_anim)

        font_tiny = pygame.font.Font(TEXT_FONT_PATH, 11)  # 11 пикселей

        dropdown_surf = pygame.Surface((dropdown_bg.width, dropdown_bg.height), pygame.SRCALPHA)
        pygame.draw.rect(dropdown_surf, CLR_PANEL, (0, 0, dropdown_bg.width, dropdown_bg.height), border_radius=12)
        old_clip = dropdown_surf.get_clip()
        dropdown_surf.set_clip(pygame.Rect(0, 0, dropdown_bg.width - 18, dropdown_bg.height))
        for i, v_name in enumerate(all_versions):
            iy = 5 + (i * ITEM_H) + scroll_y
            item_r = pygame.Rect(5, iy, dropdown_bg.width - 25, ITEM_H - 4)
            if 0 - ITEM_H < iy < dropdown_bg.height:
                global_item_rect = pygame.Rect(dropdown_bg.x + 5, dropdown_bg.y + iy,
                                               dropdown_bg.width - 25, ITEM_H - 4)
                # Проверяем, установлена ли эта версия
                installed = is_version_installed(v_name)

                # Выбираем цвет:
                if installed:
                    # Если скачана — заметно светлее
                    bg_c = (82, 82, 86) if global_item_rect.collidepoint(mx, my) else (60, 60, 64)
                else:
                    # Если не скачана — стандартный тёмный фон
                    bg_c = (65, 65, 70) if global_item_rect.collidepoint(mx, my) else (45, 45, 48)
                pygame.draw.rect(dropdown_surf, bg_c, item_r, border_radius=6)
                text_surf = font_small.render(v_name, True, WHITE)
                dropdown_surf.blit(text_surf, (item_r.x + 12, item_r.y + 3))

                # Достаём название
                release_name = RELEASE_NAMES_CACHE.get(v_name, "")

                # Если названия нет (пустая строка или пробелы)
                if not release_name or release_name.strip() == "":
                    # Считаем количество точек в версии
                    if v_name.count('.') == 1:
                        release_name = "Release"  # 1 точка (например, 26.1, 1.21)
                    else:
                        release_name = "Hotfix"  # 2 и более точек (например, 26.1.1, 1.21.9)

                # Теперь всегда рисуем, потому что название точно есть
                release_surf = font_tiny.render(release_name, True, (200, 200, 200))
                dropdown_surf.blit(release_surf, (item_r.x + 12, item_r.y + 21))
        dropdown_surf.set_clip(old_clip)
        sb_local = pygame.Rect(dropdown_bg.width - 14, 2, 14, dropdown_bg.height - 4)
        pygame.draw.rect(dropdown_surf, CLR_SCROLL_BG, sb_local, border_radius=4)
        thumb_local_h = thumb_h
        thumb_local_y = 2 + (scroll_perc * (sb_local.height - thumb_local_h))
        pygame.draw.rect(dropdown_surf, CLR_SCROLL_BAR,
                         (sb_local.x, thumb_local_y, 14, thumb_local_h), border_radius=4)

        scaled_dropdown = pygame.transform.smoothscale(dropdown_surf,
                                                       (int(dropdown_bg.width * scale_drop),
                                                        int(dropdown_bg.height * scale_drop)))
        scaled_dropdown.set_alpha(alpha)
        blit_x = dropdown_bg.centerx - scaled_dropdown.get_width() // 2
        blit_y = dropdown_bg.centery - scaled_dropdown.get_height() // 2
        screen.blit(scaled_dropdown, (blit_x, blit_y))

    for event in pygame.event.get():
        if event.type == pygame.DROPFILE:
            parse_and_install_archive(event.file, GAME_DIR)
        if event.type == pygame.QUIT:
            save_settings()
            stop_discord_presence()
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEWHEEL:
            if show_dropdown:
                scroll_velocity += event.y * 20

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if notification_queue and event.button == 1:
                for i, notif in enumerate(notification_queue):
                    if notif.y_offset < -50:
                        continue
                    w, h = 280, 65
                    x = WIDTH - w - 15
                    y = notif.y_offset
                    notif_rect = pygame.Rect(x, y, w, h)
                    if notif_rect.collidepoint(event.pos):
                        notif.closing = True
            # Переключатель языка
            new_lang = lang_switcher.handle_event(event)
            if new_lang and new_lang != current_lang:
                current_lang = new_lang
                save_settings()
                # Обновляем текст вкладок
                tab_text_surfs = [font_reg.render(t("tab_play"), True, WHITE),
                                  font_reg.render(t("tab_settings"), True, WHITE)]
                tab_text_widths = [s.get_width() for s in tab_text_surfs]
                tab_centers = [40 + i * 160 + 30 + w / 2 for i, w in enumerate(tab_text_widths)]
                target_positions = [center - tab_bar_width / 2 for center in tab_centers]
                continue

            # Дропдаун
            if show_dropdown and dropdown_bg.collidepoint(event.pos):
                if sb_area.collidepoint(event.pos):
                    if thumb_rect.collidepoint(event.pos):
                        dragging_scroll = True
                        scroll_drag_offset = my - thumb_rect.y
                        scroll_target = None
                    else:
                        new_thumb_center_y = max(sb_area.y + thumb_h // 2, min(my, sb_area.bottom - thumb_h // 2))
                        new_perc = (new_thumb_center_y - sb_area.y - thumb_h / 2) / (sb_area.height - thumb_h)
                        scroll_target = max_scroll * new_perc
                else:
                    rel_y = event.pos[1] - dropdown_bg.y - 5 - scroll_y
                    idx = int(rel_y // ITEM_H)
                    if 0 <= idx < len(all_versions):
                        v_idx = idx
                        show_dropdown = False
                        save_settings()
                continue

            if show_dropdown and not v_btn_rect.collidepoint(event.pos):
                show_dropdown = False

            # Вкладки
            if pygame.Rect(40, 0, 150, 60).collidepoint(event.pos) and not transition_active:
                if current_tab_index != 0:
                    from_tab_index = current_tab_index
                    to_tab_index = 0
                    transition_direction = 1 if to_tab_index > from_tab_index else -1
                    transition_active = True
                    transition_progress = 0.0
                show_dropdown = False
                continue

            if pygame.Rect(200, 0, 150, 60).collidepoint(event.pos) and not transition_active:
                if current_tab_index != 1:
                    from_tab_index = current_tab_index
                    to_tab_index = 1
                    transition_direction = 1 if to_tab_index > from_tab_index else -1
                    transition_active = True
                    transition_progress = 0.0
                show_dropdown = False
                continue

            # Кнопка ИГРАТЬ/ОТМЕНА
            if play_rect.collidepoint(event.pos):
                if is_running:
                    cancel_requested = True
                    if installer_process:
                        installer_process.terminate()
                    if minecraft_process:
                        minecraft_process.terminate()
                    status = t("cancelling")
                else:
                    threading.Thread(target=run_launch_logic, daemon=True).start()
                continue

            # Кнопка выбора версии
            if v_btn_rect.collidepoint(event.pos):
                show_dropdown = not show_dropdown
                if not show_dropdown:
                    dropdown_anim = 0
                continue

            # Кнопка выбора ядра
            if l_rect.collidepoint(event.pos):
                l_idx = (l_idx + 1) % len(loaders)
                save_settings()
                continue

            # Кнопка-папка
            if folder_rect.collidepoint(event.pos):
                os.startfile(GAME_DIR)
                continue

            # Поле ввода ника
            if not transition_active and current_tab_index == 0:
                if nick_rect.collidepoint(event.pos):
                    active_input = True
                    # Устанавливаем курсор в место клика
                    click_x = event.pos[0] - 40  # отступ от левого края панели
                    # Ищем ближайшую позицию в тексте
                    for i in range(len(username) + 1):
                        char_width = font_small.size(username[:i])[0]
                        if click_x < 15 + char_width:
                            cursor_pos = i
                            break
                    else:
                        cursor_pos = len(username)
                else:
                    active_input = False

            # Настройки
            if not transition_active and current_tab_index == 1:
                if checkbox_rect.collidepoint(event.pos):
                    fullscreen = not fullscreen
                    save_settings()

                if checkbox_delete_rect.collidepoint(event.pos):
                    delete_incompatible_mods = not delete_incompatible_mods
                    save_settings()

                if checkbox_download_rect.collidepoint(event.pos):
                    download_standard_mods = not download_standard_mods
                    save_settings()

                if checkbox_notif_rect.collidepoint(event.pos):
                    hide_notifications = not hide_notifications
                    save_settings()

                if pygame.Rect(70, 170, 400, 60).collidepoint(event.pos):
                    dragging_ram = True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging_ram = dragging_scroll = False
                save_settings()

        if event.type == pygame.KEYDOWN and active_input and not transition_active and current_tab_index == 0:
            # Специальные клавиши
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                active_input = False
                cursor_pos = len(username)
            elif event.key == pygame.K_LEFT:
                if cursor_pos > 0:
                    cursor_pos -= 1
            elif event.key == pygame.K_RIGHT:
                if cursor_pos < len(username):
                    cursor_pos += 1
            elif event.key == pygame.K_HOME:
                cursor_pos = 0
            elif event.key == pygame.K_END:
                cursor_pos = len(username)
            elif event.key == pygame.K_BACKSPACE:
                if cursor_pos > 0:
                    username = username[:cursor_pos - 1] + username[cursor_pos:]
                    cursor_pos -= 1
                backspace_timer = pygame.time.get_ticks()  # Сбрасываем таймер для автоповтора
            elif event.key == pygame.K_DELETE:
                if cursor_pos < len(username):
                    username = username[:cursor_pos] + username[cursor_pos + 1:]
            else:
                # Обычные символы
                if len(username) < 16 and event.unicode.isprintable():
                    username = username[:cursor_pos] + event.unicode + username[cursor_pos:]
                    cursor_pos += 1
            save_settings()

    if active_input and pygame.key.get_pressed()[pygame.K_BACKSPACE]:
        now = pygame.time.get_ticks()
        if now - backspace_timer > backspace_delay:
            if cursor_pos > 0:
                username = username[:cursor_pos-1] + username[cursor_pos:]
                cursor_pos -= 1
                save_settings()
            backspace_timer = now - (backspace_delay - backspace_interval)  # Сброс с учётом интервала
    # ===== ОТРИСОВКА УВЕДОМЛЕНИЙ =====
    if notification_queue:
        for i, notif in enumerate(notification_queue):
            # Таймер для обычных уведомлений
            if notif.progress is None:
                if notif.lifetime > 0:
                    notif.lifetime -= 1
                if notif.lifetime <= 0:
                    notif.closing = True
            else:
                # Плавное движение полосы: обновления из потоков приходят пачками
                target = float(notif.progress)
                if notif.display_progress < target:
                    step = max(0.4, (target - notif.display_progress) * 0.12)
                    notif.display_progress = min(target, notif.display_progress + step)
                else:
                    notif.display_progress = target

            if i == 0:
                notif.target_y = 20
            else:
                prev_notif = notification_queue[i - 1]
                notif.target_y = prev_notif.y_offset + 70

            # Анимация движения (в обе стороны)
            if notif.y_offset < notif.target_y and not notif.closing:
                notif.y_offset += notif.speed
                if notif.y_offset > notif.target_y:
                    notif.y_offset = notif.target_y
            elif notif.y_offset > notif.target_y and not notif.closing:
                notif.y_offset -= notif.speed
                if notif.y_offset < notif.target_y:
                    notif.y_offset = notif.target_y

            # Если закрывается — едет вверх
            if notif.closing:
                notif.y_offset -= notif.speed * 1.2
                if notif.y_offset < -130:
                    notification_queue.pop(i)
                    # Пересчитываем цели сразу
                    for j in range(len(notification_queue)):
                        if j == 0:
                            notification_queue[j].target_y = 20
                        else:
                            prev = notification_queue[j - 1]
                            notification_queue[j].target_y = prev.y_offset + 70
                    break

        # Отрисовка
        for notif in notification_queue:
            if notif.y_offset < -100:
                continue

            w, h = 280, 65
            x = WIDTH - w - 15
            y = notif.y_offset

            surf = pygame.Surface((w, h), pygame.SRCALPHA)

            # Умеренное закругление (14 пикселей)
            pygame.draw.rect(surf, (10, 10, 10, 255), (0, 0, w, h), border_radius=14)

            display_title = notif.title
            if len(display_title) > 20:
                display_title = display_title[:20] + "..."
            title_surf = font_small.render(display_title, True, (255, 255, 255))
            surf.blit(title_surf, (12, 8))

            display_text = notif.text
            if len(display_text) > 20:
                display_text = display_text[:20] + "..."
            text_surf = font_tiny.render(display_text, True, (180, 180, 180))
            surf.blit(text_surf, (12, 32))

            # Полоска внизу — теперь внутри (с отступами!)
            bar_y = h - 6
            bar_h = 2
            bar_x = 12
            bar_w = w - 24
            if notif.progress is not None:
                fill = int(bar_w * (notif.display_progress / 100.0))
            else:
                fill = int(bar_w * (notif.lifetime / 180))
            if fill > 0:
                pygame.draw.rect(surf, (*notif.color, 255), (bar_x, bar_y, fill, bar_h))

            screen.blit(surf, (x, y))
    pygame.display.flip()
    clock.tick(120)
