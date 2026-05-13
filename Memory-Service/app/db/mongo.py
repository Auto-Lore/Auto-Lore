import os

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "autolore")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
memories_collection = db["memories"]
