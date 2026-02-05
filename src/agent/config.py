import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://coffee_admin:coffee_password@localhost:5440/coffee_shop")

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is missing!")
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing!")

config = Config()
