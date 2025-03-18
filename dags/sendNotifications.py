import requests
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telegram_log.log", encoding="utf-8")
    ]
)

class fileSender:
    def __init__(self, bot_token, chat_id, csv_file):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.csv_file = csv_file
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"

    def check_file_exists(self):
        if not os.path.exists(self.csv_file):
            logging.error(f"File {self.csv_file} not found.")
            return False
        logging.info(f"File {self.csv_file} found.")
        return True

    def send_file(self):
        if not self.check_file_exists():
            return

        try:
            with open(self.csv_file, 'rb') as file:
                files = {'document': (self.csv_file, file)}
                payload = {
                    "chat_id": self.chat_id,
                    "caption": f"Data scraped on {self.get_current_date()}"  # Caption tùy chọn
                }
                response = requests.post(self.base_url, data=payload, files=files)
                response.raise_for_status()
                logging.info(f"Successfully sent {self.csv_file} to Telegram.")
        except requests.RequestException as e:
            logging.error(f"Failed to send file to Telegram: {e}")
        except Exception as e:
            logging.error(f"Error opening file {self.csv_file}: {e}")

    def get_current_date(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    sender = fileSender(bot_token=BOT_TOKEN, chat_id=CHAT_ID, csv_file="raw.csv")
    sender.send_file()