"""
AC Dashboard Module with AI Predictions
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import database.crud_ac as db_ac
from utils.anomaly import detect_anomalies_realtime, analyze_predictive_maintenance
from utils.visualizations import create_health_gauge, create_correlation_heatmap
from utils.alerts import check_alerts_and_notify
from utils.ml_engine import PredictiveMaintenanceEngine


def render_ac_dashboard():
    """Render AI Dashboard for AC"""
    
    st.title("BPF Smart Maintenance Analytics - AC")
    
    assets = db_ac.get_assets(mode=st.session_state.db_mode)
    logs = db_ac.get_all_logs(mode=st.session_state.db_mode)
    
    # Initialize ML Engine
    if 'ml_engine' not in st.session_state or st.session_state.ml_engine is None:
        st.session_state.ml_engine = PredictiveMaintenanceEngine(st.session_state.db_mode)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Unit AC", len(assets))
    with col2:
        st.metric("Total Log Maintenance", len(logs))
    with col3:
        if not logs.empty:
            avg_health = logs['health_score'].mean()
            st.metric("Rata-rata Health Score", f"{avg_health:.1f}%")
        else:
            st.metric("Rata-rata Health Score", "N/A")
    with col4:
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            recent_logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=30))]
            st.metric("Log 30 Hari Terakhir", len(recent_logs))
        else:
            st.metric("Log 30 Hari Terakhir", 0)
    
    st.markdown("---")
    
    # Alerts
    alerts = check_alerts_and_notify(mode=st.session_state.db_mode)
    if alerts:
        st.markdown("### Alert & Notifikasi")
        alert_cols = st.columns(min(3, len(alerts)))
        for i, alert in enumerate(alerts[:3]):
            with alert_cols[i]:
                if alert['type'] == 'critical':
                    st.error(f"**{alert['asset_id']}**\n\n{alert['message']}\n\n*{alert['action']}*")
                else:
                    st.warning(f"**{alert['asset_id']}**\n\n{alert['message']}\n\n*{alert['action']}*")
    
    st.markdown("---")
    
    tab_ai, tab_ml, tab_analytics = st.tabs(["AI Prediksi", "ML Analysis", "Statistik Lanjutan"])
    
    with tab_ai:
        st.subheader("Estimasi Kerusakan & Kesiapan Unit AC (AI)")
        
        show_anomaly_only = st.checkbox("Tampilkan Hanya Unit dengan Anomali")
        
        assets_list = []
        for _, asset in assets.iterrows():
            as_id = asset['asset_id']
            pred, anomaly, confidence = analyze_predictive_maintenance(
                as_id, st.session_state.ml_engine, st.session_state.db_mode
            )
            
            asset_logs = logs[logs['asset_id'] == as_id] if not logs.empty else pd.DataFrame()
            latest_health = asset_logs['health_score'].iloc[-1] if not asset_logs.empty else 100
            
            latest_readings = {}
            if not asset_logs.empty:
                latest = asset_logs.iloc[-1]
                latest_readings = {
                    'amp_kompresor': latest['amp_kompresor'] if 'amp_kompresor' in latest else 0,
                    'delta_t': latest['delta_t'] if 'delta_t' in latest else 0,
                    'low_p': latest['low_p'] if 'low_p' in latest else 140
                }
            anomalies_detected, severity = detect_anomalies_realtime(
                latest_readings, as_id, st.session_state.db_mode
            )
            
            assets_list.append({
                'asset_id': as_id,
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
        
        for i in range(0, len(assets_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(assets_list):
                    asset = assets_list[i + j]
                    with cols[j]:
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
                        
                        if asset['health_score'] > 0:
                            fig_gauge = create_health_gauge(asset['health_score'], "")
                            st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_{asset['asset_id']}_{i}_{j}")
                        
                        st.markdown(f"""
                        <div style="background:{bg_color}; padding:15px; border-left: 5px solid {border_color}; border-radius:8px; margin-bottom:10px;">
                            <div style="display: flex; justify-content: space-between;">
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
        
        if st.button("Train/Retrain ML Models"):
            with st.spinner("Training ML models..."):
                st.session_state.ml_engine = PredictiveMaintenanceEngine(st.session_state.db_mode)
            st.success("ML Models trained successfully!")
        
        selected_asset_ml = st.selectbox("Pilih Asset untuk ML Analysis", assets['asset_id'].tolist(), key="ml_asset")
        
        if selected_asset_ml:
            asset_logs = logs[logs['asset_id'] == selected_asset_ml]
            
            if not asset_logs.empty:
                latest = asset_logs.iloc[-1]
                readings = {
                    'amp': latest['amp_kompresor'] if 'amp_kompresor' in latest else 15,
                    'delta_t': latest['delta_t'] if 'delta_t' in latest else 10,
                    'low_p': latest['low_p'] if 'low_p' in latest else 140,
                    'high_p': latest['high_p'] if 'high_p' in latest else 350,
                    'temp_outdoor': latest['temp_outdoor'] if 'temp_outdoor' in latest else 32
                }
                
                ml_health, conf_interval, is_anomaly, anomaly_score = st.session_state.ml_engine.predict_health_score(
                    selected_asset_ml, readings
                )
                
                if ml_health is not None:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("ML Predicted Health Score", f"{ml_health:.1f}%")
                        if conf_interval is not None:
                            st.metric("Confidence Interval", f"[{conf_interval[0]:.1f}% - {conf_interval[1]:.1f}%]")
                    
                    with col2:
                        if is_anomaly:
                            st.error(f"Anomaly Detected (Score: {anomaly_score:.3f})")
                        else:
                            st.success(f"Normal Pattern (Score: {anomaly_score:.3f})")
                
                days_to_fail, rul_confidence, fail_date = st.session_state.ml_engine.predict_remaining_life(selected_asset_ml)
                
                if days_to_fail is not None and days_to_fail < float('inf'):
                    st.info(f"**Remaining Useful Life:** {int(days_to_fail)} hari (Confidence: {rul_confidence:.1f}%)")
                    if fail_date:
                        st.info(f"**Estimated Failure Date:** {fail_date.strftime('%d %B %Y')}")
                
                similar = st.session_state.ml_engine.get_similar_assets_pattern(selected_asset_ml)
                if similar:
                    st.markdown("**Similar Assets Pattern:**")
                    for s in similar:
                        st.markdown(f"- {s['asset_id']}: Similarity {s['similarity']}%, Avg Health: {s['avg_health']}%, Trend: {s['trend']}")
    
    with tab_analytics:
        st.subheader("Analisis Tren & Statistik")
        
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Distribusi Health Score")
                health_bins = [0, 50, 70, 85, 100]
                health_labels = ['Kritis (<50%)', 'Perhatian (50-70%)', 'Baik (70-85%)', 'Sangat Baik (>85%)']
                logs['health_category'] = pd.cut(logs['health_score'], bins=health_bins, labels=health_labels)
                health_dist = logs['health_category'].value_counts()
                st.bar_chart(health_dist)
            
            with col2:
                st.markdown("### Efisiensi (Delta T) per Unit")
                if 'delta_t' in logs.columns:
                    avg_delta_t = logs.groupby('asset_id')['delta_t'].mean().sort_values()
                    st.bar_chart(avg_delta_t)
            
            if len(logs) > 10:
                st.markdown("### Korelasi Antar Parameter")
                fig_heatmap = create_correlation_heatmap(logs)
                st.plotly_chart(fig_heatmap, use_container_width=True)