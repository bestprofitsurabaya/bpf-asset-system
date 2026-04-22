"""
BPF Asset Management System - Main Entry Point
"""

import streamlit as st
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.helpers import init_session_state, get_logo_base64
from src.database.engine import DatabaseEngine
from src.auth.user_manager import UserManager

# Import pages
from pages.login import show_login_page
from pages.executive_dashboard import show_executive_dashboard
from pages.ai_dashboard import show_ai_dashboard
from pages.ac_layout import show_ac_layout
from pages.user_management import show_user_management


def main():
    """Main application entry point"""
    
    # Page configuration
    st.set_page_config(
        page_title="BPF Asset Management System",
        page_icon="A",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_page()
        return
    
    # Main application UI
    st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    
    [data-testid="stSidebar"] { 
        background: linear-gradient(135deg, #003366 0%, #002244 100%);
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stMarkdown p {
        color: white !important;
    }
    
    .stButton>button { 
        background: linear-gradient(135deg, #CC0000 0%, #990000 100%);
        color: white; 
        border-radius: 8px;
        border: none;
    }
    
    .db-mode-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.9);
    }
    
    .db-mode-demo { color: #ff6b6b; border: 2px solid #ff6b6b; }
    .db-mode-real { color: #51cf66; border: 2px solid #51cf66; }
    </style>
    """, unsafe_allow_html=True)
    
    # Database mode indicator
    mode = st.session_state.get('db_mode', 'real')
    mode_color = "demo" if mode == 'demo' else "real"
    st.markdown(f"""
    <div class="db-mode-indicator db-mode-{mode_color}">
        Database: {mode.upper()}
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Logo
        static_dir = Path(__file__).parent / 'static'
        logo_base64 = get_logo_base64(static_dir)
        
        if logo_base64:
            st.markdown(f"""
            <div style="text-align:center; padding:10px 0;">
                <img src="data:image/png;base64,{logo_base64}" style="max-width:180px; width:100%;">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding:20px 0; background:linear-gradient(135deg, #003366 0%, #CC0000 100%); border-radius:10px;">
                <h2 style="color:white; margin:0;">BPF</h2>
                <p style="color:#FFD700; margin:0;">BESTPROFIT FUTURES</p>
                <p style="color:white; margin:5px 0 0 0; font-size:12px;">Asset Management System</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # User info
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.1); padding:10px; border-radius:8px; margin-bottom:20px;">
            <p style="margin:0; color:white;">User: {st.session_state.username}</p>
            <p style="margin:0; color:#aaa; font-size:0.9em;">Role: {st.session_state.user_role}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Database mode selector (admin only)
        if st.session_state.user_role == 'admin':
            st.markdown("### System Settings")
            new_mode = st.selectbox(
                "Database Mode",
                ['real', 'demo'],
                index=0 if mode == 'real' else 1
            )
            if new_mode != mode:
                st.session_state.db_mode = new_mode
                db_engine = DatabaseEngine()
                if new_mode == 'demo':
                    db_engine.initialize_demo_database()
                else:
                    db_engine.initialize_real_database()
                st.rerun()
            st.markdown("---")
        
        # Navigation menu
        menu_options = [
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
        ]
        
        # Add User Management for admin
        if st.session_state.get('user_permissions', {}).get('manage_users', False):
            menu_options.append("User Management")
        
        menu = st.selectbox("PILIH MODUL", menu_options)
        st.session_state.current_page = menu
        
        st.markdown("---")
        
        if mode == 'demo':
            st.warning("DEMO MODE - Data dummy")
        else:
            st.success("PRODUCTION MODE")
        
        st.markdown("---")
        
        if st.button("Logout", use_container_width=True):
            # Log session
            config_dir = Path(__file__).parent / 'config'
            user_manager = UserManager(config_dir)
            user_manager.log_session(st.session_state.username, 'logout')
            
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Route to selected page
    if menu == "Executive Dashboard":
        show_executive_dashboard()
    elif menu == "AI Dashboard":
        show_ai_dashboard()
    elif menu == "Layout AC Interactive":
        show_ac_layout()
    elif menu == "User Management":
        show_user_management()
    else:
        # Placeholder for other pages
        st.title(menu)
        st.info(f"Halaman {menu} sedang dalam pengembangan.")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="text-align:center; color:white; font-size:0.8em;">
        <p>BPF Asset Management System v4.0</p>
        <p>(C) 2024 PT BESTPROFIT FUTURES</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()