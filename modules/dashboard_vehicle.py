"""
Vehicle Dashboard Module
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import database.crud_vehicles as db_vehicles
from utils.visualizations import create_cost_analysis_charts


def analyze_vehicle_health(vehicle_id, mode='real'):
    """Enhanced vehicle health analysis"""
    try:
        services = db_vehicles.get_vehicle_services(vehicle_id, mode=mode)
        vehicle = db_vehicles.get_vehicles(mode=mode)
        
        if vehicle.empty:
            return {
                "status": "Data Kendaraan Tidak Ditemukan",
                "health_score": 0,
                "next_services": [],
                "current_odometer": 0,
                "months_used": 0,
                "error": True,
                "maintenance_cost": 0,
                "cost_per_km": 0,
                "service_count": 0
            }
        
        vehicle_data = vehicle[vehicle['vehicle_id'] == vehicle_id]
        if vehicle_data.empty:
            return {
                "status": "Data Kendaraan Tidak Ditemukan",
                "health_score": 0,
                "next_services": [],
                "current_odometer": 0,
                "months_used": 0,
                "error": True,
                "maintenance_cost": 0,
                "cost_per_km": 0,
                "service_count": 0
            }
        
        vehicle_data = vehicle_data.iloc[0]
        current_odometer = vehicle_data['last_odometer']
        purchase_date = pd.to_datetime(vehicle_data['purchase_date'])
        current_date = datetime.now()
        months_used = (current_date.year - purchase_date.year) * 12 + (current_date.month - purchase_date.month)
        
        total_cost = services['cost'].sum() if not services.empty else 0
        cost_per_km = total_cost / current_odometer if current_odometer > 0 else 0
        
        components = db_vehicles.get_vehicle_components(mode=mode)
        next_services = []
        
        for _, comp in components.iterrows():
            last_service = services[services['component_name'] == comp['component_name']]
            
            if not last_service.empty:
                last_service_date = pd.to_datetime(last_service.iloc[0]['service_date'])
                last_odometer = last_service.iloc[0]['odometer']
                months_since = (current_date.year - last_service_date.year) * 12 + (current_date.month - last_service_date.month)
                km_since = current_odometer - last_odometer
            else:
                months_since = months_used
                km_since = current_odometer
            
            km_percent = 0
            month_percent = 0
            
            if comp['standard_life_km'] > 0:
                safe_life_km = comp['standard_life_km'] * 0.9
                km_percent = min(100, (km_since / safe_life_km * 100)) if safe_life_km > 0 else 0
            
            if comp['standard_life_months'] > 0:
                safe_life_months = comp['standard_life_months'] * 0.9
                month_percent = min(100, (months_since / safe_life_months * 100)) if safe_life_months > 0 else 0
            
            max_percent = max(km_percent, month_percent)
            
            if max_percent >= 95:
                status = "CRITICAL - SEGERA GANTI"
                color = "red"
            elif max_percent >= 85:
                status = "Warning - Segera Ganti"
                color = "orange"
            elif max_percent >= 70:
                status = "Perhatian - Siapkan Penggantian"
                color = "yellow"
            else:
                status = "Good"
                color = "green"
            
            km_remaining = max(0, (comp['standard_life_km'] - km_since)) if comp['standard_life_km'] > 0 else 0
            months_remaining = max(0, (comp['standard_life_months'] - months_since)) if comp['standard_life_months'] > 0 else 0
            
            next_services.append({
                'component': comp['component_name'],
                'km_used': km_since,
                'km_limit': comp['standard_life_km'],
                'months_used': months_since,
                'months_limit': comp['standard_life_months'],
                'usage_percent': max_percent,
                'status': status,
                'color': color,
                'km_remaining': km_remaining,
                'months_remaining': months_remaining
            })
        
        if len(next_services) > 0:
            health_score = max(0, 100 - sum(s['usage_percent'] for s in next_services) / len(next_services))
        else:
            health_score = 100
        
        if health_score >= 80:
            overall_status = "Sangat Baik"
        elif health_score >= 70:
            overall_status = "Baik"
        elif health_score >= 60:
            overall_status = "Cukup"
        elif health_score >= 50:
            overall_status = "Perlu Perhatian"
        elif health_score >= 40:
            overall_status = "Kritis - Segera Tindak Lanjut"
        else:
            overall_status = "SANGAT KRITIS - STOP OPERASI"
        
        if services.empty:
            overall_status = "Baru - Belum Ada Servis"
            health_score = 100
        
        return {
            "status": overall_status,
            "health_score": health_score,
            "next_services": next_services,
            "current_odometer": current_odometer,
            "months_used": months_used,
            "error": False,
            "maintenance_cost": total_cost,
            "cost_per_km": cost_per_km,
            "service_count": len(services)
        }
        
    except Exception as e:
        return {
            "status": "Error Analisis",
            "health_score": 0,
            "next_services": [],
            "current_odometer": 0,
            "months_used": 0,
            "error": True,
            "maintenance_cost": 0,
            "cost_per_km": 0,
            "service_count": 0
        }


def render_vehicle_dashboard():
    """Render Vehicle Dashboard"""
    
    st.title("Dashboard Pemeliharaan Kendaraan")
    
    vehicles = db_vehicles.get_vehicles(mode=st.session_state.db_mode)
    
    if vehicles.empty:
        st.warning("Belum ada data kendaraan.")
        return
    
    total_vehicles = len(vehicles)
    active_vehicles = len(vehicles[vehicles['status'] == 'Aktif']) if 'status' in vehicles.columns else 0
    total_odometer = vehicles['last_odometer'].sum() if 'last_odometer' in vehicles.columns else 0
    
    all_services = db_vehicles.get_vehicle_services(mode=st.session_state.db_mode)
    total_cost = all_services['cost'].sum() if not all_services.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Kendaraan", total_vehicles)
    col2.metric("Kendaraan Aktif", active_vehicles)
    col3.metric("Total Odometer", f"{total_odometer:,} km")
    col4.metric("Total Biaya Servis", f"Rp {total_cost:,.0f}")
    
    st.markdown("---")
    
    if not all_services.empty:
        fig_vehicle, _ = create_cost_analysis_charts(all_services)
        if fig_vehicle:
            st.plotly_chart(fig_vehicle, use_container_width=True)
    
    st.subheader("Status Kesehatan Kendaraan")
    
    health_data = []
    for _, v in vehicles.iterrows():
        health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
        if not health.get('error', False):
            health_data.append({
                'Kendaraan': f"{v['vehicle_id']} - {v['brand']} {v['model']}",
                'Health Score': health['health_score'],
                'Status': health['status'],
                'Odometer': health['current_odometer'],
                'Usia (bulan)': health['months_used'],
                'Jumlah Servis': health.get('service_count', 0)
            })
    
    if health_data:
        health_df = pd.DataFrame(health_data)
        st.dataframe(
            health_df,
            column_config={
                'Kendaraan': st.column_config.TextColumn('Kendaraan'),
                'Health Score': st.column_config.ProgressColumn('Health Score', format="%.0f%%", min_value=0, max_value=100),
                'Status': st.column_config.TextColumn('Status'),
                'Odometer': st.column_config.NumberColumn('Odometer', format="%d km"),
                'Usia (bulan)': st.column_config.NumberColumn('Usia', format="%d bulan"),
                'Jumlah Servis': st.column_config.NumberColumn('Servis', format="%d kali")
            },
            use_container_width=True,
            hide_index=True
        )