"""
CRUD Operations for database
"""

import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from src.database.engine import DatabaseEngine

logger = logging.getLogger(__name__)

class CRUDOperations:
    """CRUD operations class"""
    
    def __init__(self, db_engine: DatabaseEngine = None):
        if db_engine is None:
            db_engine = DatabaseEngine()
        self.db = db_engine
    
    # ==================== ASSETS (AC) ====================
    
    def get_assets(self, mode: str = 'real') -> pd.DataFrame:
        """Get all AC assets"""
        conn = self.db.get_connection(mode)
        try:
            df = pd.read_sql_query("SELECT * FROM assets ORDER BY asset_id", conn)
            if df.empty:
                df = pd.DataFrame(columns=[
                    'asset_id', 'merk', 'tipe', 'kapasitas', 'lokasi', 'refrigerant',
                    'installation_date', 'warranty_until', 'last_maintenance', 'status',
                    'created_at', 'updated_at'
                ])
        except Exception as e:
            logger.error(f"Error getting assets: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def get_asset_by_id(self, asset_id: str, mode: str = 'real') -> Optional[Dict]:
        """Get asset by ID"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
            row = c.fetchone()
            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"Error getting asset {asset_id}: {e}")
        finally:
            conn.close()
        return None
    
    def add_asset(self, data: Tuple, mode: str = 'real') -> bool:
        """Add new AC asset"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO assets 
                (asset_id, merk, tipe, kapasitas, lokasi, refrigerant, installation_date, status) 
                VALUES (?,?,?,?,?,?,date('now'),'Aktif')
            """, data)
            conn.commit()
            logger.info(f"Added asset: {data[0]}")
            return True
        except Exception as e:
            logger.error(f"Error adding asset: {e}")
            return False
        finally:
            conn.close()
    
    def update_asset(self, asset_id: str, data: Tuple, mode: str = 'real') -> bool:
        """Update AC asset"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                UPDATE assets 
                SET merk=?, tipe=?, kapasitas=?, lokasi=?, refrigerant=?, updated_at=CURRENT_TIMESTAMP
                WHERE asset_id=?
            """, (*data, asset_id))
            conn.commit()
            logger.info(f"Updated asset: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating asset: {e}")
            return False
        finally:
            conn.close()
    
    def delete_asset(self, asset_id: str, mode: str = 'real') -> bool:
        """Delete AC asset"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("DELETE FROM assets WHERE asset_id=?", (asset_id,))
            conn.commit()
            logger.info(f"Deleted asset: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting asset: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== MAINTENANCE LOGS ====================
    
    def get_all_logs(self, mode: str = 'real') -> pd.DataFrame:
        """Get all maintenance logs with asset info"""
        conn = self.db.get_connection(mode)
        try:
            df = pd.read_sql_query("""
                SELECT m.*, a.lokasi, a.merk, a.kapasitas 
                FROM maintenance_logs m 
                JOIN assets a ON m.asset_id = a.asset_id 
                ORDER BY m.tanggal DESC, m.id DESC
            """, conn)
            
            if df.empty:
                df = pd.DataFrame(columns=[
                    'id', 'asset_id', 'tanggal', 'teknisi', 'v_supply', 'amp_kompresor',
                    'low_p', 'high_p', 'temp_ret', 'temp_sup', 'temp_outdoor', 'delta_t',
                    'drainage', 'test_run', 'health_score', 'sparepart_cost', 'catatan',
                    'next_service_date', 'created_at', 'lokasi', 'merk', 'kapasitas'
                ])
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def get_logs_by_asset(self, asset_id: str, limit: int = 100, mode: str = 'real') -> pd.DataFrame:
        """Get logs for specific asset"""
        conn = self.db.get_connection(mode)
        try:
            df = pd.read_sql_query("""
                SELECT * FROM maintenance_logs 
                WHERE asset_id = ? 
                ORDER BY tanggal DESC 
                LIMIT ?
            """, conn, params=(asset_id, limit))
        except Exception as e:
            logger.error(f"Error getting logs for {asset_id}: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def add_log(self, data: Tuple, mode: str = 'real') -> bool:
        """Add maintenance log"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            if len(data) < 16:
                data = list(data) + [None] * (16 - len(data))
            
            c.execute("""
                INSERT INTO maintenance_logs 
                (asset_id, tanggal, teknisi, v_supply, amp_kompresor, low_p, 
                 temp_ret, temp_sup, delta_t, drainage, test_run, health_score, 
                 sparepart_cost, catatan, high_p, temp_outdoor) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, data[:16])
            
            c.execute("UPDATE assets SET last_maintenance = ? WHERE asset_id = ?", (data[1], data[0]))
            conn.commit()
            logger.info(f"Added maintenance log for asset: {data[0]}")
            return True
        except Exception as e:
            logger.error(f"Error adding log: {e}")
            return False
        finally:
            conn.close()
    
    def delete_log(self, log_id: int, mode: str = 'real') -> bool:
        """Delete maintenance log"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("DELETE FROM maintenance_logs WHERE id=?", (log_id,))
            conn.commit()
            logger.info(f"Deleted maintenance log: {log_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting log: {e}")
            return False
        finally:
            conn.close()
    
    def delete_old_logs(self, days_to_keep: int, mode: str = 'real') -> int:
        """Delete logs older than specified days"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
            c.execute("DELETE FROM maintenance_logs WHERE tanggal < ?", (cutoff_date,))
            deleted = c.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted} old logs")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting old logs: {e}")
            return 0
        finally:
            conn.close()
    
    # ==================== VEHICLES ====================
    
    def get_vehicles(self, mode: str = 'real') -> pd.DataFrame:
        """Get all vehicles"""
        conn = self.db.get_connection(mode)
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
    
    def get_vehicle_by_id(self, vehicle_id: str, mode: str = 'real') -> Optional[Dict]:
        """Get vehicle by ID"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
            row = c.fetchone()
            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {e}")
        finally:
            conn.close()
        return None
    
    def add_vehicle(self, data: Tuple, mode: str = 'real') -> bool:
        """Add new vehicle"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO vehicles 
                (vehicle_id, brand, model, year, plate_number, color, fuel_type, status, 
                 purchase_date, last_odometer, notes) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, data[:11])
            conn.commit()
            logger.info(f"Added vehicle: {data[0]}")
            return True
        except Exception as e:
            logger.error(f"Error adding vehicle: {e}")
            return False
        finally:
            conn.close()
    
    def update_vehicle(self, vehicle_id: str, data: Tuple, mode: str = 'real') -> bool:
        """Update vehicle"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                UPDATE vehicles 
                SET brand=?, model=?, year=?, plate_number=?, color=?, 
                    fuel_type=?, status=?, purchase_date=?, last_odometer=?, notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE vehicle_id=?
            """, (*data[:10], vehicle_id))
            conn.commit()
            logger.info(f"Updated vehicle: {vehicle_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating vehicle: {e}")
            return False
        finally:
            conn.close()
    
    def update_vehicle_odometer(self, vehicle_id: str, odometer: int, mode: str = 'real') -> bool:
        """Update vehicle odometer"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                UPDATE vehicles 
                SET last_odometer = ?, updated_at = CURRENT_TIMESTAMP
                WHERE vehicle_id = ? AND last_odometer < ?
            """, (odometer, vehicle_id, odometer))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating odometer: {e}")
            return False
        finally:
            conn.close()
    
    def delete_vehicle(self, vehicle_id: str, mode: str = 'real') -> bool:
        """Delete vehicle"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("DELETE FROM vehicles WHERE vehicle_id=?", (vehicle_id,))
            conn.commit()
            logger.info(f"Deleted vehicle: {vehicle_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vehicle: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== VEHICLE SERVICES ====================
    
    def get_vehicle_services(self, vehicle_id: str = None, mode: str = 'real') -> pd.DataFrame:
        """Get vehicle service logs"""
        conn = self.db.get_connection(mode)
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
        except Exception as e:
            logger.error(f"Error getting vehicle services: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def add_vehicle_service(self, data: Tuple, mode: str = 'real') -> bool:
        """Add vehicle service log"""
        conn = self.db.get_connection(mode)
        try:
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
            logger.info(f"Added service for vehicle: {data[0]}")
            return True
        except Exception as e:
            logger.error(f"Error adding vehicle service: {e}")
            return False
        finally:
            conn.close()
    
    def delete_vehicle_service(self, service_id: int, mode: str = 'real') -> bool:
        """Delete vehicle service log"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("DELETE FROM vehicle_service_logs WHERE id=?", (service_id,))
            conn.commit()
            logger.info(f"Deleted vehicle service: {service_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vehicle service: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== VEHICLE COMPONENTS ====================
    
    def get_vehicle_components(self, mode: str = 'real') -> pd.DataFrame:
        """Get all vehicle components"""
        conn = self.db.get_connection(mode)
        try:
            df = pd.read_sql_query("""
                SELECT * FROM vehicle_components 
                WHERE is_active = 1 
                ORDER BY priority, component_name
            """, conn)
        except Exception as e:
            logger.error(f"Error getting components: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def add_vehicle_component(self, data: Tuple, mode: str = 'real') -> bool:
        """Add vehicle component"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO vehicle_components 
                (component_name, standard_life_km, standard_life_months, is_active) 
                VALUES (?,?,?,?)
            """, data[:4])
            conn.commit()
            logger.info(f"Added component: {data[0]}")
            return True
        except Exception as e:
            logger.error(f"Error adding component: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== RECOMMENDATIONS ====================
    
    def save_recommendation(self, asset_id: str, priority: str, urgency_days: int,
                           actions: List[str], estimated_cost: float, mode: str = 'real') -> bool:
        """Save maintenance recommendation"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO maintenance_recommendations 
                (asset_id, recommendation_date, priority, urgency_days, actions, estimated_cost, status) 
                VALUES (?, date('now'), ?, ?, ?, ?, 'Pending')
            """, (asset_id, priority, urgency_days, json.dumps(actions), estimated_cost))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")
            return False
        finally:
            conn.close()
    
    def get_recommendations(self, asset_id: str = None, mode: str = 'real') -> pd.DataFrame:
        """Get pending recommendations"""
        conn = self.db.get_connection(mode)
        try:
            if asset_id:
                df = pd.read_sql_query("""
                    SELECT * FROM maintenance_recommendations 
                    WHERE asset_id = ? AND status = 'Pending'
                    ORDER BY 
                        CASE priority 
                            WHEN 'Critical' THEN 1 
                            WHEN 'High' THEN 2 
                            WHEN 'Medium' THEN 3 
                            ELSE 4 
                        END, urgency_days
                """, conn, params=(asset_id,))
            else:
                df = pd.read_sql_query("""
                    SELECT * FROM maintenance_recommendations 
                    WHERE status = 'Pending'
                    ORDER BY 
                        CASE priority 
                            WHEN 'Critical' THEN 1 
                            WHEN 'High' THEN 2 
                            WHEN 'Medium' THEN 3 
                            ELSE 4 
                        END, urgency_days
                """, conn)
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def update_recommendation_status(self, rec_id: int, status: str, mode: str = 'real') -> bool:
        """Update recommendation status"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                UPDATE maintenance_recommendations 
                SET status = ?, completed_date = date('now')
                WHERE id = ?
            """, (status, rec_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating recommendation: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== NOTIFICATIONS ====================
    
    def save_notification(self, asset_id: str, vehicle_id: str, notification_type: str,
                         severity: str, title: str, message: str, action_required: str,
                         mode: str = 'real') -> bool:
        """Save notification"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO notifications 
                (asset_id, vehicle_id, notification_type, severity, title, message, action_required) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (asset_id, vehicle_id, notification_type, severity, title, message, action_required))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving notification: {e}")
            return False
        finally:
            conn.close()
    
    def get_notifications(self, limit: int = 20, unread_only: bool = False, mode: str = 'real') -> pd.DataFrame:
        """Get notifications"""
        conn = self.db.get_connection(mode)
        try:
            query = "SELECT * FROM notifications WHERE 1=1"
            if unread_only:
                query += " AND is_read = 0"
            query += " ORDER BY created_at DESC LIMIT ?"
            df = pd.read_sql_query(query, conn, params=(limit,))
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def mark_notification_read(self, notification_id: int, mode: str = 'real') -> bool:
        """Mark notification as read"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error marking notification read: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== EXECUTIVE SUMMARY ====================
    
    def save_executive_summary(self, period: str, summary_data: Dict, mode: str = 'real') -> bool:
        """Save executive summary"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO executive_summaries (report_date, period, summary_data) 
                VALUES (date('now'), ?, ?)
            """, (period, json.dumps(summary_data)))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving executive summary: {e}")
            return False
        finally:
            conn.close()
    
    def get_latest_executive_summary(self, mode: str = 'real') -> Optional[Dict]:
        """Get latest executive summary"""
        conn = self.db.get_connection(mode)
        try:
            df = pd.read_sql_query("""
                SELECT * FROM executive_summaries 
                ORDER BY created_at DESC LIMIT 1
            """, conn)
            if not df.empty:
                return json.loads(df.iloc[0]['summary_data'])
        except Exception as e:
            logger.error(f"Error getting executive summary: {e}")
        finally:
            conn.close()
        return None
    
    # ==================== AUDIT LOG ====================
    
    def log_audit(self, table_name: str, record_id: str, action: str, user_name: str,
                  old_values: Dict = None, new_values: Dict = None, mode: str = 'real') -> bool:
        """Log audit trail"""
        conn = self.db.get_connection(mode)
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO audit_logs 
                (table_name, record_id, action, user_name, old_values, new_values) 
                VALUES (?,?,?,?,?,?)
            """, (table_name, str(record_id), action, user_name,
                  json.dumps(old_values) if old_values else None,
                  json.dumps(new_values) if new_values else None))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
            return False
        finally:
            conn.close()