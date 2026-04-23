"""
Manage Vehicles Module
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import database.crud_vehicles as db_vehicles
from modules.dashboard_vehicle import analyze_vehicle_health


def render_manage_vehicles():
    """Render Manage Vehicles"""
    
    st.title("Manajemen Aset Kendaraan Kantor")
    
    if st.session_state.user_role not in ['admin', 'manager']:
        st.error("Anda tidak memiliki akses untuk mengelola data kendaraan.")
        st.stop()
    
    tab_list, tab_add, tab_edit, tab_components = st.tabs([
        "Daftar Kendaraan", "Tambah Kendaraan", "Edit Kendaraan", "Master Komponen"
    ])
    
    with tab_list:
        vehicles = db_vehicles.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Kendaraan", len(vehicles))
            col2.metric("Aktif", len(vehicles[vehicles['status'] == 'Aktif']) if 'status' in vehicles.columns else 0)
            col3.metric("Service", len(vehicles[vehicles['status'] == 'Service']) if 'status' in vehicles.columns else 0)
            col4.metric("Total Odometer", f"{vehicles['last_odometer'].sum():,} km" if 'last_odometer' in vehicles.columns else "0 km")
            
            st.markdown("---")
            
            for _, v in vehicles.iterrows():
                health = analyze_vehicle_health(v['vehicle_id'], mode=st.session_state.db_mode)
                
                if health.get('error', False):
                    status_color = "#6c757d"
                    health_score_display = "N/A"
                    status_text = health.get('status', 'Error')
                    bg_color = "#f8f9fa"
                else:
                    health_score = health.get('health_score', 0)
                    if health_score >= 80:
                        status_color = "#28a745"
                        bg_color = "#f0fff4"
                    elif health_score >= 60:
                        status_color = "#ffc107"
                        bg_color = "#fffbf0"
                    else:
                        status_color = "#dc3545"
                        bg_color = "#fff5f5"
                    
                    health_score_display = f"{health_score:.0f}%"
                    status_text = health.get('status', 'Unknown')
                
                status_badge_class = {
                    'Aktif': 'status-good',
                    'Service': 'status-warning',
                    'Nonaktif': 'status-critical'
                }.get(v['status'], 'status-info')
                
                st.markdown(f"""
                <div class="vehicle-card" style="background:{bg_color};">
                    <table style="width:100%;">
                        <tr>
                            <td style="width:50%;">
                                <b style="font-size:1.3em;">{v['vehicle_id']}</b><br>
                                <span style="font-size:1.1em;">{v['brand']} {v['model']} ({v['year']})</span><br>
                                <span style="color:#666;">Plat: {v['plate_number']} | {v['color']} | {v['fuel_type']}</span>
                            </td>
                            <td style="width:25%; text-align:center;">
                                <span style="font-size:0.9em; color:#666;">Odometer</span><br>
                                <b style="font-size:1.2em;">{v['last_odometer']:,} km</b><br>
                                <span class="status-badge {status_badge_class}">{v['status']}</span>
                            </td>
                            <td style="width:25%; text-align:center;">
                                <div style="background:rgba(0,0,0,0.05); border-radius:10px; padding:10px;">
                                    <span style="font-size:0.9em; color:#666;">Health Score</span><br>
                                    <span style="font-size:1.8em; color:{status_color}; font-weight:bold;">{health_score_display}</span><br>
                                    <small style="color:#666;">{status_text}</small>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Belum ada data kendaraan.")
    
    with tab_add:
        with st.form("add_vehicle_form"):
            st.markdown("### Informasi Kendaraan")
            
            col1, col2 = st.columns(2)
            vid = col1.text_input("ID Kendaraan*", placeholder="Contoh: VH-006")
            brand = col1.text_input("Merek*", placeholder="Toyota, Honda")
            model = col2.text_input("Model*", placeholder="Innova, CRV")
            year = col2.number_input("Tahun*", min_value=2000, max_value=datetime.now().year + 1, step=1, value=datetime.now().year)
            
            col3, col4 = st.columns(2)
            plate = col3.text_input("Plat Nomor*", placeholder="B 1234 ABC")
            color = col4.text_input("Warna", placeholder="Hitam, Putih")
            
            col5, col6 = st.columns(2)
            fuel = col5.selectbox("Jenis BBM*", ["Bensin", "Solar", "Listrik", "Hybrid"])
            status = col6.selectbox("Status*", ["Aktif", "Nonaktif", "Service"])
            
            col7, col8 = st.columns(2)
            purchase_date = col7.date_input("Tanggal Beli*", datetime.now())
            last_odometer = col8.number_input("Odometer Awal (km)*", min_value=0, step=1000, value=0)
            
            notes = st.text_area("Catatan")
            
            if st.form_submit_button("SIMPAN KENDARAAN"):
                if all([vid, brand, model, plate, fuel, status]):
                    try:
                        db_vehicles.add_vehicle((
                            vid, brand, model, year, plate, color,
                            fuel, status, str(purchase_date), last_odometer, notes
                        ), mode=st.session_state.db_mode)
                        st.success(f"Kendaraan {vid} berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah kendaraan: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")
    
    with tab_edit:
        vehicles = db_vehicles.get_vehicles(mode=st.session_state.db_mode)
        if not vehicles.empty:
            sel_vehicle = st.selectbox("Pilih Kendaraan", vehicles['vehicle_id'].tolist())
            v_data = vehicles[vehicles['vehicle_id'] == sel_vehicle].iloc[0]
            
            with st.form("edit_vehicle_form"):
                col1, col2 = st.columns(2)
                e_brand = col1.text_input("Merek*", value=v_data['brand'])
                e_model = col1.text_input("Model*", value=v_data['model'])
                e_year = col2.number_input("Tahun*", value=int(v_data['year']), min_value=2000)
                e_plate = col2.text_input("Plat Nomor*", value=v_data['plate_number'])
                
                col3, col4 = st.columns(2)
                e_color = col3.text_input("Warna", value=v_data['color'] if v_data['color'] else "")
                
                fuel_options = ["Bensin", "Solar", "Listrik", "Hybrid"]
                e_fuel = col3.selectbox("Jenis BBM*", fuel_options,
                                       index=fuel_options.index(v_data['fuel_type']) if v_data['fuel_type'] in fuel_options else 0)
                
                status_options = ["Aktif", "Nonaktif", "Service"]
                e_status = col4.selectbox("Status*", status_options,
                                         index=status_options.index(v_data['status']) if v_data['status'] in status_options else 0)
                
                col5, col6 = st.columns(2)
                e_purchase = col5.date_input("Tanggal Beli*", pd.to_datetime(v_data['purchase_date']))
                e_odometer = col6.number_input("Odometer (km)*", value=int(v_data['last_odometer']), min_value=0)
                
                e_notes = st.text_area("Catatan", value=v_data['notes'] if v_data['notes'] else "")
                
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.form_submit_button("UPDATE"):
                    try:
                        db_vehicles.update_vehicle(sel_vehicle, (
                            e_brand, e_model, e_year, e_plate, e_color,
                            e_fuel, e_status, str(e_purchase), e_odometer, e_notes
                        ), mode=st.session_state.db_mode)
                        st.success("Data kendaraan berhasil diupdate!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal update: {e}")
                
                if col_btn2.form_submit_button("HAPUS", type="secondary"):
                    if st.session_state.db_mode == 'real':
                        confirm = st.text_input("Ketik 'HAPUS'")
                        if confirm == "HAPUS":
                            db_vehicles.delete_vehicle(sel_vehicle, mode=st.session_state.db_mode)
                            st.success("Kendaraan dihapus!")
                            st.rerun()
                    else:
                        db_vehicles.delete_vehicle(sel_vehicle, mode=st.session_state.db_mode)
                        st.success("Kendaraan dihapus!")
                        st.rerun()
    
    with tab_components:
        st.subheader("Master Komponen Kendaraan")
        
        components = db_vehicles.get_vehicle_components(mode=st.session_state.db_mode)
        
        if not components.empty:
            st.dataframe(
                components[['component_name', 'standard_life_km', 'standard_life_months', 'is_active']],
                use_container_width=True,
                hide_index=True
            )
        
        with st.form("component_form"):
            comp_name = st.text_input("Nama Komponen*")
            col1, col2 = st.columns(2)
            life_km = col1.number_input("Standard Life (km)", min_value=0, step=1000, value=0)
            life_months = col2.number_input("Standard Life (bulan)", min_value=0, step=1, value=0)
            is_active = st.checkbox("Aktif", value=True)
            
            if st.form_submit_button("SIMPAN KOMPONEN"):
                if comp_name:
                    try:
                        db_vehicles.add_vehicle_component(
                            (comp_name, life_km, life_months, 1 if is_active else 0),
                            mode=st.session_state.db_mode
                        )
                        st.success(f"Komponen {comp_name} berhasil disimpan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan: {e}")