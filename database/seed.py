"""
Database Seeding - Initial data and dummy data generation
"""

import random
import logging
from datetime import datetime, timedelta
import pandas as pd
from database.engine import get_connection

logger = logging.getLogger(__name__)


def init_bpf_assets(mode='real'):
    """Initialize BPF AC assets"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    assets = [
        ("AC-01-R. BEST 8", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 8", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-02-R. BEST 7, OPERATIONAL", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 7, OPERATIONAL", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-03-R. BEST 6", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 6", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-04-R. BEST 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 5", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-05-R. BEST 3, VIP 8", "Daikin", "Split Duct", "100.000 Btu/h", "R. BEST 3, VIP 8", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-06-R. BEST 2, VIP 6 & 7", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 2, VIP 6 & 7", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-07-R. BEST 1, VIP 3 & 5", "Daikin", "Split Duct", "60.000 Btu/h", "R. BEST 1, VIP 3 & 5", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-08-R. KARAOKE", "Daikin", "Split Duct", "100.000 Btu/h", "R. KARAOKE", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-09-LOUNGE 1, 2, VIP 1, 2", "Daikin", "Split Duct", "60.000 Btu/h", "LOUNGE 1, 2, VIP 1, 2", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-10-R. BM & R. FINANCE", "Daikin", "Split Duct", "60.000 Btu/h", "R. BM & R. FINANCE", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-11-R. MEETING & RECEPTIONIST", "Daikin", "Split Duct", "60.000 Btu/h", "R. MEETING & RECEPTIONIST", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-12-R. TRAINER & R. SECRETARY", "Daikin", "Split Duct", "60.000 Btu/h", "R. TRAINER & R. SECRETARY", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-13-COMPLIANCE & TRAINING 2", "Daikin", "Split Duct", "60.000 Btu/h", "COMPLIANCE & TRAINING 2", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-14-IT & R. SERVER", "Daikin", "Split Duct", "60.000 Btu/h", "IT & R. SERVER", "R32", "2020-01-15", "2025-01-15", "Aktif"),
        ("AC-15-RUANG TRAINING 1", "Daikin", "Split Wall", "2 PK", "RUANG TRAINING 1", "R32", "2020-01-15", "2025-01-15", "Aktif")
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO assets 
        (asset_id, merk, tipe, kapasitas, lokasi, refrigerant, installation_date, warranty_until, status) 
        VALUES (?,?,?,?,?,?,?,?,?)
    """, assets)
    
    conn.commit()
    conn.close()
    logger.info(f"BPF assets initialized in {mode} mode")


def init_vehicle_components(mode='real'):
    """Initialize vehicle components"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    components = [
        ("Oli Mesin", 5000, 6, 1, "Mesin", 1, 500000, "Ganti setiap 5,000 km atau 6 bulan"),
        ("Oli Transmisi", 40000, 24, 1, "Transmisi", 2, 750000, "Ganti setiap 40,000 km atau 2 tahun"),
        ("Ban", 40000, 36, 1, "Roda", 2, 3500000, "Rotasi dan ganti sesuai keausan"),
        ("Aki", 0, 24, 1, "Kelistrikan", 2, 1200000, "Ganti setiap 2 tahun"),
        ("Filter Oli", 5000, 6, 1, "Mesin", 1, 85000, "Ganti bersama oli mesin"),
        ("Filter Udara", 20000, 12, 1, "Mesin", 2, 150000, "Ganti setiap 20,000 km atau 1 tahun"),
        ("Filter AC", 20000, 12, 1, "AC", 3, 200000, "Ganti untuk kualitas udara"),
        ("Busi", 20000, 12, 1, "Pengapian", 2, 350000, "Ganti setiap 20,000 km"),
        ("Kampas Rem Depan", 30000, 18, 1, "Rem", 1, 850000, "Periksa setiap servis"),
        ("Kampas Rem Belakang", 40000, 24, 1, "Rem", 1, 750000, "Periksa setiap servis"),
        ("Pendingin Radiator", 40000, 24, 1, "Pendingin", 2, 350000, "Ganti setiap 40,000 km"),
        ("Timing Belt", 80000, 48, 1, "Mesin", 1, 2500000, "KRITIS - Ganti tepat waktu"),
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicle_components 
        (component_name, standard_life_km, standard_life_months, is_active, category, priority, estimated_cost, notes) 
        VALUES (?,?,?,?,?,?,?,?)
    """, components)
    
    conn.commit()
    conn.close()
    logger.info(f"Vehicle components initialized in {mode} mode")


