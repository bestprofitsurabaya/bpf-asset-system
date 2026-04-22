"""
AI Dashboard Page - Predictive Maintenance
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.crud import CRUDOperations
from src.database.engine import DatabaseEngine
from src.ml.predictive_engine import PredictiveMaintenanceEngine
from src.visualization.charts import (
    create_health_gauge, create_correlation_heatmap, create_3d_scatter,
    create_degradation_timeline, create_health_distribution_chart
)
from src.utils.helpers import get_health_color, get_health_status


def analyze_predictive_maintenance(asset_id: str, ml_engine: PredictiveMaintenanceEngine,
                                   crud: CRUDOperations, mode: str) -> tuple:
    """Analyze predictive maintenance for an asset"""
    try:
        logs = crud.get_all_logs(mode)
        if logs.empty:
            return "Belum ada data", "Normal", 0
        
        unit_logs = logs[logs['asset_id'] == asset_id].copy()
        
        if len(unit_logs) < 5:
            return "Data Belum Cukup (Min. 5 log)", "Normal", 0
        
        unit_logs['tanggal'] = pd.to_datetime(unit_logs['tanggal'])
        unit_logs = unit_logs.sort_values('tanggal')
        
        # Get latest readings
        latest = unit_logs.iloc[-1]
        readings = {
            'amp': latest['amp_kompresor'] if 'amp_kompresor' in latest else 15,
            'delta_t': latest['delta_t'] if 'delta_t' in latest else 10,
            'low_p': latest['low_p'] if 'low_p' in latest else 140,
            'high_p': latest['high_p'] if 'high_p' in latest else 350,
            'temp_outdoor': latest['temp_outdoor'] if 'temp_outdoor' in latest else 32
        }
        
        # ML prediction
        ml_health, conf_interval, is_anomaly, anomaly_score = ml_engine.predict_health_score(
            asset_id, readings, logs
        )
        
        # RUL prediction
        days_to_fail, rul_confidence, fail_date = ml_engine.predict_remaining_life(asset_id, logs)
        
        # Determine prediction message
        if days_to_fail is not None and days_to_fail < float('inf'):
            if days_to_fail > 0:
                if fail_date:
                    pred_msg = fail_date.strftime('%d %b %Y')
                else:
                    pred_msg = f"{int(days_to_fail)} hari lagi"
            else:
                pred_msg = "SEGERA - Sudah Kritis!"
        else:
            pred_msg = "Kondisi Stabil/Membaik"
        
        # Determine status
        status = "Normal"
        if is_anomaly:
            status = "ML Anomali Terdeteksi"
        
        # Anomaly detection
        anomalies, severity = ml_engine.detect_anomalies_realtime(readings, asset_id, logs)
        if severity in ['Critical', 'High']:
            status = f"Anomali {severity}"
        
        confidence = 85 if ml_health is not None else 60
        
        return pred_msg, status, confidence
        
    except Exception as e:
        return "Error Analisis", "Error", 0


def show_ai_dashboard():
    """Display AI Dashboard"""
    
    st.title("BPF Smart Maintenance Analytics - AC")
    
    # Initialize
    db_engine = DatabaseEngine()
    crud = CRUDOperations(db_engine)
    mode = st.session_state.get('db_mode', 'real')
    
    assets = crud.get_assets(mode)
    logs = crud.get_all_logs(mode)
    
    # Initialize ML Engine
    if 'ml_engine' not in st.session_state:
        st.session_state.ml_engine = PredictiveMaintenanceEngine(mode)
    
    ml_engine = st.session_state.ml_engine
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Unit AC", len(assets))
    with col2:
        st.metric("Total Log Maintenance", len(logs))
    with col3:
        if not logs.empty and 'health_score' in logs.columns:
            avg_health = logs['health_score'].mean()
            st.metric("Rata-rata Health Score", f"{avg_health:.1f}%")
        else:
            st.metric("Rata-rata Health Score", "N/A")
    with col4:
        if not logs.empty and 'tanggal' in logs.columns:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            recent = logs[logs['tanggal'] > (datetime.now() - timedelta(days=30))]
            st.metric("Log 30 Hari Terakhir", len(recent))
        else:
            st.metric("Log 30 Hari Terakhir", 0)
    
    st.markdown("---")
    
    # Tabs
    tab_ai, tab_ml, tab_analytics = st.tabs([
        "AI Prediksi", 
        "ML Analysis", 
        "Statistik Lanjutan"
    ])
    
    with tab_ai:
        st.subheader("Estimasi Kerusakan & Kesiapan Unit AC")
        
        show_anomaly_only = st.checkbox("Tampilkan Hanya Unit dengan Anomali")
        
        assets_list = []
        for _, asset in assets.iterrows():
            asset_id = asset['asset_id']
            pred, anomaly, confidence = analyze_predictive_maintenance(
                asset_id, ml_engine, crud, mode
            )
            
            asset_logs = logs[logs['asset_id'] == asset_id] if not logs.empty else pd.DataFrame()
            latest_health = asset_logs['health_score'].iloc[-1] if not asset_logs.empty else 100
            
            # Get anomalies
            latest_readings = {}
            if not asset_logs.empty:
                latest = asset_logs.iloc[-1]
                latest_readings = {
                    'amp_kompresor': latest.get('amp_kompresor', 0),
                    'delta_t': latest.get('delta_t', 0),
                    'low_p': latest.get('low_p', 140)
                }
            
            anomalies_detected, severity = ml_engine.detect_anomalies_realtime(
                latest_readings, asset_id, logs
            )
            
            assets_list.append({
                'asset_id': asset_id,
                'prediction': pred,
                'anomaly': anomaly,
                'confidence': confidence,
                'health_score': latest_health,
                'location': asset['lokasi'],
                'anomalies': anomalies_detected,
                'severity': severity
            })
        
        if show_anomaly_only:
            assets_list = [a for a in assets_list if a['severity'] in ['Critical', 'High', 'Medium']]
        
        # Display in grid
        for i in range(0, len(assets_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(assets_list):
                    asset = assets_list[i + j]
                    with cols[j]:
                        # Determine colors
                        if asset['severity'] == 'Critical':
                            border_color = "#dc3545"
                            bg_color = "#fff5f5"
                        elif asset['severity'] == 'High':
                            border_color = "#FF6B6B"
                            bg_color = "#FFF5F5"
                        elif asset['health_score'] < 70:
                            border_color = "#FFD93D"
                            bg_color = "#FFFBF0"
                        else:
                            border_color = "#51CF66"
                            bg_color = "#F0FFF4"
                        
                        confidence_stars = "***" if asset['confidence'] > 70 else "**" if asset['confidence'] > 50 else "*"
                        
                        # Gauge chart
                        if asset['health_score'] > 0:
                            fig_gauge = create_health_gauge(asset['health_score'], "")
                            st.plotly_chart(fig_gauge, use_container_width=True, 
                                          key=f"gauge_{asset['asset_id']}_{i}_{j}")
                        
                        st.markdown(f"""
                        <div style="background:{bg_color}; padding:15px; border-left:5px solid {border_color}; 
                                   border-radius:8px; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between;">
                                <b style="color:#003366;">{asset['asset_id']}</b>
                                <span>{confidence_stars}</span>
                            </div>
                            <p style="margin:5px 0; color:#666; font-size:0.9em;">{asset['location']}</p>
                            <p style="margin:5px 0;"><b style="color:#CC0000;">{asset['prediction']}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if asset['anomalies']:
                            with st.expander(f"Anomali ({asset['severity']})"):
                                for a in asset['anomalies']:
                                    st.markdown(f"- **{a['parameter']}**: {a['message']}")
    
    with tab_ml:
        st.subheader("Machine Learning Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Train/Retrain ML Models", use_container_width=True):
                with st.spinner("Training ML models..."):
                    success = ml_engine.train_models(logs)
                    if success:
                        st.success("ML Models trained successfully!")
                    else:
                        st.warning("Need at least 50 logs to train models")
        
        with col2:
            if st.button("Load Existing Models", use_container_width=True):
                success = ml_engine.load_or_train_models(logs)
                if success:
                    st.success("ML Models loaded successfully!")
                else:
                    st.warning("No existing models found")
        
        st.markdown("---")
        
        selected_asset = st.selectbox("Pilih Asset untuk ML Analysis", assets['asset_id'].tolist())
        
        if selected_asset:
            asset_logs = logs[logs['asset_id'] == selected_asset]
            
            if not asset_logs.empty:
                latest = asset_logs.iloc[-1]
                readings = {
                    'amp': latest.get('amp_kompresor', 15),
                    'delta_t': latest.get('delta_t', 10),
                    'low_p': latest.get('low_p', 140),
                    'high_p': latest.get('high_p', 350),
                    'temp_outdoor': latest.get('temp_outdoor', 32)
                }
                
                ml_health, conf_interval, is_anomaly, anomaly_score = ml_engine.predict_health_score(
                    selected_asset, readings, logs
                )
                
                if ml_health is not None:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("ML Predicted Health Score", f"{ml_health:.1f}%")
                        if conf_interval:
                            st.metric("Confidence Interval", 
                                    f"[{conf_interval[0]:.1f}% - {conf_interval[1]:.1f}%]")
                    
                    with col2:
                        if is_anomaly:
                            st.error(f"Anomaly Detected (Score: {anomaly_score:.3f})")
                        else:
                            st.success(f"Normal Pattern (Score: {anomaly_score:.3f})")
                
                days_to_fail, rul_confidence, fail_date = ml_engine.predict_remaining_life(selected_asset, logs)
                
                if days_to_fail is not None and days_to_fail < float('inf'):
                    st.info(f"**Remaining Useful Life:** {int(days_to_fail)} hari (Confidence: {rul_confidence:.1f}%)")
                    if fail_date:
                        st.info(f"**Estimated Failure Date:** {fail_date.strftime('%d %B %Y')}")
                
                # Similar assets
                similar = ml_engine.get_similar_assets_pattern(selected_asset, logs)
                if similar:
                    st.markdown("**Similar Assets Pattern:**")
                    for s in similar:
                        st.markdown(f"- {s['asset_id']}: Similarity {s['similarity']}%, "
                                  f"Avg Health: {s['avg_health']}%, Trend: {s['trend']}")
    
    with tab_analytics:
        st.subheader("Analisis Tren & Statistik")
        
        if not logs.empty:
            logs_copy = logs.copy()
            if 'tanggal' in logs_copy.columns:
                logs_copy['tanggal'] = pd.to_datetime(logs_copy['tanggal'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Distribusi Health Score")
                fig_dist = create_health_distribution_chart(logs_copy)
                if fig_dist:
                    st.plotly_chart(fig_dist, use_container_width=True)
            
            with col2:
                st.markdown("### Efisiensi (Delta T) per Unit")
                if 'delta_t' in logs_copy.columns:
                    avg_delta = logs_copy.groupby('asset_id')['delta_t'].mean().sort_values()
                    st.bar_chart(avg_delta)
            
            if len(logs_copy) > 10:
                st.markdown("### Korelasi Antar Parameter")
                fig_heatmap = create_correlation_heatmap(logs_copy)
                st.plotly_chart(fig_heatmap, use_container_width=True)