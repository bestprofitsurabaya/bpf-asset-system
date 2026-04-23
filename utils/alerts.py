"""
Alert and Notification Functions
"""

import pandas as pd
from datetime import datetime
import database.crud_ac as db_ac
import database.crud_vehicles as db_vehicles
from utils.anomaly import detect_anomalies_realtime


def check_alerts_and_notify(mode='real'):
    """Check for alerts and generate notifications"""
    
    logs = db_ac.get_all_logs(mode=mode)
    if logs.empty:
        return []
    
    alerts = []
    logs['tanggal'] = pd.to_datetime(logs['tanggal'])
    
    for asset_id in logs['asset_id'].unique():
        asset_logs = logs[logs['asset_id'] == asset_id].sort_values('tanggal').tail(10)
        
        if asset_logs.empty:
            continue
        
        latest = asset_logs.iloc[-1]
        
        # Critical health alert
        if latest['health_score'] < 50:
            alerts.append({
                'type': 'critical',
                'asset_id': asset_id,
                'message': f"Health Score KRITIS: {latest['health_score']}%",
                'action': 'SEGERA lakukan servis besar',
                'timestamp': datetime.now().strftime('%H:%M')
            })
            db_ac.save_notification(
                asset_id, None, 'health_critical', 'Critical',
                f'Health Score Kritis - {asset_id}',
                f'Health Score: {latest["health_score"]}%',
                'Segera lakukan servis besar',
                mode
            )
        
        # Degradation alert
        elif len(asset_logs) >= 5:
            health_trend = asset_logs['health_score'].tail(5).tolist()
            if len(health_trend) >= 3:
                if health_trend[0] > health_trend[1] > health_trend[2]:
                    drop = health_trend[0] - health_trend[2]
                    if drop > 10:
                        alerts.append({
                            'type': 'warning',
                            'asset_id': asset_id,
                            'message': f"Health Score turun cepat: {drop:.0f}%",
                            'action': 'Jadwalkan inspeksi',
                            'timestamp': datetime.now().strftime('%H:%M')
                        })
                        db_ac.save_notification(
                            asset_id, None, 'health_degrading', 'Warning',
                            f'Penurunan Health Score - {asset_id}',
                            f'Health Score turun {drop:.0f}%',
                            'Jadwalkan inspeksi',
                            mode
                        )
        
        # Anomaly detection
        latest_readings = {
            'amp_kompresor': latest['amp_kompresor'] if 'amp_kompresor' in latest else 0,
            'delta_t': latest['delta_t'] if 'delta_t' in latest else 0,
            'low_p': latest['low_p'] if 'low_p' in latest else 140
        }
        anomalies, severity = detect_anomalies_realtime(latest_readings, asset_id, mode)
        
        if severity in ['Critical', 'High']:
            alerts.append({
                'type': 'critical' if severity == 'Critical' else 'warning',
                'asset_id': asset_id,
                'message': f"Anomali terdeteksi: {severity}",
                'action': 'Periksa parameter operasional',
                'timestamp': datetime.now().strftime('%H:%M'),
                'details': anomalies[:2]
            })
            db_ac.save_notification(
                asset_id, None, 'anomaly_detected', severity,
                f'Anomali Terdeteksi - {asset_id}',
                f'Terdeteksi {len(anomalies)} anomali',
                'Periksa parameter operasional',
                mode
            )
    
    type_order = {'critical': 0, 'warning': 1, 'info': 2}
    alerts.sort(key=lambda x: type_order.get(x['type'], 3))
    
    return alerts[:10]


def generate_maintenance_recommendations(mode='real'):
    """Generate smart maintenance recommendations"""
    
    recommendations = []
    logs = db_ac.get_all_logs(mode=mode)
    
    if logs.empty:
        return []
    
    for asset_id in logs['asset_id'].unique():
        asset_logs = logs[logs['asset_id'] == asset_id].sort_values('tanggal')
        
        if len(asset_logs) < 3:
            continue
        
        latest = asset_logs.iloc[-1]
        
        avg_delta = asset_logs['delta_t'].tail(5).mean()
        avg_amp = asset_logs['amp_kompresor'].tail(5).mean()
        
        rec = {
            'asset_id': asset_id,
            'priority': 'Normal',
            'actions': [],
            'estimated_cost': 0,
            'urgency_days': 90
        }
        
        if avg_delta < 6:
            rec['actions'].append("Bersihkan filter dan evaporator - SEGERA")
            rec['estimated_cost'] += 300000
            rec['priority'] = 'Critical'
            rec['urgency_days'] = 3
        elif avg_delta < 8:
            rec['actions'].append("Bersihkan filter dan evaporator")
            rec['estimated_cost'] += 250000
            rec['priority'] = 'High'
            rec['urgency_days'] = 7
        elif avg_delta < 10:
            rec['actions'].append("Cek dan bersihkan filter")
            rec['estimated_cost'] += 150000
            rec['priority'] = 'Medium'
            rec['urgency_days'] = 30
        
        if avg_amp > 30:
            rec['actions'].append("PERIKSA KOMPRESOR SEGERA - Risiko Kerusakan")
            rec['estimated_cost'] += 1000000
            rec['priority'] = 'Critical'
            rec['urgency_days'] = 1
        elif avg_amp > 25:
            rec['actions'].append("Periksa kompresor dan kelistrikan")
            rec['estimated_cost'] += 500000
            rec['priority'] = 'High'
            rec['urgency_days'] = 7
        elif avg_amp > 20:
            rec['actions'].append("Cek beban kompresor")
            rec['estimated_cost'] += 200000
            rec['priority'] = 'Medium'
            rec['urgency_days'] = 14
        
        if latest['low_p'] < 120 or latest['low_p'] > 160:
            rec['actions'].append("Periksa tekanan freon dan kebocoran")
            rec['estimated_cost'] += 350000
            rec['priority'] = 'High'
            rec['urgency_days'] = 5
        elif latest['low_p'] < 130 or latest['low_p'] > 150:
            rec['actions'].append("Monitor tekanan freon")
            rec['estimated_cost'] += 100000
            rec['priority'] = 'Medium'
            rec['urgency_days'] = 14
        
        last_maintenance = pd.to_datetime(latest['tanggal'])
        days_since = (datetime.now() - last_maintenance).days
        
        if days_since > 90:
            rec['actions'].append("Servis rutin terjadwal (3 bulan)")
            rec['estimated_cost'] += 300000
            if rec['priority'] == 'Normal':
                rec['priority'] = 'High'
            rec['urgency_days'] = 7
        elif days_since > 60:
            rec['actions'].append("Servis rutin terjadwal (2 bulan)")
            rec['estimated_cost'] += 300000
            if rec['priority'] == 'Normal':
                rec['priority'] = 'Medium'
            rec['urgency_days'] = 30
        
        if rec['actions']:
            recommendations.append(rec)
            db_ac.save_recommendation(
                asset_id, rec['priority'], rec['urgency_days'],
                rec['actions'], rec['estimated_cost'], mode
            )
    
    priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Normal': 3}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    return recommendations