Working:

1.Bot Token Setup: The script uses python-telegram-bot (telegram.ext.Application) with your configured token (BOT_TOKEN = "...").

2.Available Telegram Commands: Once the script runs, open Telegram, message your bot, and use any of these commands:

  - /start or /help: Lists all available commands and usage.
  - /sendlogs: Sends all captured keylog .txt files from ~/.keylogger_logs/ as documents.
  - /screenshots: Sends all saved screenshot .png images from ~/.keylogger_logs/ as photos.
  - /take_screenshot: Instantly captures a live screenshot of the active screen and sends it immediately to your Telegram chat.
  - /all: Sends both keylog text files and screenshots in sequence.
  - /info: Sends full system details (LAN/Global IP, OS, Architecture, Hostname).
3.Built-in Protections:

 - Skips empty files to prevent BadRequest: File is empty API crashes.
 - Includes exception handling per file so one failed file doesn't block the rest.
 - Uses send_photo for images (.png) and send_document for keylog files (.txt)
