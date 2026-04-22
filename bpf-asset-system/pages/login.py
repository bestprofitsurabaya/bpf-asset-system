"""
Login Page Module
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.user_manager import UserManager
from src.database.engine import DatabaseEngine
from src.utils.helpers import init_session_state

def show_login_page():
    """Display login page"""
    
    # Custom CSS for login page
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 40px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .login-header h1 {
        color: #003366;
        margin: 0;
        font-size: 28px;
    }
    
    .login-header p {
        color: #666;
        margin: 5px 0 0 0;
    }
    
    .login-footer {
        text-align: center;
        margin-top: 20px;
        color: #999;
        font-size: 12px;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #003366 0%, #002244 100%);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #002244 0%, #001122 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .demo-button > button {
        background: linear-gradient(135deg, #CC0000 0%, #990000 100%);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-header">
            <h1>BPF</h1>
            <p>Asset Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize user manager
        config_dir = Path(__file__).parent.parent / 'config'
        user_manager = UserManager(config_dir)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Masukkan username",
                key="login_username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Masukkan password",
                key="login_password"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                login_submitted = st.form_submit_button(
                    "Login",
                    use_container_width=True
                )
            
            with col_btn2:
                demo_submitted = st.form_submit_button(
                    "Demo Mode",
                    use_container_width=True
                )
            
            if login_submitted:
                if username and password:
                    success, message, user_info = user_manager.authenticate(username, password)
                    
                    if success:
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_role = user_info['role']
                        st.session_state.user_full_name = user_info['full_name']
                        st.session_state.user_permissions = user_info['permissions']
                        st.session_state.db_mode = 'real'
                        
                        # Log session
                        user_manager.log_session(username, 'login')
                        
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Mohon isi username dan password")
            
            if demo_submitted:
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.session_state.user_role = "viewer"
                st.session_state.user_full_name = "Demo User"
                st.session_state.user_permissions = {
                    "view_dashboard": True,
                    "manage_assets": False,
                    "manage_vehicles": False,
                    "input_maintenance": False,
                    "edit_delete_data": False,
                    "manage_users": False,
                    "view_analytics": True,
                    "print_reports": True
                }
                st.session_state.db_mode = 'demo'
                
                # Initialize demo database
                db_engine = DatabaseEngine()
                db_engine.initialize_demo_database()
                
                st.rerun()
        
        # Default credentials info
        with st.expander("Default Credentials", expanded=False):
            st.markdown("""
            **Gunakan kredensial berikut:**
            
            | Username | Password | Role |
            |----------|----------|------|
            | admin | admin123 | Administrator |
            | teknisi | teknisi123 | Teknisi |
            | manager | manager123 | Manager |
            | demo | demo123 | Viewer |
            """)
        
        st.markdown("""
        <div class="login-footer">
            PT BESTPROFIT FUTURES SURABAYA<br>
            Version 4.0.0
        </div>
        """, unsafe_allow_html=True)