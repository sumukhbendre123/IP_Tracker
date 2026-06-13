from flask import Flask, render_template_string
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Database setup
DB_FILE = 'visitor_ips.db'

def init_database():
    """Create database and table if they don't exist"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_client_ip():
    """Get the client's IP address"""
    if app.environ_base.get('REMOTE_ADDR'):
        return app.environ_base.get('REMOTE_ADDR')
    return '127.0.0.1'

def store_ip(ip_address):
    """Store IP address in database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO visitors (ip_address) VALUES (?)', (ip_address,))
    conn.commit()
    conn.close()

def get_all_visitors():
    """Retrieve all stored IP addresses"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT ip_address, timestamp FROM visitors ORDER BY timestamp DESC LIMIT 100')
    visitors = cursor.fetchall()
    conn.close()
    return visitors

@app.route('/')
def home():
    """Main page - captures IP and displays it"""
    # Get client IP from Flask's request object
    from flask import request
    client_ip = request.remote_addr

    # Store IP in database
    store_ip(client_ip)

    # Get all visitors
    visitors = get_all_visitors()
    visitor_count = len(visitors)

    # Get unique IP count
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM visitors')
    unique_ips = cursor.fetchone()[0]
    conn.close()

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
    from flask import request

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM visitors')
    total_visits = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM visitors')
    unique_ips = cursor.fetchone()[0]

    cursor.execute('SELECT ip_address, COUNT(*) as count FROM visitors GROUP BY ip_address ORDER BY count DESC LIMIT 10')
    top_ips = cursor.fetchall()

    conn.close()

    return json.dumps({
        'total_visits': total_visits,
        'unique_ips': unique_ips,
        'your_ip': request.remote_addr,
        'top_ips': [{'ip': ip, 'visits': count} for ip, count in top_ips]
    }, indent=2)

if __name__ == '__main__':
    # Initialize database
    init_database()

    print("=" * 50)
    print("🚀 IP Tracker Server Starting...")
    print("=" * 50)
    print(f"Database file: {os.path.abspath(DB_FILE)}")

    # Get port from environment variable (Replit sets this) or use 5000 for local
    port = int(os.environ.get('PORT', 5000))

    print(f"Server running on port {port}")
    print("Main page: http://localhost:5000/ (or your Replit URL)")
    print("Stats API: http://localhost:5000/stats")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    # Run Flask server - Replit compatible
    app.run(host='0.0.0.0', port=port, debug=False)
