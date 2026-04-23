"""
Authentication Module
"""

import streamlit as st
from utils.helpers import verify_password, load_users
import database.models as db_models
import database.seed as db_seed


def init_database(mode='real'):
    """Initialize database based on mode"""
    try:
        db_models.create_db(mode=mode)
        if mode == 'real':
            db_seed.init_bpf_assets(mode=mode)
            db_seed.init_vehicle_components(mode=mode)
            db_seed.init_sample_vehicles(mode=mode)
        else:
            db_seed.init_bpf_assets(mode=mode)
            db_seed.init_vehicle_components(mode=mode)
            db_seed.init_sample_vehicles(mode=mode)
            db_seed.generate_dummy_ac_logs(logs_per_asset=100, mode=mode)
            db_seed.generate_dummy_vehicle_services(services_per_vehicle=50, mode=mode)
            db_seed.generate_dummy_vehicles(count=15, mode=mode)
        return True
    except Exception as e:
        st.error(f"Gagal menginisialisasi database: {e}")
        return False


def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    if "password" in st.session_state:
        del st.session_state["password"]


def render_login_page():
    """Render login page"""
    st.title("BPF Asset Management System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Silakan Login")
        
        with st.form("login_form"):
            username_input = st.text_input("Username", placeholder="Masukkan username")
            password_input = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_submitted = st.form_submit_button("Login", use_container_width=True)
            with col_btn2:
                demo_submitted = st.form_submit_button("Demo Mode", use_container_width=True)
            
            if login_submitted:
                success, message = verify_password(username_input, password_input)
                if success:
                    users = load_users()
                    st.session_state.authenticated = True
                    st.session_state.user_role = users[username_input]["role"]
                    st.session_state.username = username_input
                    st.session_state.db_mode = 'real'
                    init_database('real')
                    st.rerun()
                else:
                    st.error(message)
            
            if demo_submitted:
                st.session_state.authenticated = True
                st.session_state.user_role = "viewer"
                st.session_state.username = "demo"
                st.session_state.db_mode = 'demo'
                init_database('demo')
                st.rerun()
    
    st.markdown("---")
    with st.expander("Default Credentials (Klik untuk lihat)"):
        st.markdown("""
        **Gunakan kredensial berikut untuk login:**
        
        | Username | Password | Role |
        |----------|----------|------|
        | admin | admin123 | Administrator |
        | teknisi | teknisi123 | Teknisi |
        | manager | manager123 | Manager |
        | demo | demo123 | Viewer |
        """)