"""
Helper functions used throughout the application
"""

import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def get_logo_base64(static_dir: Path) -> str:
    """Convert logo to base64 for embedding"""
    logo_path = static_dir / 'logo.png'
    if logo_path.exists():
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

def format_currency(amount: float) -> str:
    """Format currency to readable string"""
    if amount >= 1_000_000_000:
        return f"Rp {amount/1_000_000_000:.2f} M"
    elif amount >= 1_000_000:
        return f"Rp {amount/1_000_000:.1f} Jt"
    elif amount > 0:
        return f"Rp {amount:,.0f}"
    else:
        return "Rp 0"

def format_date(date_obj, format_str: str = '%d %b %Y') -> str:
    """Format date object to string"""
    if date_obj is None:
        return ''
    if isinstance(date_obj, str):
        try:
            date_obj = pd.to_datetime(date_obj)
        except:
            return date_obj
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime(format_str)
    return str(date_obj)

def get_health_color(health_score: float) -> str:
    """Get color based on health score"""
    if health_score >= 80:
        return "#28a745"
    elif health_score >= 60:
        return "#ffc107"
    elif health_score >= 40:
        return "#fd7e14"
    else:
        return "#dc3545"

def get_health_status(health_score: float) -> str:
    """Get status text based on health score"""
    if health_score >= 80:
        return "Good"
    elif health_score >= 60:
        return "Warning"
    elif health_score >= 40:
        return "Critical"
    else:
        return "Severe"

def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    emoji_map = {
        'Good': 'GREEN',
        'Warning': 'YELLOW',
        'Critical': 'ORANGE',
        'Severe': 'RED',
        'Normal': 'GREEN',
        'Abnormal': 'RED'
    }
    return emoji_map.get(status, 'WHITE')

def calculate_delta_t(temp_ret: float, temp_sup: float) -> float:
    """Calculate Delta T"""
    return temp_ret - temp_sup if temp_ret > temp_sup else 0

def calculate_health_score(delta_t: float, amp: float, drain: str, low_p: float) -> int:
    """Calculate health score based on parameters"""
    health_score = 100
    
    # Delta T scoring
    if delta_t >= 12:
        health_score -= 0
    elif delta_t >= 10:
        health_score -= 10
    elif delta_t >= 8:
        health_score -= 20
    elif delta_t >= 6:
        health_score -= 35
    else:
        health_score -= 50
    
    # Ampere scoring
    if amp > 25:
        health_score -= 20
    elif amp > 20:
        health_score -= 10
    elif amp > 15:
        health_score -= 5
    
    # Drainage scoring
    if drain != "Lancar":
        health_score -= 15
    
    # Pressure scoring
    if low_p < 130 or low_p > 150:
        health_score -= 10
    
    return max(0, min(100, health_score))

def load_json_file(filepath: Path) -> dict:
    """Load JSON file"""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json_file(filepath: Path, data: dict) -> bool:
    """Save JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")
        return False

def init_session_state():
    """Initialize session state variables"""
    if 'db_mode' not in st.session_state:
        st.session_state.db_mode = 'real'
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_permissions' not in st.session_state:
        st.session_state.user_permissions = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Executive Dashboard"