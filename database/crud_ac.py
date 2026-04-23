"""
CRUD Operations for AC Assets and Maintenance Logs
"""

import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from database.engine import get_connection

logger = logging.getLogger(__name__)


def get_assets(mode='real'):
    """Get all AC assets"""
    conn = get_connection(mode)
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


def add_asset(data, mode='real'):
    """Add new AC asset"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO assets 
        (asset_id, merk, tipe, kapasitas, lokasi, refrigerant, installation_date, status) 
        VALUES (?,?,?,?,?,?,date('now'),'Aktif')
    """, data)
    conn.commit()
    conn.close()
    logger.info(f"Added asset: {data[0]}")


def update_asset(asset_id, data, mode='real'):
    """Update AC asset"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE assets 
        SET merk=?, tipe=?, kapasitas=?, lokasi=?, refrigerant=?, updated_at=CURRENT_TIMESTAMP
        WHERE asset_id=?
    """, (*data, asset_id))
    conn.commit()
    conn.close()
    logger.info(f"Updated asset: {asset_id}")


def delete_asset(asset_id, mode='real'):
    """Delete AC asset"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM assets WHERE asset_id=?", (asset_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted asset: {asset_id}")


def add_log(data, mode='real'):
    """Add maintenance log"""
    conn = get_connection(mode)
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
    conn.close()
    logger.info(f"Added maintenance log for asset: {data[0]}")


def get_all_logs(mode='real'):
    """Get all maintenance logs with asset info"""
    conn = get_connection(mode)
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


def delete_log(log_id, mode='real'):
    """Delete maintenance log"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("DELETE FROM maintenance_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted maintenance log: {log_id}")


def delete_old_logs(days_to_keep, mode='real'):
    """Delete logs older than specified days"""
    conn = get_connection(mode)
    c = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
    c.execute("DELETE FROM maintenance_logs WHERE tanggal < ?", (cutoff_date,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Deleted {deleted} old logs")
    return deleted


def save_recommendation(asset_id, priority, urgency_days, actions, estimated_cost, mode='real'):
    """Save maintenance recommendation"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO maintenance_recommendations 
        (asset_id, recommendation_date, priority, urgency_days, actions, estimated_cost, status) 
        VALUES (?, date('now'), ?, ?, ?, ?, 'Pending')
    """, (asset_id, priority, urgency_days, json.dumps(actions), estimated_cost))
    conn.commit()
    conn.close()


def get_recommendations(asset_id=None, mode='real'):
    """Get maintenance recommendations"""
    conn = get_connection(mode)
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
    conn.close()
    return df


def update_recommendation_status(rec_id, status, mode='real'):
    """Update recommendation status"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        UPDATE maintenance_recommendations 
        SET status = ?, completed_date = date('now')
        WHERE id = ?
    """, (status, rec_id))
    conn.commit()
    conn.close()


def save_notification(asset_id, vehicle_id, notification_type, severity, title, message, action_required, mode='real'):
    """Save notification"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO notifications 
        (asset_id, vehicle_id, notification_type, severity, title, message, action_required) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (asset_id, vehicle_id, notification_type, severity, title, message, action_required))
    conn.commit()
    conn.close()


def get_notifications(limit=20, unread_only=False, mode='real'):
    """Get notifications"""
    conn = get_connection(mode)
    query = "SELECT * FROM notifications WHERE 1=1"
    if unread_only:
        query += " AND is_read = 0"
    query += " ORDER BY created_at DESC LIMIT ?"
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df


def mark_notification_read(notification_id, mode='real'):
    """Mark notification as read"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()


def save_executive_summary(period, summary_data, mode='real'):
    """Save executive summary"""
    conn = get_connection(mode)
    c = conn.cursor()
    c.execute("""
        INSERT INTO executive_summaries (report_date, period, summary_data) 
        VALUES (date('now'), ?, ?)
    """, (period, json.dumps(summary_data)))
    conn.commit()
    conn.close()


def get_latest_executive_summary(mode='real'):
    """Get latest executive summary"""
    conn = get_connection(mode)
    df = pd.read_sql_query("""
        SELECT * FROM executive_summaries 
        ORDER BY created_at DESC LIMIT 1
    """, conn)
    conn.close()
    if not df.empty:
        return json.loads(df.iloc[0]['summary_data'])
    return None