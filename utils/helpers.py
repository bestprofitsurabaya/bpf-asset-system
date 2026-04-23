"""
Helper Functions
"""

import hashlib
import base64
import json
import os
from pathlib import Path
from datetime import datetime
from config.settings import STATIC_DIR, CONFIG_DIR, DEFAULT_USERS


def load_users():
    """Load users from environment variable or config file"""
    users_json = os.environ.get('BPF_USERS')
    if users_json:
        try:
            return json.loads(users_json)
        except:
            pass
    return DEFAULT_USERS


def verify_password(username, password):
    """Verify username and password"""
    users = load_users()
    
    if not username or not password:
        return False, "Mohon isi username dan password"
    
    if username not in users:
        return False, "Username tidak ditemukan"
    
    hashed_input = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    if hashed_input == users[username]["password"]:
        return True, "Login berhasil"
    else:
        return False, "Password salah"


def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def get_logo_base64():
    """Convert logo to base64 for embedding"""
    logo_path = STATIC_DIR / 'logo.png'
    if logo_path.exists():
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None


def get_favicon_path():
    """Get favicon path"""
    favicon_path = STATIC_DIR / 'favicon.ico'
    if favicon_path.exists():
        return str(favicon_path)
    return None


def load_ac_layout_config():
    """Load AC layout configuration"""
    config_path = CONFIG_DIR / 'ac_layout_config.json'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Default config
    return {
        "indoor": {
            "background": "static/layout_indoor.jpg",
            "width": 1000,
            "height": 700,
            "ac_units": []
        },
        "outdoor": {
            "ac_units": []
        }
    }


def format_currency(amount):
    """Format currency to readable string"""
    if amount >= 1_000_000_000:
        return f"Rp {amount/1_000_000_000:.2f} M"
    elif amount >= 1_000_000:
        return f"Rp {amount/1_000_000:.1f} Jt"
    elif amount > 0:
        return f"Rp {amount:,.0f}"
    else:
        return "Rp 0"


def format_date(date_val, format='%d %b %Y'):
    """Format date safely"""
    if date_val is None:
        return ''
    
    if isinstance(date_val, str):
        try:
            date_val = datetime.strptime(date_val, '%Y-%m-%d')
        except:
            return date_val
    
    if hasattr(date_val, 'strftime'):
        return date_val.strftime(format)
    
    return str(date_val)


def get_health_status_color(health_score):
    """Get color based on health score"""
    if health_score >= 80:
        return '#28a745', 'Good'
    elif health_score >= 60:
        return '#ffc107', 'Warning'
    elif health_score >= 40:
        return '#fd7e14', 'Critical'
    else:
        return '#dc3545', 'Severe'


def get_priority_order(priority):
    """Get numeric order for priority"""
    order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Normal': 3}
    return order.get(priority, 4)