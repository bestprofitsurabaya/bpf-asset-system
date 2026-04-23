"""
Konfigurasi Aplikasi BPF Asset Management System
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / 'static'
STATIC_DIR.mkdir(exist_ok=True)

CONFIG_DIR = BASE_DIR / 'config'
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

MODEL_DIR = BASE_DIR / 'models'
MODEL_DIR.mkdir(exist_ok=True)

BACKUP_DIR = DATA_DIR / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)

# Database paths
REAL_DB_PATH = DATA_DIR / 'bpf_ac_ai_system.db'
DEMO_DB_PATH = DATA_DIR / 'bpf_ac_ai_system_demo.db'

# Default users (passwords are SHA256 hashes)
DEFAULT_USERS = {
    "admin": {
        "password": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "admin"
    },
    "teknisi": {
        "password": "6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090",  # teknisi123
        "role": "teknisi"
    },
    "manager": {
        "password": "6b3a55e0261b0304143f805a24924d0c1c44524821305f31d9277843b8a0f49e",  # manager123
        "role": "manager"
    },
    "demo": {
        "password": "2a97516c354b68848cdbd8f54a226a0a55b21ed138e207ad6c5cbb9c00aa5aea",  # demo123
        "role": "viewer"
    }
}

# App settings
APP_NAME = "BPF Asset Management System"
APP_VERSION = "3.0"
APP_COMPANY = "PT BESTPROFIT FUTURES SURABAYA"

# Color scheme
COLORS = {
    'primary': '#003366',
    'secondary': '#CC0000',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'dark': '#002244',
    'light': '#f0f2f6'
}

# AC Health thresholds
HEALTH_THRESHOLDS = {
    'good': 80,
    'warning': 60,
    'critical': 40,
    'severe': 0
}

# Anomaly detection thresholds
ANOMALY_THRESHOLDS = {
    'delta_t_min': 8,
    'delta_t_critical': 6,
    'amp_max': 25,
    'amp_critical': 30,
    'low_p_min': 120,
    'low_p_max': 160
}