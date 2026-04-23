"""
Database Models - Table creation and schema
"""

import logging
from database.engine import get_connection

logger = logging.getLogger(__name__)


def create_db(mode='real'):
    """Create all database tables"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    # Master Aset AC
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY, 
                    merk TEXT NOT NULL, 
                    tipe TEXT NOT NULL, 
                    kapasitas TEXT NOT NULL, 
                    lokasi TEXT NOT NULL, 
                    refrigerant TEXT NOT NULL,
                    installation_date TEXT,
                    warranty_until TEXT,
                    last_maintenance TEXT,
                    status TEXT DEFAULT 'Aktif',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Master Aset Kendaraan
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id TEXT PRIMARY KEY, 
                    brand TEXT NOT NULL, 
                    model TEXT NOT NULL, 
                    year INTEGER NOT NULL,
                    plate_number TEXT UNIQUE NOT NULL,
                    color TEXT,
                    fuel_type TEXT NOT NULL,
                    status TEXT DEFAULT 'Aktif',
                    purchase_date TEXT NOT NULL,
                    last_odometer INTEGER DEFAULT 0,
                    notes TEXT,
                    insurance_until TEXT,
                    tax_until TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Log Maintenance AC
    c.execute('''CREATE TABLE IF NOT EXISTS maintenance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    tanggal TEXT NOT NULL,
                    teknisi TEXT NOT NULL,
                    v_supply REAL,
                    amp_kompresor REAL,
                    low_p REAL,
                    high_p REAL,
                    temp_ret REAL,
                    temp_sup REAL,
                    temp_outdoor REAL,
                    delta_t REAL,
                    drainage TEXT,
                    test_run TEXT,
                    health_score INTEGER,
                    sparepart_cost REAL DEFAULT 0,
                    catatan TEXT,
                    next_service_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asset_id) REFERENCES assets (asset_id) ON DELETE CASCADE)''')
    
    # Log Servis Kendaraan
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_service_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id TEXT NOT NULL,
                    service_date TEXT NOT NULL,
                    odometer INTEGER NOT NULL,
                    service_type TEXT NOT NULL,
                    component_name TEXT NOT NULL,
                    component_life_km INTEGER DEFAULT 0,
                    component_life_months INTEGER DEFAULT 0,
                    current_usage_km INTEGER DEFAULT 0,
                    current_usage_months INTEGER DEFAULT 0,
                    next_service_km INTEGER DEFAULT 0,
                    next_service_months INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0,
                    mechanic_name TEXT,
                    notes TEXT,
                    parts_replaced TEXT,
                    invoice_number TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id) ON DELETE CASCADE)''')
    
    # Master Komponen Kendaraan
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_name TEXT UNIQUE NOT NULL,
                    standard_life_km INTEGER DEFAULT 0,
                    standard_life_months INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    category TEXT,
                    priority INTEGER DEFAULT 1,
                    estimated_cost REAL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # Maintenance Recommendations
    c.execute('''CREATE TABLE IF NOT EXISTS maintenance_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    recommendation_date TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    urgency_days INTEGER DEFAULT 0,
                    actions TEXT NOT NULL,
                    estimated_cost REAL DEFAULT 0,
                    status TEXT DEFAULT 'Pending',
                    completed_date TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asset_id) REFERENCES assets (asset_id) ON DELETE CASCADE)''')
    
    # Notifications
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT,
                    vehicle_id TEXT,
                    notification_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    action_required TEXT,
                    is_read INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # ML Model Metadata
    c.execute('''CREATE TABLE IF NOT EXISTS ml_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    accuracy REAL,
                    last_trained TEXT,
                    parameters TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # Audit Logs
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id TEXT,
                    action TEXT NOT NULL,
                    user_name TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # Executive Summaries Cache
    c.execute('''CREATE TABLE IF NOT EXISTS executive_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT NOT NULL,
                    period TEXT NOT NULL,
                    summary_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_logs_asset_date ON maintenance_logs(asset_id, tanggal)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_logs_health ON maintenance_logs(health_score)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vehicle_services_vehicle ON vehicle_service_logs(vehicle_id, service_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_vehicle_services_component ON vehicle_service_logs(component_name)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_recommendations_asset ON maintenance_recommendations(asset_id, status)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_asset ON notifications(asset_id, is_read)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_notifications_vehicle ON notifications(vehicle_id, is_read)')
    
    conn.commit()
    conn.close()
    logger.info(f"Database tables created in {mode} mode")