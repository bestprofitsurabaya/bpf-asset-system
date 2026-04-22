"""
Executive Dashboard Page
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.crud import CRUDOperations
from src.database.engine import DatabaseEngine
from src.reports.pdf_generator import PDFGenerator
from src.utils.helpers import format_currency, get_health_color, get_health_status
from src.ml.predictive_engine import PredictiveMaintenanceEngine

def analyze_vehicle_health(vehicle_id: str, crud: CRUDOperations, mode: str) -> dict:
    """Analyze vehicle health"""
    try:
        services = crud.get_vehicle_services(vehicle_id, mode)
        vehicle = crud.get_vehicle_by_id(vehicle_id, mode)
        
        if not vehicle:
            return {"status": "Data tidak ditemukan", "health_score": 0, "error": True}
        
        current_odometer = vehicle.get('last_odometer', 0)
        purchase_date = pd.to_datetime(vehicle.get('purchase_date', datetime.now()))
        months_used = (datetime.now().year - purchase_date.year) * 12 + (datetime.now().month - purchase_date.month)
        
        total_cost = services['cost'].sum() if not services.empty else 0
        
        components = crud.get_vehicle_components(mode)
        next_services = []
        
        for _, comp in components.iterrows():
            comp_services = services[services['component_name'] == comp['component_name']]
            
            if not comp_services.empty:
                last_service = comp_services.iloc[0]
                last_date = pd.to_datetime(last_service['service_date'])
                last_odometer = last_service['odometer']
                months_since = (datetime.now().year - last_date.year) * 12 + (datetime.now().month - last_date.month)
                km_since = current_odometer - last_odometer
            else:
                months_since = months_used
                km_since = current_odometer
            
            km_percent = 0
            month_percent = 0
            
            if comp['standard_life_km'] > 0:
                km_percent = min(100, (km_since / (comp['standard_life_km'] * 0.9)) * 100)
            
            if comp['standard_life_months'] > 0:
                month_percent = min(100, (months_since / (comp['standard_life_months'] * 0.9)) * 100)
            
            max_percent = max(km_percent, month_percent)
            next_services.append({'usage_percent': max_percent})
        
        if next_services:
            health_score = max(0, 100 - sum(s['usage_percent'] for s in next_services) / len(next_services))
        else:
            health_score = 100
        
        if health_score >= 80:
            status = "Sangat Baik"
        elif health_score >= 60:
            status = "Baik"
        elif health_score >= 40:
            status = "Perlu Perhatian"
        else:
            status = "Kritis"
        
        return {
            "status": status,
            "health_score": health_score,
            "error": False,
            "maintenance_cost": total_cost
        }
        
    except Exception as e:
        return {"status": "Error", "health_score": 0, "error": True}


def generate_executive_summary(crud: CRUDOperations, mode: str) -> dict:
    """Generate executive summary"""
    
    logs = crud.get_all_logs(mode)
    vehicles = crud.get_vehicles(mode)
    services = crud.get_vehicle_services(mode=mode)
    assets = crud.get_assets(mode)
    
    total_ac = len(assets)
    total_vehicles = len(vehicles)
    total_active = len(vehicles[vehicles['status'] == 'Aktif']) if not vehicles.empty else 0
    total_ac_logs = len(logs)
    total_services = len(services)
    
    avg_health = logs['health_score'].mean() if not logs.empty and 'health_score' in logs.columns else 0
    
    ac_cost = logs['sparepart_cost'].sum() if not logs.empty and 'sparepart_cost' in logs.columns else 0
    vehicle_cost = services['cost'].sum() if not services.empty and 'cost' in services.columns else 0
    total_cost = ac_cost + vehicle_cost
    
    cost_display = format_currency(total_cost)
    
    summary = {
        'report_date': datetime.now().strftime('%d %B %Y'),
        'period': datetime.now().strftime('%B %Y'),
        'ac_units': total_ac,
        'vehicles': total_vehicles,
        'active_vehicles': total_active,
        'total_ac_maintenance': total_ac_logs,
        'total_vehicle_services': total_services,
        'total_cost': total_cost,
        'cost_display': cost_display,
        'avg_ac_health': avg_health,
        'critical_ac_units': [],
        'vehicle_health_summary': [],
        'recommendations_count': 0,
        'unread_notifications': 0
    }
    
    # Critical AC units
    if not logs.empty and 'health_score' in logs.columns:
        logs_copy = logs.copy()
        if 'tanggal' in logs_copy.columns:
            logs_copy['tanggal'] = pd.to_datetime(logs_copy['tanggal'], errors='coerce')
            logs_copy = logs_copy.dropna(subset=['tanggal'])
            
            if not logs_copy.empty:
                latest_logs = logs_copy.sort_values('tanggal').groupby('asset_id').tail(1)
                critical = latest_logs[latest_logs['health_score'] < 60]
                
                for _, row in critical.iterrows():
                    asset_info = assets[assets['asset_id'] == row['asset_id']]
                    location = asset_info['lokasi'].iloc[0] if not asset_info.empty else 'Unknown'
                    
                    summary['critical_ac_units'].append({
                        'asset_id': row['asset_id'],
                        'health_score': row['health_score'],
                        'location': location
                    })
    
    # Vehicle health
    for _, v in vehicles.head(5).iterrows():
        health = analyze_vehicle_health(v['vehicle_id'], crud, mode)
        if not health.get('error', False):
            summary['vehicle_health_summary'].append({
                'vehicle_id': v['vehicle_id'],
                'name': f"{v['brand']} {v['model']}",
                'health_score': health['health_score'],
                'status': health['status']
            })
    
    # Recommendations count
    recs = crud.get_recommendations(mode=mode)
    summary['recommendations_count'] = len(recs)
    
    # Notifications
    notifs = crud.get_notifications(unread_only=True, mode=mode)
    summary['unread_notifications'] = len(notifs)
    
    return summary


def show_executive_dashboard():
    """Display executive dashboard"""
    
    st.title("Executive Dashboard")
    
    # Initialize
    db_engine = DatabaseEngine()
    crud = CRUDOperations(db_engine)
    mode = st.session_state.get('db_mode', 'real')
    
    # Generate summary
    summary = generate_executive_summary(crud, mode)
    recommendations = crud.get_recommendations(mode=mode)
    
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
    
    # Secondary Metrics
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
        st.metric("Notifikasi", notif_value, delta=f"{notif_value} belum dibaca" if notif_value > 0 else None)
    
    st.markdown("---")
    
    # Critical Units and Vehicle Status
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Unit AC Kritis")
        
        if summary['critical_ac_units']:
            for unit in summary['critical_ac_units']:
                health = unit['health_score']
                if health < 40:
                    st.error(f"RED **{unit['asset_id']}** - {unit['location']} - Health: {health:.0f}% (SEVERE)")
                elif health < 50:
                    st.error(f"ORANGE **{unit['asset_id']}** - {unit['location']} - Health: {health:.0f}% (CRITICAL)")
                else:
                    st.warning(f"YELLOW **{unit['asset_id']}** - {unit['location']} - Health: {health:.0f}% (WARNING)")
        else:
            st.success("GREEN Tidak ada unit AC dalam kondisi kritis")
    
    with col2:
        st.subheader("Status Kendaraan")
        
        if summary['vehicle_health_summary']:
            for v in summary['vehicle_health_summary']:
                health = v['health_score']
                if health >= 80:
                    st.success(f"GREEN **{v['vehicle_id']}** - {v['name']} - Health: {health:.0f}%")
                elif health >= 60:
                    st.warning(f"YELLOW **{v['vehicle_id']}** - {v['name']} - Health: {health:.0f}%")
                else:
                    st.error(f"RED **{v['vehicle_id']}** - {v['name']} - Health: {health:.0f}%")
        else:
            st.info("Data kendaraan tidak tersedia")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("Rekomendasi Maintenance Prioritas")
    
    if not recommendations.empty:
        for _, rec in recommendations.head(5).iterrows():
            priority = rec.get('priority', 'Normal')
            asset_id = rec.get('asset_id', 'Unknown')
            urgency = rec.get('urgency_days', 0)
            cost = rec.get('estimated_cost', 0)
            
            if priority == 'Critical':
                label = f"RED **{asset_id}** - CRITICAL ({urgency} hari) - Rp {cost:,.0f}"
            elif priority == 'High':
                label = f"ORANGE **{asset_id}** - High ({urgency} hari) - Rp {cost:,.0f}"
            else:
                label = f"YELLOW **{asset_id}** - {priority} ({urgency} hari) - Rp {cost:,.0f}"
            
            with st.expander(label):
                actions = eval(rec.get('actions', '[]')) if isinstance(rec.get('actions'), str) else rec.get('actions', [])
                for action in actions:
                    st.markdown(f"- {action}")
                
                if st.button("Selesai", key=f"done_{rec.get('id', 0)}"):
                    crud.update_recommendation_status(rec['id'], 'Completed', mode)
                    st.success("Rekomendasi ditandai selesai")
                    st.rerun()
    else:
        st.success("GREEN Tidak ada rekomendasi maintenance saat ini")
    
    st.markdown("---")
    
    # PDF Download
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Download Executive Summary PDF", use_container_width=True):
            pdf_gen = PDFGenerator(Path(__file__).parent.parent / 'static')
            pdf = pdf_gen.generate_executive_summary(summary)
            filename = f"Executive_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.markdown(pdf_gen.get_download_link(pdf, filename), unsafe_allow_html=True)
            st.success("PDF berhasil dibuat! Klik link di atas untuk download.")