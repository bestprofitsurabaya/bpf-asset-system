"""
Executive Dashboard Module
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import database.crud_ac as db_ac
import database.crud_vehicles as db_vehicles
from utils.alerts import generate_maintenance_recommendations
from utils.helpers import format_currency
from utils.pdf_generator import generate_executive_summary_pdf, get_pdf_download_link


def generate_executive_summary():
    """Generate executive summary report"""
    
    logs = db_ac.get_all_logs(mode=st.session_state.db_mode)
    vehicles = db_vehicles.get_vehicles(mode=st.session_state.db_mode)
    services = db_vehicles.get_vehicle_services(mode=st.session_state.db_mode)
    assets = db_ac.get_assets(mode=st.session_state.db_mode)
    
    total_ac = len(assets)
    total_vehicles = len(vehicles)
    total_active_vehicles = len(vehicles[vehicles['status'] == 'Aktif']) if not vehicles.empty and 'status' in vehicles.columns else 0
    total_ac_maintenance = len(logs)
    total_vehicle_services = len(services)
    
    if not logs.empty and 'health_score' in logs.columns:
        avg_ac_health = logs['health_score'].mean()
        if pd.isna(avg_ac_health):
            avg_ac_health = 0
    else:
        avg_ac_health = 0
    
    ac_cost = logs['sparepart_cost'].sum() if not logs.empty and 'sparepart_cost' in logs.columns else 0
    vehicle_cost = services['cost'].sum() if not services.empty and 'cost' in services.columns else 0
    total_cost = ac_cost + vehicle_cost
    
    cost_display = format_currency(total_cost)
    
    summary = {
        'report_date': datetime.now().strftime('%d %B %Y'),
        'period': datetime.now().strftime('%B %Y'),
        'ac_units': total_ac,
        'vehicles': total_vehicles,
        'active_vehicles': total_active_vehicles,
        'total_ac_maintenance': total_ac_maintenance,
        'total_vehicle_services': total_vehicle_services,
        'total_cost': total_cost,
        'cost_display': cost_display,
        'avg_ac_health': avg_ac_health,
        'critical_ac_units': [],
        'vehicle_health_summary': [],
        'recommendations_count': 0,
        'unread_notifications': 0
    }
    
    if not logs.empty and 'health_score' in logs.columns:
        try:
            logs_copy = logs.copy()
            if 'tanggal' in logs_copy.columns:
                logs_copy['tanggal'] = pd.to_datetime(logs_copy['tanggal'], errors='coerce')
                logs_copy = logs_copy.dropna(subset=['tanggal'])
                
                if not logs_copy.empty:
                    latest_logs = logs_copy.sort_values('tanggal').groupby('asset_id').tail(1)
                    critical = latest_logs[latest_logs['health_score'] < 60]
                    
                    for _, row in critical.iterrows():
                        asset_id = row['asset_id']
                        asset_info = assets[assets['asset_id'] == asset_id] if not assets.empty else pd.DataFrame()
                        location = asset_info['lokasi'].iloc[0] if not asset_info.empty else 'Unknown'
                        
                        summary['critical_ac_units'].append({
                            'asset_id': asset_id,
                            'health_score': row['health_score'],
                            'location': location
                        })
        except Exception as e:
            pass
    
    if not vehicles.empty:
        for _, v in vehicles.head(5).iterrows():
            try:
                from modules.dashboard_vehicle import analyze_vehicle_health
                health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
                if not health.get('error', False):
                    summary['vehicle_health_summary'].append({
                        'vehicle_id': v['vehicle_id'],
                        'name': f"{v['brand']} {v['model']}",
                        'health_score': health.get('health_score', 0),
                        'status': health.get('status', 'Unknown')
                    })
            except Exception:
                pass
    
    try:
        recs = db_ac.get_recommendations(mode=st.session_state.db_mode)
        summary['recommendations_count'] = len(recs)
    except:
        pass
    
    try:
        notifs = db_ac.get_notifications(unread_only=True, mode=st.session_state.db_mode)
        summary['unread_notifications'] = len(notifs)
    except:
        pass
    
    return summary


def render_executive_dashboard():
    """Render Executive Dashboard"""
    
    st.title("Executive Dashboard")
    
    summary = generate_executive_summary()
    recommendations = generate_maintenance_recommendations(mode=st.session_state.db_mode)
    
    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #003366 0%, #002244 100%); 
                color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px;">
        <h2 style="margin:0; color:white;">Executive Summary - {summary['period']}</h2>
        <p style="margin:5px 0 0 0; opacity:0.9;">Laporan per {summary['report_date']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Unit AC", summary['ac_units'])
    with col2:
        st.metric("Kendaraan", summary['vehicles'])
    with col3:
        st.metric("Avg Health Score", f"{summary['avg_ac_health']:.1f}%")
    with col4:
        st.metric("Total Biaya", summary['cost_display'])
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Maintenance AC", summary['total_ac_maintenance'])
    with col2:
        st.metric("Servis Kendaraan", summary['total_vehicle_services'])
    with col3:
        st.metric("Kendaraan Aktif", summary['active_vehicles'])
    with col4:
        notif_value = summary['unread_notifications']
        if notif_value > 0:
            st.metric("Notifikasi", notif_value, delta=f"{notif_value} belum dibaca", delta_color="inverse")
        else:
            st.metric("Notifikasi", notif_value)
    
    st.markdown("---")
    
    # Critical Units and Vehicle Health
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Unit AC Kritis")
        critical_units = summary.get('critical_ac_units', [])
        if critical_units:
            for unit in critical_units:
                health_score = unit.get('health_score', 0)
                asset_id = unit.get('asset_id', 'Unknown')
                location = unit.get('location', 'Unknown')
                
                if health_score < 40:
                    st.error(f"**{asset_id}** - {location}\n\nHealth: {health_score:.0f}% (SEVERE)")
                elif health_score < 50:
                    st.error(f"**{asset_id}** - {location}\n\nHealth: {health_score:.0f}% (CRITICAL)")
                else:
                    st.warning(f"**{asset_id}** - {location}\n\nHealth: {health_score:.0f}% (WARNING)")
        else:
            st.success("Tidak ada unit AC dalam kondisi kritis")
    
    with col2:
        st.subheader("Status Kendaraan")
        vehicle_summary = summary.get('vehicle_health_summary', [])
        if vehicle_summary:
            for v in vehicle_summary:
                health_score = v.get('health_score', 0)
                vehicle_id = v.get('vehicle_id', 'Unknown')
                name = v.get('name', 'Unknown')
                status = v.get('status', 'Unknown')
                
                if health_score >= 80:
                    st.success(f"**{vehicle_id}** - {name}\n\nHealth: {health_score:.0f}% - {status}")
                elif health_score >= 60:
                    st.warning(f"**{vehicle_id}** - {name}\n\nHealth: {health_score:.0f}% - {status}")
                elif health_score >= 40:
                    st.warning(f"**{vehicle_id}** - {name}\n\nHealth: {health_score:.0f}% - {status}")
                else:
                    st.error(f"**{vehicle_id}** - {name}\n\nHealth: {health_score:.0f}% - {status}")
        else:
            st.info("Data kendaraan tidak tersedia")
    
    st.markdown("---")
    
    # Top Recommendations
    st.subheader("Rekomendasi Maintenance Prioritas")
    
    if recommendations:
        pending_recs = [r for r in recommendations if r.get('status', 'Pending') == 'Pending']
        
        if pending_recs:
            for rec in pending_recs[:5]:
                priority = rec.get('priority', 'Normal')
                asset_id = rec.get('asset_id', 'Unknown')
                urgency_days = rec.get('urgency_days', 0)
                estimated_cost = rec.get('estimated_cost', 0)
                actions = rec.get('actions', [])
                
                if priority == 'Critical':
                    expander_label = f"{asset_id} - PRIORITAS: CRITICAL (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
                elif priority == 'High':
                    expander_label = f"{asset_id} - Prioritas: High (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
                elif priority == 'Medium':
                    expander_label = f"{asset_id} - Prioritas: Medium (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
                else:
                    expander_label = f"{asset_id} - Prioritas: Normal (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
                
                with st.expander(expander_label):
                    st.markdown("**Tindakan yang Direkomendasikan:**")
                    for action in actions:
                        st.markdown(f"- {action}")
                    st.markdown(f"**Estimasi Biaya:** Rp {estimated_cost:,.0f}")
        else:
            st.success("Semua rekomendasi sudah ditindaklanjuti!")
    else:
        st.success("Tidak ada rekomendasi maintenance saat ini.")
    
    st.markdown("---")
    
    # PDF Download
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Download Executive Summary PDF", use_container_width=True):
            pdf = generate_executive_summary_pdf(summary)
            filename = f"Executive_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.markdown(get_pdf_download_link(pdf, filename), unsafe_allow_html=True)
            st.success("PDF berhasil dibuat! Klik link di atas untuk download.")