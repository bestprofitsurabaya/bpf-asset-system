"""
Print Reports Module (PDF Generation)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

import database.crud_ac as db_ac
import database.crud_vehicles as db_vehicles
from modules.dashboard_vehicle import analyze_vehicle_health
from modules.dashboard_executive import generate_executive_summary
from utils.pdf_generator import (
    generate_ac_report_pdf, generate_vehicle_report_pdf,
    generate_executive_summary_pdf, get_pdf_download_link
)


def render_print_reports():
    """Render Print Reports"""
    
    st.title("Cetak Laporan")
    
    report_type = st.selectbox("Pilih Jenis Laporan", [
        "Laporan Maintenance AC",
        "Laporan Status Kendaraan",
        "Executive Summary"
    ])
    
    if report_type == "Laporan Maintenance AC":
        logs = db_ac.get_all_logs(mode=st.session_state.db_mode)
        if not logs.empty:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            
            col1, col2 = st.columns(2)
            asset_filter = col1.selectbox("Pilih Asset", ["Semua"] + logs['asset_id'].unique().tolist())
            
            if asset_filter != "Semua":
                logs = logs[logs['asset_id'] == asset_filter]
            
            date_range = col2.selectbox("Periode", ["Semua", "30 Hari", "90 Hari", "1 Tahun"])
            
            if date_range == "30 Hari":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=30))]
            elif date_range == "90 Hari":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=90))]
            elif date_range == "1 Tahun":
                logs = logs[logs['tanggal'] > (datetime.now() - timedelta(days=365))]
            
            if st.button("Generate PDF Report"):
                pdf = generate_ac_report_pdf(logs, asset_filter, date_range)
                filename = f"Laporan_AC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.markdown(get_pdf_download_link(pdf, filename), unsafe_allow_html=True)
                st.success("PDF berhasil dibuat!")
        else:
            st.info("Belum ada data maintenance AC")
    
    elif report_type == "Laporan Status Kendaraan":
        vehicles = db_vehicles.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            sel_v = st.selectbox("Pilih Kendaraan", ["Semua"] + vehicles['vehicle_id'].tolist())
            
            vehicles_to_report = vehicles if sel_v == "Semua" else vehicles[vehicles['vehicle_id'] == sel_v]
            
            health_data = {}
            for _, v in vehicles_to_report.iterrows():
                health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
                health_data[v['vehicle_id']] = health
            
            if st.button("Generate PDF Report"):
                pdf = generate_vehicle_report_pdf(vehicles_to_report, health_data)
                filename = f"Laporan_Kendaraan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.markdown(get_pdf_download_link(pdf, filename), unsafe_allow_html=True)
                st.success("PDF berhasil dibuat!")
        else:
            st.info("Belum ada data kendaraan")
    
    elif report_type == "Executive Summary":
        summary = generate_executive_summary()
        
        st.markdown("### Preview Executive Summary")
        st.json(summary)
        
        if st.button("Generate Executive Summary PDF"):
            pdf = generate_executive_summary_pdf(summary)
            filename = f"Executive_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.markdown(get_pdf_download_link(pdf, filename), unsafe_allow_html=True)
            st.success("PDF Executive Summary berhasil dibuat!")