def init_sample_vehicles(mode='real'):
    """Initialize sample vehicles"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    vehicles = [
        ("VH-001", "Toyota", "Innova", 2020, "B 1234 ABC", "Hitam", "Bensin", "Aktif", "2020-01-15", 85000, "Mobil Operasional Direktur", "2025-01-15", "2025-01-15"),
        ("VH-002", "Honda", "CRV", 2021, "B 5678 DEF", "Putih", "Bensin", "Aktif", "2021-03-20", 45000, "Mobil Operasional Manager", "2026-03-20", "2025-03-20"),
        ("VH-003", "Mitsubishi", "Xpander", 2022, "B 9012 GHI", "Silver", "Bensin", "Aktif", "2022-06-10", 28000, "Mobil Antar Jemput Karyawan", "2027-06-10", "2025-06-10"),
        ("VH-004", "Suzuki", "Carry", 2019, "B 3456 JKL", "Putih", "Bensin", "Aktif", "2019-11-05", 120000, "Mobil Operasional Logistik", "2024-11-05", "2024-11-05"),
        ("VH-005", "Toyota", "Hiace", 2018, "B 7890 MNO", "Abu-abu", "Solar", "Aktif", "2018-08-12", 180000, "Mobil Antar Jemput", "2023-08-12", "2024-08-12")
    ]
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status, purchase_date, last_odometer, notes, insurance_until, tax_until) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, vehicles)
    
    conn.commit()
    conn.close()
    logger.info(f"Sample vehicles initialized in {mode} mode")


def generate_dummy_ac_logs(logs_per_asset=100, mode='demo'):
    """Generate dummy AC maintenance logs"""
    conn = get_connection(mode)
    assets_df = pd.read_sql_query("SELECT asset_id FROM assets", conn)
    asset_ids = assets_df['asset_id'].tolist()
    
    start_date = datetime.now() - timedelta(days=365)
    dummy_logs = []
    teknisi_list = ['Andi Wijaya', 'Budi Santoso', 'Cahyo Purnomo', 'Dedi Kurniawan', 'Eko Prasetyo']
    
    for asset_id in asset_ids:
        for i in range(logs_per_asset):
            days_offset = i * random.randint(3, 10)
            log_date = start_date + timedelta(days=days_offset)
            if log_date > datetime.now():
                continue
            
            amp = 15 + random.uniform(-2, 10)
            delta_t = 10 + random.uniform(-3, 5)
            health_score = max(20, min(100, int(80 + random.uniform(-30, 20))))
            
            dummy_logs.append((
                asset_id, log_date.strftime('%Y-%m-%d'), random.choice(teknisi_list),
                380, round(amp, 2), 140, 350, 24, 24-delta_t, 32, round(delta_t, 1),
                'Lancar', 'Normal' if health_score > 65 else 'Abnormal', health_score,
                random.randint(0, 500000), '', None
            ))
    
    c = conn.cursor()
    for batch in [dummy_logs[i:i+100] for i in range(0, len(dummy_logs), 100)]:
        c.executemany("""
            INSERT INTO maintenance_logs 
            (asset_id, tanggal, teknisi, v_supply, amp_kompresor, low_p, high_p, 
             temp_ret, temp_sup, temp_outdoor, delta_t, drainage, test_run, 
             health_score, sparepart_cost, catatan, next_service_date) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
    
    conn.commit()
    conn.close()
    logger.info(f"Generated {len(dummy_logs)} dummy AC logs")


