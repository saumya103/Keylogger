# Keylogger 
Python-based keylogger and system monitoring utility with Telegram Bot integration for remote management. It captures keystrokes, tracks active window titles, captures screenshots, gathers system hardware/network information, and streams logged data back to a specified Telegram bot.

# Features:
## 1.  Keystroke Monitoring
   - Real-time Key Capture: Logs both alphanumeric characters and special functional keys (e.g., [ENTER], [SPACE], [SHIFT], [CTRL], [ALT]).
  -  Hotkey Toggle: Pause and resume logging at any time by pressing F9.
## 2. Active Window Context
  - App & Window Title Tracking: Attaches the active application name/window title to logged keys so keystrokes can be correlated with specific programs or websites.
  - Cross-Platform Window Detection: Supports Linux (xdotool), Windows (win32gui), and macOS (AppKit).
## 3. Screenshot Capture
  - Initial Capture: Automatically captures initial screenshots upon script launch.
  - Live On-Demand Screenshots: Instantly captures and uploads a live screenshot upon receiving a command from Telegram.
## 4. System & Network Reconnaissance
 - Hardware & OS Details: Gathers OS release/version, CPU architecture, hostname, and processor info.
-  Network Identification: Retrieves both local IP, MAC address, and public/global IP address via ipify API.
##  5. Telegram Bot Control Commands
 - /start / /help – Display menu of commands.
 - /sendlogs – Upload non-empty .txt keylog files to Telegram.
 - /screenshots – Upload stored screenshots to Telegram.
 - /take_screenshot – Trigger and send a live screenshot.
 - /info – Return formatted system specs and network information.
 - /all – Retrieve all logs and screenshots at once.
## 6. Log Management & Safety
- Size-based Rotation: Prevents oversized log files by automatically rotating to a new .txt file when reaching the 5 MB size limit.
- Isolated Log Storage: Stores logs cleanly inside the user's home directory (~/.keylogger_logs/).
- Threaded Execution: Keylogger runs on a background daemon thread while the Telegram bot operates on the main thread without blocking performance.

# Workflow:

## 1. Bot Token Setup: 
  The script uses python-telegram-bot (telegram.ext.Application) with your configured token (BOT_TOKEN = "...").

## 2. Available Telegram Commands: 
  Once the script runs, open Telegram, message your bot, and use any of these commands:

  - /start or /help: Lists all available commands and usage.
  - /sendlogs: Sends all captured keylog .txt files from ~/.keylogger_logs/ as documents.
  - /screenshots: Sends all saved screenshot .png images from ~/.keylogger_logs/ as photos.
  - /take_screenshot: Instantly captures a live screenshot of the active screen and sends it immediately to your Telegram chat.
  - /all: Sends both keylog text files and screenshots in sequence.
  - /info: Sends full system details (LAN/Global IP, OS, Architecture, Hostname).
    
## 3.Built-in Protections:

 - Skips empty files to prevent BadRequest: File is empty API crashes.
 - Includes exception handling per file so one failed file doesn't block the rest.
 - Uses send_photo for images (.png) and send_document for keylog files (.txt)
