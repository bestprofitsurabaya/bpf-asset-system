"""
Anomaly Detection Functions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import database.crud_ac as db_ac
from config.settings import ANOMALY_THRESHOLDS


def detect_anomalies_realtime(readings, asset_id, mode='real'):
    """Real-time anomaly detection with multiple methods"""
    
    logs = db_ac.get_all_logs(mode=mode)
    if logs.empty:
        return [], "Normal"
    
    asset_logs = logs[logs['asset_id'] == asset_id].tail(30)
    
    anomalies = []
    severity = "Normal"
    
    if len(asset_logs) >= 5:
        # Statistical anomaly (Z-score)
        for param in ['amp_kompresor', 'delta_t', 'low_p']:
            if param in readings and param in asset_logs.columns:
                mean_val = asset_logs[param].mean()
                std_val = asset_logs[param].std()
                
                if std_val > 0:
                    z_score = abs(readings[param] - mean_val) / std_val
                    
                    if z_score > 3:
                        anomalies.append({
                            'parameter': param,
                            'value': readings[param],
                            'expected': f"{mean_val:.2f} +/- {std_val*2:.2f}",
                            'z_score': round(z_score, 2),
                            'severity': 'High' if z_score > 4 else 'Medium',
                            'message': f'Nilai {param} di luar batas normal'
                        })
    
    # Rule-based anomaly
    delta_t = readings.get('delta_t', 0)
    if delta_t < ANOMALY_THRESHOLDS['delta_t_critical']:
        anomalies.append({
            'parameter': 'delta_t',
            'value': delta_t,
            'expected': f"> {ANOMALY_THRESHOLDS['delta_t_min']}",
            'severity': 'High',
            'message': 'Efisiensi pendinginan sangat rendah - periksa filter dan freon'
        })
    elif delta_t < ANOMALY_THRESHOLDS['delta_t_min']:
        anomalies.append({
            'parameter': 'delta_t',
            'value': delta_t,
            'expected': f"> {ANOMALY_THRESHOLDS['delta_t_min']}",
            'severity': 'Medium',
            'message': 'Efisiensi pendinginan di bawah optimal'
        })
    
    amp = readings.get('amp_kompresor', 0)
    if amp > ANOMALY_THRESHOLDS['amp_critical']:
        anomalies.append({
            'parameter': 'amp_kompresor',
            'value': amp,
            'expected': f"< {ANOMALY_THRESHOLDS['amp_max']}",
            'severity': 'Critical',
            'message': 'Arus kompresor terlalu tinggi - risiko overheating!'
        })
    elif amp > ANOMALY_THRESHOLDS['amp_max']:
        anomalies.append({
            'parameter': 'amp_kompresor',
            'value': amp,
            'expected': f"< {ANOMALY_THRESHOLDS['amp_max']}",
            'severity': 'High',
            'message': 'Arus kompresor di atas normal'
        })
    
    low_p = readings.get('low_p', 140)
    if low_p < ANOMALY_THRESHOLDS['low_p_min']:
        anomalies.append({
            'parameter': 'low_p',
            'value': low_p,
            'expected': f"{ANOMALY_THRESHOLDS['low_p_min']}-{ANOMALY_THRESHOLDS['low_p_max']}",
            'severity': 'High',
            'message': 'Tekanan rendah - kemungkinan kebocoran freon'
        })
    elif low_p > ANOMALY_THRESHOLDS['low_p_max']:
        anomalies.append({
            'parameter': 'low_p',
            'value': low_p,
            'expected': f"{ANOMALY_THRESHOLDS['low_p_min']}-{ANOMALY_THRESHOLDS['low_p_max']}",
            'severity': 'Medium',
            'message': 'Tekanan tinggi - periksa kondensor'
        })
    
    # Trend-based anomaly
    if len(asset_logs) >= 3:
        recent_health = asset_logs['health_score'].tail(3).tolist()
        if len(recent_health) == 3:
            if recent_health[0] > recent_health[1] > recent_health[2]:
                drop_rate = (recent_health[0] - recent_health[2]) / 2
                if drop_rate > 5:
                    anomalies.append({
                        'parameter': 'health_trend',
                        'value': f"Turun {drop_rate:.1f}% per minggu",
                        'expected': 'Stabil',
                        'severity': 'High' if drop_rate > 10 else 'Medium',
                        'message': 'Penurunan performa cepat - perlu investigasi'
                    })
    
    # Determine overall severity
    severity_levels = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
    if anomalies:
        max_severity = max(anomalies, key=lambda x: severity_levels.get(x['severity'], 0))
        severity = max_severity['severity']
    
    return anomalies, severity


def analyze_predictive_maintenance(asset_id, ml_engine, mode='real'):
    """Enhanced predictive maintenance analysis with ML"""
    try:
        logs = db_ac.get_all_logs(mode=mode)
        if logs.empty:
            return "Belum ada data", "Normal", 0
            
        unit_logs = logs[logs['asset_id'] == asset_id].copy()
        
        if len(unit_logs) < 5:
            return "Data Belum Cukup (Min. 5 log)", "Normal", 0
        
        unit_logs['tgl_dt'] = pd.to_datetime(unit_logs['tanggal'])
        base_date = unit_logs['tgl_dt'].min()
        unit_logs['days'] = (unit_logs['tgl_dt'] - base_date).dt.days
        
        latest = unit_logs.iloc[-1]
        readings = {
            'amp': latest['amp_kompresor'] if 'amp_kompresor' in latest else 15,
            'delta_t': latest['delta_t'] if 'delta_t' in latest else 10,
            'low_p': latest['low_p'] if 'low_p' in latest else 140,
            'high_p': latest['high_p'] if 'high_p' in latest else 350,
            'temp_outdoor': latest['temp_outdoor'] if 'temp_outdoor' in latest else 32
        }
        
        ml_health, confidence_interval, is_anomaly, anomaly_score = ml_engine.predict_health_score(asset_id, readings)
        
        if ml_health is None:
            from sklearn.linear_model import LinearRegression
            X = unit_logs[['days']].values
            y = unit_logs['health_score'].values
            
            if len(set(y)) < 2:
                return "Data tidak cukup bervariasi", "Normal", 0
            
            weights = np.linspace(0.5, 1.0, len(y))
            model = LinearRegression()
            model.fit(X, y, sample_weight=weights)
            
            confidence = min(95, max(0, model.score(X, y) * 100))
            
            m = model.coef_[0]
            c = model.intercept_
            
            if m >= 0:
                pred_msg = "Kondisi Stabil/Membaik"
            else:
                days_to_fail = (65 - c) / m
                if days_to_fail > 0:
                    fail_date = base_date + timedelta(days=int(days_to_fail))
                    pred_msg = fail_date.strftime('%d %b %Y')
                else:
                    pred_msg = "SEGERA - Sudah Kritis!"
        else:
            confidence = 85
            days_to_fail, rul_confidence, fail_date = ml_engine.predict_remaining_life(asset_id)
            
            if days_to_fail is not None and days_to_fail < float('inf'):
                if days_to_fail > 0:
                    pred_msg = fail_date.strftime('%d %b %Y') if fail_date else f"{int(days_to_fail)} hari lagi"
                else:
                    pred_msg = "SEGERA - Sudah Kritis!"
            else:
                pred_msg = "Kondisi Stabil/Membaik"
        
        status = "Normal"
        
        if 'amp_kompresor' in unit_logs.columns:
            avg_amp = unit_logs['amp_kompresor'].mean()
            std_amp = unit_logs['amp_kompresor'].std()
            last_amp = unit_logs['amp_kompresor'].iloc[-1]
            if std_amp > 0 and last_amp > (avg_amp + 2 * std_amp):
                status = "Anomali Arus Tinggi"
        
        if 'delta_t' in unit_logs.columns and len(unit_logs) >= 3:
            recent_delta_t = unit_logs['delta_t'].iloc[-3:].mean()
            historical_delta_t = unit_logs['delta_t'].iloc[:-3].mean()
            if historical_delta_t > 0 and recent_delta_t < historical_delta_t * 0.8:
                status = "Anomali Efisiensi" if status == "Normal" else "Multi Anomali"
        
        if is_anomaly:
            status = "ML Anomali Terdeteksi" if status == "Normal" else "ML Multi Anomali"
        
        return pred_msg, status, confidence
        
    except Exception as e:
        logger.error(f"Error in predictive maintenance analysis: {e}")
        return "Error Analisis", "Error", 0