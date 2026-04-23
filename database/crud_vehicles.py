"""
CRUD Operations for Vehicles and Service Logs
"""

import pandas as pd
import logging
from database.engine import get_connection

logger = logging.getLogger(__name__)


def get_vehicles(mode='real'):
    """Get all vehicles"""
    conn = get_connection(mode)
    try:
        df = pd.read_sql_query("SELECT * FROM vehicles ORDER BY vehicle_id", conn)
        if df.empty:
            df = pd.DataFrame(columns=[
                'vehicle_id', 'brand', 'model', 'year', 'plate_number', 'color',
                'fuel_type', 'status', 'purchase_date', 'last_odometer', 'notes',
                'insurance_until', 'tax_until', 'created_at', 'updated_at'
            ])
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def add_vehicle(data, mode='real'):
    """Add new vehicle"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicles 
        (vehicle_id, brand, model, year, plate_number, color, fuel_type, status, 
         purchase_date, last_odometer, notes) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, data[:11])
    conn.commit()
    conn.close()
    logger.info(f"Added vehicle: {data[0]}")


def update_vehicle(vehicle_id, data, mode='real'):
    """Update vehicle"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE vehicles 
        SET brand=?, model=?, year=?, plate_number=?, color=?, 
            fuel_type=?, status=?, purchase_date=?, last_odometer=?, notes=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE vehicle_id=?
    """, (*data[:10], vehicle_id))
    conn.commit()
    conn.close()
    logger.info(f"Updated vehicle: {vehicle_id}")


def update_vehicle_odometer(vehicle_id, odometer, mode='real'):
    """Update vehicle odometer"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("UPDATE vehicles SET last_odometer = ? WHERE vehicle_id = ? AND last_odometer < ?", 
              (odometer, vehicle_id, odometer))
    conn.commit()
    conn.close()


def delete_vehicle(vehicle_id, mode='real'):
    """Delete vehicle"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM vehicles WHERE vehicle_id=?", (vehicle_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted vehicle: {vehicle_id}")


def add_vehicle_service(data, mode='real'):
    """Add vehicle service log"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicle_service_logs 
        (vehicle_id, service_date, odometer, service_type, component_name,
         component_life_km, component_life_months, current_usage_km,
         current_usage_months, next_service_km, next_service_months, 
         cost, mechanic_name, notes) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data[:14])
    conn.commit()
    conn.close()
    logger.info(f"Added service for vehicle: {data[0]}")


def get_vehicle_services(vehicle_id=None, mode='real'):
    """Get vehicle service logs"""
    conn = get_connection(mode)
    try:
        if vehicle_id:
            df = pd.read_sql_query("""
                SELECT * FROM vehicle_service_logs 
                WHERE vehicle_id = ? 
                ORDER BY service_date DESC, id DESC
            """, conn, params=(vehicle_id,))
        else:
            df = pd.read_sql_query("""
                SELECT * FROM vehicle_service_logs 
                ORDER BY service_date DESC, id DESC
            """, conn)
        
        if df.empty:
            df = pd.DataFrame(columns=[
                'id', 'vehicle_id', 'service_date', 'odometer', 'service_type',
                'component_name', 'component_life_km', 'component_life_months',
                'current_usage_km', 'current_usage_months', 'next_service_km',
                'next_service_months', 'cost', 'mechanic_name', 'notes',
                'parts_replaced', 'invoice_number', 'created_at'
            ])
    except Exception as e:
        logger.error(f"Error getting vehicle services: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def delete_vehicle_service(service_id, mode='real'):
    """Delete vehicle service log"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM vehicle_service_logs WHERE id=?", (service_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted vehicle service: {service_id}")


def get_vehicle_components(mode='real'):
    """Get all vehicle components"""
    conn = get_connection(mode)
    df = pd.read_sql_query("""
        SELECT * FROM vehicle_components 
        WHERE is_active = 1 
        ORDER BY priority, component_name
    """, conn)
    conn.close()
    return df


def add_vehicle_component(data, mode='real'):
    """Add vehicle component"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO vehicle_components 
        (component_name, standard_life_km, standard_life_months, is_active) 
        VALUES (?,?,?,?)
    """, data[:4])
    conn.commit()
    conn.close()
    logger.info(f"Added vehicle component: {data[0]}")