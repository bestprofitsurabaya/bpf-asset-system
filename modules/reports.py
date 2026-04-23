"""
Analytics & Reports Module
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import database.crud_ac as db_ac
import database.crud_vehicles as db_vehicles


def render_analytics_reports():
    """Render Analytics & Reports"""
    
    st.title("Analytics & Reports")
    
    tab_ac, tab_vehicle = st.tabs(["AC Analytics", "Vehicle Analytics"])
    
    with tab_ac:
        logs = db_ac.get_all_logs(mode=st.session_state.db_mode)
        
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Tanggal Mulai", logs['tanggal'].min(), key="ac_start")
            end_date = col2.date_input("Tanggal Akhir", logs['tanggal'].max(), key="ac_end")
            
            filtered_logs = logs[(logs['tanggal'] >= pd.Timestamp(start_date)) &
                                (logs['tanggal'] <= pd.Timestamp(end_date))]
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Maintenance", len(filtered_logs))
            col2.metric("Rata-rata Health", f"{filtered_logs['health_score'].mean():.1f}%" if 'health_score' in filtered_logs.columns else "N/A")
            col3.metric("Rata-rata Delta T", f"{filtered_logs['delta_t'].mean():.1f} C" if 'delta_t' in filtered_logs.columns else "N/A")
            col4.metric("Total Biaya", f"Rp {filtered_logs['sparepart_cost'].sum():,.0f}" if 'sparepart_cost' in filtered_logs.columns else "Rp 0")
            
            if st.button("Export CSV (AC)"):
                csv = filtered_logs.to_csv(index=False)
                st.download_button("Download CSV", csv, f"ac_report_{start_date}_{end_date}.csv", "text/csv")
        else:
            st.info("Belum ada data maintenance AC")
    
    with tab_vehicle:
        services = db_vehicles.get_vehicle_services(mode=st.session_state.db_mode)
        
        if not services.empty:
            services['service_date'] = pd.to_datetime(services['service_date'])
            
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Tanggal Mulai", services['service_date'].min(), key="vh_start")
            end_date = col2.date_input("Tanggal Akhir", services['service_date'].max(), key="vh_end")
            
            filtered = services[(services['service_date'] >= pd.Timestamp(start_date)) &
                              (services['service_date'] <= pd.Timestamp(end_date))]
            
            st.metric("Total Biaya Servis", f"Rp {filtered['cost'].sum():,.0f}" if 'cost' in filtered.columns else "Rp 0")
            
            if st.button("Export CSV (Kendaraan)"):
                csv = filtered.to_csv(index=False)
                st.download_button("Download CSV", csv, f"vehicle_report_{start_date}_{end_date}.csv", "text/csv")
        else:
            st.info("Belum ada data servis kendaraan")