def generate_dummy_vehicle_services(services_per_vehicle=50, mode='demo'):
    """Generate dummy vehicle service logs"""
    conn = get_connection(mode)
    vehicles_df = pd.read_sql_query("SELECT vehicle_id, last_odometer FROM vehicles", conn)
    components_df = pd.read_sql_query("""
        SELECT component_name, standard_life_km, standard_life_months, estimated_cost 
        FROM vehicle_components WHERE is_active = 1
    """, conn)
    
    start_date = datetime.now() - timedelta(days=730)
    dummy_services = []
    
    for _, vehicle in vehicles_df.iterrows():
        vehicle_id = vehicle['vehicle_id']
        current_odometer = vehicle['last_odometer']
        
        for i in range(services_per_vehicle):
            days_offset = i * random.randint(20, 40)
            service_date = start_date + timedelta(days=days_offset)
            if service_date > datetime.now():
                continue
            
            service_odometer = int(current_odometer * (i / services_per_vehicle)) + random.randint(-1000, 1000)
            service_odometer = max(0, min(current_odometer, service_odometer))
            
            if components_df.empty:
                continue
                
            component = components_df.sample(1).iloc[0]
            cost = component['estimated_cost'] * random.uniform(0.8, 1.3)
            
            dummy_services.append((
                vehicle_id, service_date.strftime('%Y-%m-%d'), service_odometer,
                'Servis Rutin' if i % 3 == 0 else 'Penggantian Komponen',
                component['component_name'], component['standard_life_km'],
                component['standard_life_months'], 0, 0,
                service_odometer + component['standard_life_km'] if component['standard_life_km'] > 0 else 0,
                component['standard_life_months'], round(cost, -3),
                'Bengkel Resmi', f"Servis {component['component_name']}", '', f"INV-{random.randint(1000,9999)}"
            ))
    
    c = conn.cursor()
    for batch in [dummy_services[i:i+100] for i in range(0, len(dummy_services), 100)]:
        c.executemany("""
            INSERT INTO vehicle_service_logs 
            (vehicle_id, service_date, odometer, service_type, component_name,
             component_life_km, component_life_months, current_usage_km,
             current_usage_months, next_service_km, next_service_months, 
             cost, mechanic_name, notes, parts_replaced, invoice_number) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
    
    conn.commit()
    conn.close()
    logger.info(f"Generated {len(dummy_services)} dummy vehicle services")


def generate_dummy_vehicles(count=15, mode='demo'):
    """Generate additional dummy vehicles"""
    conn = get_connection(mode)
    c = conn.cursor()
    
    brands = ['Toyota', 'Honda', 'Mitsubishi', 'Suzuki', 'Daihatsu', 'Nissan', 'Mazda']
    models = {
        'Toyota': ['Avanza', 'Innova', 'Fortuner', 'Rush', 'Yaris'],
        'Honda': ['Brio', 'Jazz', 'CR-V', 'HR-V', 'Mobilio'],
        'Mitsubishi': ['Xpander', 'Pajero', 'Triton', 'Outlander'],
        'Suzuki': ['Ertiga', 'Carry', 'XL7', 'Baleno'],
        'Daihatsu': ['Xenia', 'Terios', 'Sigra', 'Rocky'],
        'Nissan': ['Livina', 'March', 'Kicks', 'Navara'],
        'Mazda': ['CX-3', 'CX-5', '2', '3']
    }
    colors = ['Hitam', 'Putih', 'Silver', 'Abu-abu', 'Merah', 'Biru']
    fuel_types = ['Bensin', 'Solar']
    
    existing = pd.read_sql_query("SELECT vehicle_id FROM vehicles", conn)
    existing_ids = set(existing['vehicle_id'].tolist()) if not existing.empty else set()
    
    new_vehicles = []
    for i in range(count):
        while True:
            new_id = f"VH-{random.randint(100, 999):03d}"
            if new_id not in existing_ids:
                existing_ids.add(new_id)
                break
        
        brand = random.choice(brands)
        model = random.choice(models[brand])
        year = random.randint(2018, 2024)
        plate = f"B {random.randint(1000, 9999)} {''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))}"
        color = random.choice(colors)
        fuel = random.choice(fuel_types)
        status = random.choice(['Aktif', 'Aktif', 'Aktif', 'Service'])
        purchase_date = datetime.now() - timedelta(days=random.randint(365, 1825))
        months_old = (datetime.now() - purchase_date).days / 30
        odometer = int(months_old * random.randint(1000, 2500))
        
        new_vehicles.append((
            new_id, brand, model, year, plate, color, fuel, status,
            purchase_date.strftime('%Y-%m-%d'), odometer, f"Kendaraan operasional {brand} {model}",
            (datetime.now() + timedelta(days=random.randint(180, 540))).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=random.randint(90, 450))).strftime('%Y-%m-%d')
        ))
    
    c.executemany("""
        INSERT OR IGNORE INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status,
         purchase_date, last_odometer, notes, insurance_until, tax_until)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, new_vehicles)
    
    conn.commit()
    conn.close()
    logger.info(f"Generated {len(new_vehicles)} additional dummy vehicles")