"""
User Management Page
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.user_manager import UserManager
from src.utils.constants import ROLE_ADMIN, ROLE_TEKNISI, ROLE_MANAGER, ROLE_VIEWER


def show_user_management():
    """Display user management page"""
    
    st.title("User Management")
    st.markdown("Kelola pengguna dan hak akses sistem")
    
    # Initialize user manager
    config_dir = Path(__file__).parent.parent / 'config'
    user_manager = UserManager(config_dir)
    
    # Check permissions
    if not st.session_state.get('user_permissions', {}).get('manage_users', False):
        st.error("Anda tidak memiliki akses ke halaman ini.")
        st.stop()
    
    # Tabs
    tab_list, tab_add, tab_profile, tab_sessions = st.tabs([
        "Daftar Pengguna",
        "Tambah Pengguna",
        "Profil Saya",
        "Session Log"
    ])
    
    with tab_list:
        st.subheader("Daftar Pengguna Terdaftar")
        
        # Statistics
        stats = user_manager.get_user_count()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pengguna", stats['total'])
        with col2:
            st.metric("Pengguna Aktif", stats['active'])
        with col3:
            st.metric("Pengguna Nonaktif", stats['inactive'])
        with col4:
            st.metric("Administrator", stats['by_role'].get(ROLE_ADMIN, 0))
        
        st.markdown("---")
        
        # Users table
        users_df = user_manager.get_all_users()
        
        if not users_df.empty:
            st.dataframe(
                users_df,
                column_config={
                    'Username': 'Username',
                    'Full Name': 'Nama Lengkap',
                    'Role': 'Role',
                    'Email': 'Email',
                    'Status': 'Status',
                    'Last Login': 'Login Terakhir',
                    'Created At': 'Dibuat Pada'
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Quick actions
            st.markdown("---")
            st.subheader("Quick Actions")
            
            selected_user = st.selectbox(
                "Pilih Pengguna",
                users_df['Username'].tolist(),
                key="quick_action_user"
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Toggle Status", use_container_width=True):
                    success, message = user_manager.toggle_user_status(selected_user)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                if st.button("Reset Password", use_container_width=True):
                    st.session_state.show_reset_modal = True
                    st.session_state.reset_user = selected_user
            
            with col3:
                if st.button("Hapus Pengguna", use_container_width=True, type="secondary"):
                    if selected_user == st.session_state.username:
                        st.error("Tidak dapat menghapus akun sendiri")
                    else:
                        success, message = user_manager.delete_user(selected_user)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            # Reset password modal
            if st.session_state.get('show_reset_modal', False):
                st.markdown("---")
                st.subheader(f"Reset Password: {st.session_state.reset_user}")
                
                new_password = st.text_input("Password Baru", type="password")
                confirm_password = st.text_input("Konfirmasi Password", type="password")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Simpan"):
                        if new_password != confirm_password:
                            st.error("Password tidak cocok")
                        elif len(new_password) < 6:
                            st.error("Password minimal 6 karakter")
                        else:
                            success, message = user_manager.reset_password(
                                st.session_state.reset_user, new_password
                            )
                            if success:
                                st.success(message)
                                st.session_state.show_reset_modal = False
                                st.rerun()
                            else:
                                st.error(message)
                
                with col2:
                    if st.button("Batal"):
                        st.session_state.show_reset_modal = False
                        st.rerun()
    
    with tab_add:
        st.subheader("Tambah Pengguna Baru")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username*", placeholder="min. 4 karakter")
                password = st.text_input("Password*", type="password", placeholder="min. 6 karakter")
                confirm_password = st.text_input("Konfirmasi Password*", type="password")
            
            with col2:
                full_name = st.text_input("Nama Lengkap", placeholder="Opsional")
                email = st.text_input("Email", placeholder="opsional@email.com")
                role = st.selectbox(
                    "Role*",
                    [ROLE_ADMIN, ROLE_TEKNISI, ROLE_MANAGER, ROLE_VIEWER],
                    format_func=lambda x: {
                        ROLE_ADMIN: "Administrator",
                        ROLE_MANAGER: "Manager",
                        ROLE_TEKNISI: "Teknisi",
                        ROLE_VIEWER: "Viewer"
                    }.get(x, x)
                )
            
            submitted = st.form_submit_button("Tambah Pengguna", use_container_width=True)
            
            if submitted:
                errors = []
                if not username or len(username) < 4:
                    errors.append("Username minimal 4 karakter")
                if not password or len(password) < 6:
                    errors.append("Password minimal 6 karakter")
                if password != confirm_password:
                    errors.append("Password tidak cocok")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    success, message = user_manager.create_user(
                        username, password, role, full_name, email
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab_profile:
        st.subheader("Profil Saya")
        
        users = user_manager.load_users()
        user_data = users.get(st.session_state.username, {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Username:** {st.session_state.username}
            
            **Nama Lengkap:** {user_data.get('full_name', '-')}
            
            **Role:** {user_data.get('role', '-')}
            
            **Email:** {user_data.get('email', '-')}
            
            **Status:** {'Aktif' if user_data.get('is_active', True) else 'Nonaktif'}
            
            **Login Terakhir:** {user_data.get('last_login', 'Belum pernah')}
            """)
        
        with col2:
            st.markdown("### Ubah Password")
            
            with st.form("change_password_form"):
                old_password = st.text_input("Password Lama", type="password")
                new_password = st.text_input("Password Baru", type="password")
                confirm_password = st.text_input("Konfirmasi Password Baru", type="password")
                
                submitted = st.form_submit_button("Ubah Password", use_container_width=True)
                
                if submitted:
                    if not old_password or not new_password or not confirm_password:
                        st.error("Semua field harus diisi")
                    elif new_password != confirm_password:
                        st.error("Password baru tidak cocok")
                    elif len(new_password) < 6:
                        st.error("Password minimal 6 karakter")
                    else:
                        success, message = user_manager.change_password(
                            st.session_state.username, old_password, new_password
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
    
    with tab_sessions:
        st.subheader("Log Aktivitas Pengguna")
        
        sessions = user_manager.get_recent_sessions(100)
        
        if sessions:
            sessions_df = pd.DataFrame(sessions)
            if 'timestamp' in sessions_df.columns:
                sessions_df['timestamp'] = pd.to_datetime(sessions_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            st.dataframe(
                sessions_df,
                column_config={
                    'username': 'Username',
                    'action': 'Aksi',
                    'timestamp': 'Waktu',
                    'ip_address': 'IP Address'
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Belum ada log aktivitas")