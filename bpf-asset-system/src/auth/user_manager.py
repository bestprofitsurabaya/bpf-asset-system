"""
User management module
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st

from src.utils.helpers import hash_password, verify_password, save_json_file, load_json_file
from src.utils.constants import ROLE_ADMIN, ROLE_TEKNISI, ROLE_MANAGER, ROLE_VIEWER, PERMISSIONS

logger = logging.getLogger(__name__)

class UserManager:
    """User management class"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.users_file = config_dir / 'users.json'
        self.sessions_file = config_dir / 'sessions.json'
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Ensure config files exist with default data"""
        if not self.users_file.exists():
            default_users = {
                "admin": {
                    "password": hash_password("admin123"),
                    "role": ROLE_ADMIN,
                    "full_name": "Administrator",
                    "email": "admin@bestprofit.co.id",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "is_active": True
                },
                "teknisi": {
                    "password": hash_password("teknisi123"),
                    "role": ROLE_TEKNISI,
                    "full_name": "Teknisi Maintenance",
                    "email": "teknisi@bestprofit.co.id",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "is_active": True
                },
                "manager": {
                    "password": hash_password("manager123"),
                    "role": ROLE_MANAGER,
                    "full_name": "Manager Operasional",
                    "email": "manager@bestprofit.co.id",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "is_active": True
                },
                "demo": {
                    "password": hash_password("demo123"),
                    "role": ROLE_VIEWER,
                    "full_name": "Demo User",
                    "email": "demo@bestprofit.co.id",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "is_active": True
                }
            }
            save_json_file(self.users_file, default_users)
        
        if not self.sessions_file.exists():
            save_json_file(self.sessions_file, {"active_sessions": []})
    
    def load_users(self) -> Dict:
        """Load all users"""
        return load_json_file(self.users_file)
    
    def save_users(self, users: Dict) -> bool:
        """Save users to file"""
        return save_json_file(self.users_file, users)
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user"""
        users = self.load_users()
        
        if not username or not password:
            return False, "Mohon isi username dan password", None
        
        if username not in users:
            return False, "Username tidak ditemukan", None
        
        user_data = users[username]
        
        if not user_data.get('is_active', True):
            return False, "Akun tidak aktif. Hubungi administrator.", None
        
        if verify_password(password, user_data['password']):
            # Update last login
            user_data['last_login'] = datetime.now().isoformat()
            users[username] = user_data
            self.save_users(users)
            
            # Set permissions
            permissions = PERMISSIONS.get(user_data['role'], {})
            
            return True, "Login berhasil", {
                'username': username,
                'role': user_data['role'],
                'full_name': user_data.get('full_name', username),
                'email': user_data.get('email', ''),
                'permissions': permissions
            }
        else:
            return False, "Password salah", None
    
    def create_user(self, username: str, password: str, role: str, 
                   full_name: str = "", email: str = "") -> Tuple[bool, str]:
        """Create new user"""
        users = self.load_users()
        
        if username in users:
            return False, f"Username '{username}' sudah digunakan"
        
        if role not in [ROLE_ADMIN, ROLE_TEKNISI, ROLE_MANAGER, ROLE_VIEWER]:
            return False, f"Role '{role}' tidak valid"
        
        users[username] = {
            "password": hash_password(password),
            "role": role,
            "full_name": full_name or username,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        
        if self.save_users(users):
            logger.info(f"User '{username}' created successfully")
            return True, f"User '{username}' berhasil dibuat"
        else:
            return False, "Gagal menyimpan data user"
    
    def update_user(self, username: str, updates: Dict) -> Tuple[bool, str]:
        """Update user data"""
        users = self.load_users()
        
        if username not in users:
            return False, f"User '{username}' tidak ditemukan"
        
        # Don't allow changing username
        updates.pop('username', None)
        
        # Handle password update separately
        if 'password' in updates and updates['password']:
            updates['password'] = hash_password(updates['password'])
        elif 'password' in updates:
            del updates['password']
        
        # Update user data
        users[username].update(updates)
        
        if self.save_users(users):
            logger.info(f"User '{username}' updated successfully")
            return True, f"User '{username}' berhasil diupdate"
        else:
            return False, "Gagal menyimpan data user"
    
    def delete_user(self, username: str) -> Tuple[bool, str]:
        """Delete user"""
        users = self.load_users()
        
        if username not in users:
            return False, f"User '{username}' tidak ditemukan"
        
        # Prevent deleting the last admin
        if users[username]['role'] == ROLE_ADMIN:
            admin_count = sum(1 for u in users.values() if u['role'] == ROLE_ADMIN and u.get('is_active', True))
            if admin_count <= 1:
                return False, "Tidak dapat menghapus admin terakhir"
        
        del users[username]
        
        if self.save_users(users):
            logger.info(f"User '{username}' deleted successfully")
            return True, f"User '{username}' berhasil dihapus"
        else:
            return False, "Gagal menghapus user"
    
    def toggle_user_status(self, username: str) -> Tuple[bool, str]:
        """Toggle user active status"""
        users = self.load_users()
        
        if username not in users:
            return False, f"User '{username}' tidak ditemukan"
        
        # Prevent deactivating the last admin
        if users[username]['role'] == ROLE_ADMIN:
            admin_count = sum(1 for u in users.values() if u['role'] == ROLE_ADMIN and u.get('is_active', True))
            if admin_count <= 1 and users[username].get('is_active', True):
                return False, "Tidak dapat menonaktifkan admin terakhir"
        
        current_status = users[username].get('is_active', True)
        users[username]['is_active'] = not current_status
        
        if self.save_users(users):
            status_text = "diaktifkan" if not current_status else "dinonaktifkan"
            logger.info(f"User '{username}' {status_text}")
            return True, f"User '{username}' berhasil {status_text}"
        else:
            return False, "Gagal mengubah status user"
    
    def get_all_users(self) -> pd.DataFrame:
        """Get all users as DataFrame"""
        users = self.load_users()
        
        data = []
        for username, user_data in users.items():
            data.append({
                'Username': username,
                'Full Name': user_data.get('full_name', username),
                'Role': user_data.get('role', 'Unknown'),
                'Email': user_data.get('email', ''),
                'Status': 'Active' if user_data.get('is_active', True) else 'Inactive',
                'Last Login': user_data.get('last_login', 'Never'),
                'Created At': user_data.get('created_at', 'Unknown')
            })
        
        return pd.DataFrame(data)
    
    def get_user_count(self) -> Dict:
        """Get user statistics"""
        users = self.load_users()
        
        stats = {
            'total': len(users),
            'active': sum(1 for u in users.values() if u.get('is_active', True)),
            'inactive': sum(1 for u in users.values() if not u.get('is_active', True)),
            'by_role': {}
        }
        
        for role in [ROLE_ADMIN, ROLE_TEKNISI, ROLE_MANAGER, ROLE_VIEWER]:
            stats['by_role'][role] = sum(1 for u in users.values() if u['role'] == role)
        
        return stats
    
    def reset_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password"""
        return self.update_user(username, {'password': new_password})
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change password with old password verification"""
        users = self.load_users()
        
        if username not in users:
            return False, f"User '{username}' tidak ditemukan"
        
        if not verify_password(old_password, users[username]['password']):
            return False, "Password lama salah"
        
        return self.update_user(username, {'password': new_password})
    
    def log_session(self, username: str, action: str, ip_address: str = "", user_agent: str = ""):
        """Log user session activity"""
        try:
            sessions = load_json_file(self.sessions_file)
            
            session_entry = {
                'username': username,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            sessions['active_sessions'].append(session_entry)
            
            # Keep only last 1000 sessions
            if len(sessions['active_sessions']) > 1000:
                sessions['active_sessions'] = sessions['active_sessions'][-1000:]
            
            save_json_file(self.sessions_file, sessions)
        except Exception as e:
            logger.error(f"Error logging session: {e}")
    
    def get_recent_sessions(self, limit: int = 50) -> List[Dict]:
        """Get recent session logs"""
        sessions = load_json_file(self.sessions_file)
        return sessions.get('active_sessions', [])[-limit:][::-1]