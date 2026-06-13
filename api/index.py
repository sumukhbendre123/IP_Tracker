from flask import Flask, render_template_string, request
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from .env file (for local testing)
load_dotenv()

app = Flask(__name__)

# MongoDB Atlas connection with proper URL encoding
MONGO_URI = os.environ.get('MONGODB_URI')

# If MONGODB_URI contains special chars that aren't encoded, encode them
if MONGO_URI and 'mongodb+srv://' in MONGO_URI:
    # Don't modify if already set as full URI
    pass
else:
    # Fallback for local development
    MONGO_URI = 'mongodb://localhost:27017'

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

try:
    client.admin.command('ismaster')
    db = client['ip_tracker']
    visitors_collection = db['visitors']
    # Create index for faster queries
    visitors_collection.create_index([('timestamp', -1)])
    print("✅ MongoDB connected successfully")
except ServerSelectionTimeoutError:
    print("⚠️ MongoDB connection failed - ensure MONGODB_URI is set")

def init_database():
    """Initialize database (MongoDB doesn't require explicit initialization)"""
    try:
        visitors_collection.create_index([('timestamp', -1)])
    except:
        pass

def store_ip(ip_address):
    """Store IP address in database"""
    try:
        visitors_collection.insert_one({
            'ip_address': ip_address,
            'timestamp': datetime.utcnow()
        })
    except Exception as e:
        print(f"Error storing IP: {e}")

def get_all_visitors():
    """Retrieve all stored IP addresses"""
    try:
        visitors = list(visitors_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(100))
        return [(v['ip_address'], v['timestamp'].strftime('%Y-%m-%d %H:%M:%S')) for v in visitors]
    except Exception as e:
        print(f"Error fetching visitors: {e}")
        return []

@app.route('/')
def home():
    """Main page - captures IP and displays it"""
    init_database()

    # Get client IP from request, handle proxies
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    # Store IP in database
    store_ip(client_ip)

    # Get all visitors
    visitors = get_all_visitors()
    visitor_count = len(visitors)

    # Get unique IP count
    try:
        unique_ips = visitors_collection.distinct('ip_address').__len__()
    except:
        unique_ips = 0

    # HTML template
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>IP Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .info { background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>🌐 IP Address Tracker</h1>

        <div class="info">
            <h2>Your Information</h2>
            <p><strong>Your IP Address:</strong> {{ client_ip }}</p>
            <p><strong>Event Time:</strong> {{ current_time }}</p>
        </div>

        <div class="info">
            <h2>Statistics</h2>
            <p><strong>Total Visits:</strong> {{ visitor_count }}</p>
            <p><strong>Unique IPs:</strong> {{ unique_ips }}</p>
        </div>

        <h2>Recent Visitors (Last 100)</h2>
        <table>
            <tr>
                <th>IP Address</th>
                <th>Timestamp</th>
            </tr>
            {% for visitor in visitors %}
            <tr>
                <td>{{ visitor[0] }}</td>
                <td>{{ visitor[1] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''

    return render_template_string(
        html,
        client_ip=client_ip,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        visitor_count=visitor_count,
        unique_ips=unique_ips,
        visitors=visitors
    )

@app.route('/stats')
def stats():
    """API endpoint to get stats as JSON"""
    import json

    try:
        total_visits = visitors_collection.count_documents({})
        unique_ips = len(visitors_collection.distinct('ip_address'))

        # Get top IPs
        pipeline = [
            {'$group': {'_id': '$ip_address', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        top_ips = list(visitors_collection.aggregate(pipeline))

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return json.dumps({
            'error': 'Database connection failed',
            'total_visits': 0,
            'unique_ips': 0,
            'your_ip': request.remote_addr,
            'top_ips': []
        }, indent=2)

    # Get client IP
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    return json.dumps({
        'total_visits': total_visits,
        'unique_ips': unique_ips,
        'your_ip': client_ip,
        'top_ips': [{'ip': ip['_id'], 'visits': ip['count']} for ip in top_ips]
    }, indent=2)

if __name__ == '__main__':
    init_database()
    print("=" * 50)
    print("🚀 IP Tracker Server Starting...")
    print("=" * 50)
    print(f"Database file: {os.path.abspath(DB_FILE)}")
    port = int(os.environ.get('PORT', 5000))
    print(f"Server running on port {port}")
    print("Main page: http://localhost:5000/")
    print("Stats API: http://localhost:5000/stats")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
