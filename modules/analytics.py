"""
Interactive Analytics Module
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

import database.crud_ac as db_ac
import database.crud_vehicles as db_vehicles
from utils.visualizations import (
    create_health_gauge, create_degradation_timeline, create_radar_chart,
    create_3d_scatter, create_cost_analysis_charts, create_monthly_trend_chart
)
from utils.anomaly import detect_anomalies_realtime


def render_interactive_analytics():
    """Render Interactive Analytics"""
    
    st.title("Interactive Analytics & Visualization")
    
    logs = db_ac.get_all_logs(mode=st.session_state.db_mode)
    assets = db_ac.get_assets(mode=st.session_state.db_mode)
    
    if logs.empty:
        st.warning("Belum ada data maintenance untuk analisis.")
        return
    
    logs['tanggal'] = pd.to_datetime(logs['tanggal'])
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Health Gauge",
        "Degradation Timeline",
        "Radar Analysis",
        "3D Scatter Plot",
        "Cost Analysis"
    ])
    
    with tab1:
        st.subheader("Health Score Gauge")
        
        selected_asset = st.selectbox("Pilih Asset", assets['asset_id'].tolist(), key="gauge_asset")
        
        asset_logs = logs[logs['asset_id'] == selected_asset]
        if not asset_logs.empty:
            latest_health = asset_logs['health_score'].iloc[-1]
            
            col1, col2 = st.columns([2, 1])
            with col1:
                fig_gauge = create_health_gauge(latest_health, f"Health Score - {selected_asset}")
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col2:
                st.markdown("### Informasi Asset")
                asset_info = assets[assets['asset_id'] == selected_asset].iloc[0]
                st.markdown(f"""
                - **Lokasi:** {asset_info['lokasi']}
                - **Merk:** {asset_info['merk']}
                - **Tipe:** {asset_info['tipe']}
                - **Kapasitas:** {asset_info['kapasitas']}
                - **Status:** {asset_info['status']}
                """)
                
                st.markdown("### Statistik")
                st.metric("Total Maintenance", len(asset_logs))
                st.metric("Rata-rata Health", f"{asset_logs['health_score'].mean():.1f}%")
                if 'delta_t' in asset_logs.columns:
                    st.metric("Rata-rata Delta T", f"{asset_logs['delta_t'].mean():.1f} C")
    
    with tab2:
        st.subheader("Degradation Timeline Analysis")
        
        selected_asset = st.selectbox("Pilih Asset untuk Timeline", assets['asset_id'].tolist(), key="timeline_asset")
        
        fig_timeline = create_degradation_timeline(selected_asset, logs)
        if fig_timeline:
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("Data tidak cukup untuk membuat timeline")
    
    with tab3:
        st.subheader("Multi-Parameter Radar Analysis")
        
        selected_asset = st.selectbox("Pilih Asset untuk Radar Analysis", assets['asset_id'].tolist(), key="radar_asset")
        
        asset_logs_radar = logs[logs['asset_id'] == selected_asset]
        if not asset_logs_radar.empty:
            latest = asset_logs_radar.iloc[-1].to_dict()
            fig_radar = create_radar_chart(latest, selected_asset)
            st.plotly_chart(fig_radar, use_container_width=True)
            
            anomalies, severity = detect_anomalies_realtime(
                {'amp_kompresor': latest.get('amp_kompresor', 0),
                 'delta_t': latest.get('delta_t', 0),
                 'low_p': latest.get('low_p', 140)},
                selected_asset,
                st.session_state.db_mode
            )
            
            if anomalies:
                st.markdown(f"### Anomali Terdeteksi (Severity: {severity})")
                for a in anomalies:
                    if a['severity'] == 'Critical':
                        st.error(f"**{a['parameter']}**: {a['message']}")
                    elif a['severity'] == 'High':
                        st.warning(f"**{a['parameter']}**: {a['message']}")
                    else:
                        st.info(f"**{a['parameter']}**: {a['message']}")
    
    with tab4:
        st.subheader("3D Multivariate Analysis")
        
        if len(logs) >= 10:
            fig_3d = create_3d_scatter(logs)
            st.plotly_chart(fig_3d, use_container_width=True)
            
            st.markdown("""
            **Interpretasi:**
            - **Sumbu X (Ampere):** Arus listrik kompresor
            - **Sumbu Y (Delta T):** Efisiensi pendinginan
            - **Sumbu Z (Health Score):** Skor kesehatan
            - **Warna:** Health Score (hijau = baik, merah = buruk)
            """)
        else:
            st.info("Data tidak cukup untuk 3D scatter plot (minimal 10 data point)")
    
    with tab5:
        st.subheader("Cost Analysis - Kendaraan")
        
        services = db_vehicles.get_vehicle_services(mode=st.session_state.db_mode)
        
        if not services.empty:
            fig_vehicle, fig_component = create_cost_analysis_charts(services)
            
            if fig_vehicle:
                st.plotly_chart(fig_vehicle, use_container_width=True)
            
            if fig_component:
                st.plotly_chart(fig_component, use_container_width=True)
            
            fig_trend = create_monthly_trend_chart(services)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Belum ada data servis kendaraan")