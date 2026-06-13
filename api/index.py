from flask import Flask, render_template_string, request
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from .env file (for local testing)
load_dotenv()

app = Flask(__name__)

# MongoDB Atlas connection with proper URL encoding
MONGO_URI = os.environ.get('MONGODB_URI')

print(f"[DEBUG] MONGO_URI from env: {MONGO_URI[:50] if MONGO_URI else 'NOT SET'}...")

# If MONGODB_URI contains special chars that aren't encoded, encode them
if not MONGO_URI:
    print("[ERROR] MONGODB_URI environment variable is not set!")
    MONGO_URI = 'mongodb://localhost:27017'
    print("[INFO] Falling back to localhost")

if MONGO_URI and 'mongodb+srv://' in MONGO_URI:
    # Don't modify if already set as full URI
    pass

# Initialize collection as None
db = None
visitors_collection = None

try:
    print(f"[INFO] Attempting MongoDB connection...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    db = client['ip_tracker']
    visitors_collection = db['visitors']
    # Create index for faster queries
    visitors_collection.create_index([('timestamp', -1)])
    print("[SUCCESS] MongoDB connected successfully")
except ServerSelectionTimeoutError as e:
    print(f"[ERROR] MongoDB connection timeout: {e}")
except Exception as e:
    print(f"[ERROR] MongoDB connection failed: {e}")

def init_database():
    """Initialize database (MongoDB doesn't require explicit initialization)"""
    if visitors_collection is None:
        return False
    try:
        visitors_collection.create_index([('timestamp', -1)])
        return True
    except Exception as e:
        print(f"[ERROR] init_database failed: {e}")
        return False

def store_ip(ip_address):
    """Store IP address in database"""
    if visitors_collection is None:
        print("[ERROR] Cannot store IP - MongoDB not connected")
        return False
    try:
        visitors_collection.insert_one({
            'ip_address': ip_address,
            'timestamp': datetime.utcnow()
        })
        return True
    except Exception as e:
        print(f"[ERROR] Error storing IP: {e}")
        return False

def get_all_visitors():
    """Retrieve all stored IP addresses"""
    if visitors_collection is None:
        print("[ERROR] Cannot get visitors - MongoDB not connected")
        return []
    try:
        visitors = list(visitors_collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(100))
        return [(v['ip_address'], v['timestamp'].strftime('%Y-%m-%d %H:%M:%S')) for v in visitors]
    except Exception as e:
        print(f"[ERROR] Error fetching visitors: {e}")
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
    if visitors_collection is None:
        unique_ips = 0
    else:
        try:
            unique_ips = len(visitors_collection.distinct('ip_address'))
        except:
            unique_ips = 0

    # HTML template - Scary Hacked Theme
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WARNING: ACCOUNT COMPROMISED</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Courier+Prime&display=swap');

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Courier Prime', monospace;
                background: #0a0a0a;
                color: #ff0000;
                background-image:
                    repeating-linear-gradient(
                        0deg,
                        rgba(255, 0, 0, 0.03),
                        rgba(255, 0, 0, 0.03) 1px,
                        transparent 1px,
                        transparent 2px
                    );
                animation: flicker 0.15s infinite;
                padding: 20px;
                overflow-x: hidden;
            }

            @keyframes flicker {
                0% { opacity: 0.97; }
                50% { opacity: 1; }
                100% { opacity: 0.97; }
            }

            @keyframes blink {
                0%, 49% { opacity: 1; }
                50%, 100% { opacity: 0; }
            }

            @keyframes glitch {
                0% { transform: translate(0); }
                20% { transform: translate(-2px, 2px); }
                40% { transform: translate(-2px, -2px); }
                60% { transform: translate(2px, 2px); }
                80% { transform: translate(2px, -2px); }
                100% { transform: translate(0); }
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
            }

            header {
                text-align: center;
                margin-bottom: 30px;
                border: 3px solid #ff0000;
                padding: 20px;
                background: rgba(255, 0, 0, 0.1);
                animation: glitch 0.3s infinite;
            }

            .warning {
                font-size: 48px;
                font-weight: bold;
                animation: blink 0.7s infinite;
                text-shadow: 0 0 10px #ff0000;
            }

            .warning-text {
                font-size: 14px;
                margin-top: 10px;
                color: #ff3333;
            }

            .alert-box {
                background: #1a0000;
                border: 2px solid #ff0000;
                border-radius: 0;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 0 20px rgba(255, 0, 0, 0.5), inset 0 0 10px rgba(255, 0, 0, 0.2);
            }

            .alert-title {
                font-size: 20px;
                font-weight: bold;
                color: #ff3333;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }

            .alert-content {
                color: #ffaaaa;
                line-height: 1.6;
                font-size: 14px;
            }

            .threat-level {
                display: inline-block;
                background: #ff0000;
                color: #000000;
                padding: 10px 20px;
                font-weight: bold;
                margin: 10px 0;
                animation: blink 1s infinite;
                text-transform: uppercase;
            }

            .hack-info {
                background: #0d0d0d;
                border-left: 5px solid #ff0000;
                padding: 15px;
                margin: 15px 0;
                font-size: 13px;
            }

            .hack-info strong {
                color: #ff3333;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }

            th {
                background: #330000;
                color: #ff0000;
                padding: 12px;
                text-align: left;
                border: 1px solid #ff0000;
                font-weight: bold;
                text-transform: uppercase;
            }

            td {
                padding: 10px;
                border: 1px solid #330000;
                background: #0a0a0a;
                color: #ffaaaa;
                font-family: 'Courier Prime', monospace;
                font-size: 12px;
            }

            tr:hover td {
                background: #2a0000;
                color: #ff3333;
            }

            .access-log {
                background: #1a0000;
                border: 1px solid #ff0000;
                padding: 15px;
                margin-top: 20px;
                max-height: 300px;
                overflow-y: auto;
            }

            .log-entry {
                color: #ff9999;
                font-size: 11px;
                margin: 5px 0;
                font-family: 'Courier Prime', monospace;
            }

            .severity-critical {
                color: #ff0000;
            }

            .severity-high {
                color: #ff3333;
            }

            footer {
                text-align: center;
                margin-top: 40px;
                color: #666666;
                font-size: 12px;
                border-top: 1px solid #333333;
                padding-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="warning">WARNING!</div>
                <div class="warning-text">YOUR ACCOUNT HAS BEEN COMPROMISED</div>
            </header>

            <div class="alert-box">
                <div class="alert-title">CRITICAL SECURITY ALERT</div>
                <div class="threat-level">THREAT LEVEL: CRITICAL</div>
                <div class="alert-content">
                    Your account access has been detected and logged. A new connection from your IP address has been identified in our security system.
                </div>
            </div>

            <div class="alert-box">
                <div class="alert-title">INTRUDER INFORMATION</div>
                <div class="hack-info">
                    <strong>Detection Timestamp:</strong> {{ current_time }}<br>
                    <strong>Intruder IP Address:</strong> {{ client_ip }}<br>
                    <strong>Access Method:</strong> Direct Web Connection<br>
                    <strong>Session Status:</strong> ACTIVE THREAT
                </div>
            </div>

            <div class="alert-box">
                <div class="alert-title">SECURITY STATISTICS</div>
                <div class="hack-info">
                    <strong>Total Unauthorized Access Attempts:</strong> <span style="color: #ff3333;">{{ visitor_count }}</span><br>
                    <strong>Unique Intruder IPs Detected:</strong> <span style="color: #ff3333;">{{ unique_ips }}</span><br>
                    <strong>System Status:</strong> <span style="color: #ff0000;">COMPROMISED</span>
                </div>
            </div>

            <div class="alert-box">
                <div class="alert-title">INTRUSION LOG - RECENT ACCESS DETECTED</div>
                <table>
                    <thead>
                        <tr>
                            <th>INTRUDER IP</th>
                            <th>ACCESS TIME</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if visitors %}
                        {% for visitor in visitors %}
                        <tr>
                            <td class="severity-high">{{ visitor[0] }}</td>
                            <td class="severity-critical">{{ visitor[1] }}</td>
                        </tr>
                        {% endfor %}
                        {% else %}
                        <tr>
                            <td colspan="2">Analyzing system logs...</td>
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>

            <footer>
                [SECURITY SYSTEM ALERT] - All unauthorized access attempts are being logged and monitored
            </footer>
        </div>
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

    if visitors_collection is None:
        return json.dumps({
            'error': 'MongoDB not connected',
            'total_visits': 0,
            'unique_ips': 0,
            'your_ip': request.remote_addr,
            'top_ips': []
        }, indent=2)

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
        print(f"[ERROR] Error fetching stats: {e}")
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
