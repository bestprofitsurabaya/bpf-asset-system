"""
Constants used throughout the application
"""

# App info
APP_NAME = "BPF Asset Management System"
APP_VERSION = "4.0.0"
COMPANY_NAME = "PT BESTPROFIT FUTURES SURABAYA"

# Database modes
DB_MODE_REAL = "real"
DB_MODE_DEMO = "demo"

# User roles
ROLE_ADMIN = "admin"
ROLE_TEKNISI = "teknisi"
ROLE_MANAGER = "manager"
ROLE_VIEWER = "viewer"

# Permission matrix
PERMISSIONS = {
    ROLE_ADMIN: {
        "view_dashboard": True,
        "manage_assets": True,
        "manage_vehicles": True,
        "input_maintenance": True,
        "edit_delete_data": True,
        "manage_users": True,
        "view_analytics": True,
        "print_reports": True
    },
    ROLE_MANAGER: {
        "view_dashboard": True,
        "manage_assets": True,
        "manage_vehicles": True,
        "input_maintenance": False,
        "edit_delete_data": False,
        "manage_users": False,
        "view_analytics": True,
        "print_reports": True
    },
    ROLE_TEKNISI: {
        "view_dashboard": True,
        "manage_assets": False,
        "manage_vehicles": False,
        "input_maintenance": True,
        "edit_delete_data": False,
        "manage_users": False,
        "view_analytics": True,
        "print_reports": False
    },
    ROLE_VIEWER: {
        "view_dashboard": True,
        "manage_assets": False,
        "manage_vehicles": False,
        "input_maintenance": False,
        "edit_delete_data": False,
        "manage_users": False,
        "view_analytics": True,
        "print_reports": True
    }
}

# AC Health thresholds
HEALTH_GOOD = 80
HEALTH_WARNING = 60
HEALTH_CRITICAL = 40

# Anomaly thresholds
DELTA_T_MIN = 8
DELTA_T_OPTIMAL = 12
AMP_MAX_NORMAL = 20
AMP_WARNING = 25
AMP_CRITICAL = 30
LOW_PRESSURE_MIN = 120
LOW_PRESSURE_MAX = 160

# Colors
COLOR_PRIMARY = "#003366"
COLOR_SECONDARY = "#CC0000"
COLOR_SUCCESS = "#28a745"
COLOR_WARNING = "#ffc107"
COLOR_DANGER = "#dc3545"
COLOR_INFO = "#17a2b8"