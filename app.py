"""
BPF Asset Management System - Main Entry Point
"""

import streamlit as st
import logging
from datetime import datetime

# Import modules
from modules.auth import render_login_page, logout, init_database
from modules.dashboard_executive import render_executive_dashboard
from modules.dashboard_ac import render_ac_dashboard
from modules.analytics import render_interactive_analytics
from modules.layout_ac import render_layout_ac
from modules.manage_ac import render_manage_ac
from modules.manage_vehicles import render_manage_vehicles
from modules.input_ac import render_input_ac
from modules.input_vehicle import render_input_vehicle
from modules.dashboard_vehicle import render_vehicle_dashboard
from modules.recommendations import render_recommendations
from modules.reports import render_analytics_reports
from modules.edit_data import render_edit_data
from modules.print_reports import render_print_reports

from utils.helpers import get_logo_base64, get_favicon_path
from utils.alerts import check_alerts_and_notify
from config.settings import APP_NAME, APP_VERSION, APP_COMPANY, COLORS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session state initialization
if 'db_mode' not in st.session_state:
    st.session_state.db_mode = 'real'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Initialize database
if not init_database(st.session_state.db_mode):
    st.stop()

# Page configuration
favicon_path = get_favicon_path()
page_config = {
    "page_title": APP_NAME,
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
if favicon_path:
    page_config["page_icon"] = favicon_path
else:
    page_config["page_icon"] = "A"

st.set_page_config(**page_config)

# CSS Styles
st.markdown(f"""
    <style>
    .main {{ background-color: {COLORS['light']}; }}
    
    [data-testid="stSidebar"] {{ 
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['dark']} 100%);
    }}
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] p {{
        color: white !important;
    }}
    
    .stButton>button {{ 
        background: linear-gradient(135deg, {COLORS['secondary']} 0%, #990000 100%);
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        border: none;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{ 
        background: linear-gradient(135deg, #990000 0%, #660000 100%);
        transform: translateY(-2px);
    }}
    
    .db-mode-indicator {{
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.9);
    }}
    
    .db-mode-demo {{ color: #ff6b6b; border: 2px solid #ff6b6b; }}
    .db-mode-real {{ color: #51cf66; border: 2px solid #51cf66; }}
    </style>
""", unsafe_allow_html=True)

# Login check
if not st.session_state.authenticated:
    render_login_page()
    st.stop()

# Main Application
mode_color = "demo" if st.session_state.db_mode == 'demo' else "real"
st.markdown(f"""
    <div class="db-mode-indicator db-mode-{mode_color}">
        Database: {st.session_state.db_mode.upper()}
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    logo_base64 = get_logo_base64()
    if logo_base64:
        st.markdown(f"""
        <div style="text-align:center; padding:10px 0;">
            <img src="data:image/png;base64,{logo_base64}" style="max-width:180px; width:100%;">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center; padding:20px 0; background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%); border-radius: 10px;">
            <h2 style="color:white; margin:0;">BPF</h2>
            <p style="color:#FFD700; margin:0;">BESTPROFIT FUTURES</p>
            <p style="color:white; margin:5px 0 0 0; font-size:12px;">Asset Management System</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 20px;">
        <p style="margin: 0; color: white;">User: {st.session_state.username}</p>
        <p style="margin: 0; color: #aaa; font-size: 0.9em;">Role: {st.session_state.user_role}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Alerts
    alerts = check_alerts_and_notify()
    if alerts:
        st.markdown("### Notifikasi")
        for alert in alerts[:5]:
            if alert['type'] == 'critical':
                st.error(f"**{alert['asset_id']}** - {alert['message']}")
            elif alert['type'] == 'warning':
                st.warning(f"**{alert['asset_id']}** - {alert['message']}")
        st.markdown("---")
    
    # System Settings (Admin only)
    if st.session_state.user_role == 'admin':
        st.markdown("### System Settings")
        new_mode = st.selectbox("Database Mode", ['real', 'demo'], 
                                index=0 if st.session_state.db_mode == 'real' else 1)
        if new_mode != st.session_state.db_mode:
            st.session_state.db_mode = new_mode
            init_database(new_mode)
            st.rerun()
        st.markdown("---")
    
    # Navigation Menu
    menu = st.selectbox("PILIH MODUL", [
        "Executive Dashboard",
        "AI Dashboard",
        "Interactive Analytics",
        "Layout AC Interactive",
        "Manage Master Aset AC",
        "Input Log SOW AC",
        "Manage Kendaraan",
        "Input Servis Kendaraan",
        "Dashboard Kendaraan",
        "Maintenance Recommendations",
        "Analytics & Reports",
        "Edit/Hapus Data",
        "Cetak Laporan"
    ])
    
    st.markdown("---")
    
    if st.session_state.db_mode == 'demo':
        st.warning("DEMO MODE - Data dummy.")
    else:
        st.success("PRODUCTION MODE - Database real.")
    
    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()

# Route to selected module
if menu == "Executive Dashboard":
    render_executive_dashboard()
elif menu == "AI Dashboard":
    render_ac_dashboard()
elif menu == "Interactive Analytics":
    render_interactive_analytics()
elif menu == "Layout AC Interactive":
    render_layout_ac()
elif menu == "Manage Master Aset AC":
    render_manage_ac()
elif menu == "Input Log SOW AC":
    render_input_ac()
elif menu == "Manage Kendaraan":
    render_manage_vehicles()
elif menu == "Input Servis Kendaraan":
    render_input_vehicle()
elif menu == "Dashboard Kendaraan":
    render_vehicle_dashboard()
elif menu == "Maintenance Recommendations":
    render_recommendations()
elif menu == "Analytics & Reports":
    render_analytics_reports()
elif menu == "Edit/Hapus Data":
    render_edit_data()
elif menu == "Cetak Laporan":
    render_print_reports()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="text-align:center; color:white; font-size:0.8em;">
    <p>{APP_NAME} v{APP_VERSION}</p>
    <p>(C) 2024 {APP_COMPANY}</p>
    <p>Mode: {st.session_state.db_mode.upper()}</p>
</div>
""", unsafe_allow_html=True)