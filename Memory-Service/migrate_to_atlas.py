"""
Migrate all memories from local MongoDB to Atlas.
Run once: python migrate_to_atlas.py
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).parent / ".env")

LOCAL_URI = "mongodb://localhost:27017"
ATLAS_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "autolore")

if not ATLAS_URI or "localhost" in ATLAS_URI:
    raise SystemExit("ERROR: Set a real Atlas MONGO_URI in your .env file first.")

local_col = MongoClient(LOCAL_URI)[DB_NAME]["memories"]
atlas_col = MongoClient(ATLAS_URI)[DB_NAME]["memories"]

docs = list(local_col.find())
if not docs:
    print("No local memories found — nothing to migrate.")
else:
    existing_ids = set(str(d["_id"]) for d in atlas_col.find({}, {"_id": 1}))
    to_insert = [d for d in docs if str(d["_id"]) not in existing_ids]

    if not to_insert:
        print(f"All {len(docs)} memories already exist in Atlas — nothing to do.")
    else:
        result = atlas_col.insert_many(to_insert)
        print(f"Migrated {len(result.inserted_ids)} memories to Atlas ({len(docs) - len(to_insert)} already existed).")
