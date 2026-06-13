#!/usr/bin/env python
"""
View MongoDB Atlas data locally
"""

from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.environ.get('MONGODB_URI')

if not MONGO_URI:
    print("[ERROR] MONGODB_URI not found in .env file")
    print("Please add your MongoDB connection string to .env file")
    exit(1)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    print("[SUCCESS] Connected to MongoDB Atlas successfully!\n")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

# Access database and collection
db = client['ip_tracker']
visitors_collection = db['visitors']

# Get statistics
total_visits = visitors_collection.count_documents({})
unique_ips = len(visitors_collection.distinct('ip_address'))

print("=" * 70)
print("[STATS] IP TRACKER DATABASE STATISTICS")
print("=" * 70)
print(f"Total Visits: {total_visits}")
print(f"Unique IP Addresses: {unique_ips}")
print("=" * 70 + "\n")

# Get top IPs
print("[TOP] TOP 10 MOST VISITED IPs:")
print("-" * 70)
pipeline = [
    {'$group': {'_id': '$ip_address', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 10}
]
top_ips = list(visitors_collection.aggregate(pipeline))

if top_ips:
    print(f"{'IP Address':<20} | {'Visit Count':<15}")
    print("-" * 70)
    for ip in top_ips:
        print(f"{ip['_id']:<20} | {ip['count']:<15}")
else:
    print("No data yet")

print("\n")

# Get all visitors
print("[RECORDS] ALL VISITOR RECORDS (Last 50):")
print("-" * 70)
visitors = list(visitors_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(50))

if visitors:
    print(f"{'#':<5} | {'IP Address':<20} | {'Timestamp':<20}")
    print("-" * 70)
    for idx, visitor in enumerate(visitors, 1):
        timestamp = visitor['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{idx:<5} | {visitor['ip_address']:<20} | {timestamp:<20}")
else:
    print("No visitor records found")

print("\n" + "=" * 70)
print("[COMPLETE] Database view complete!")
print("=" * 70)

# Menu for more options
print("\nOptions:")
print("1. View raw MongoDB data (first 20)")
print("2. Export data to CSV")
print("3. Delete all records")
print("4. Exit")

choice = input("\nEnter your choice (1-4): ").strip()

if choice == "1":
    print("\n[DATA] Raw MongoDB Documents (First 20):")
    print("-" * 70)
    for idx, visitor in enumerate(visitors_collection.find({}).limit(20), 1):
        print(f"\n{idx}. IP: {visitor['ip_address']}, Timestamp: {visitor['timestamp']}")

elif choice == "2":
    import csv
    filename = "ip_tracker_export.csv"
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['ip_address', 'timestamp'])
            writer.writeheader()
            for visitor in visitors_collection.find({}, {'_id': 0}).sort('timestamp', -1):
                visitor_copy = visitor.copy()
                visitor_copy['timestamp'] = visitor_copy['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow(visitor_copy)
        print(f"[SUCCESS] Data exported to {filename}")
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")

elif choice == "3":
    confirm = input("[WARNING] Are you sure you want to delete ALL records? (yes/no): ").strip().lower()
    if confirm == "yes":
        result = visitors_collection.delete_many({})
        print(f"[SUCCESS] Deleted {result.deleted_count} records")
    else:
        print("[INFO] Deletion cancelled")

else:
    print("[INFO] Exiting...")

client.close()

