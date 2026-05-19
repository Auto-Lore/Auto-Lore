import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "autolore")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
memories_collection = db["memories"]
