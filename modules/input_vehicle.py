"""
Input Vehicle Service Module
"""

import streamlit as st
from datetime import datetime

import database.crud_vehicles as db_vehicles


def render_input_vehicle():
    """Render Input Vehicle Service Form"""
    
    st.title("Input Servis / Penggantian Komponen Kendaraan")
    
    if st.session_state.user_role not in ['admin', 'teknisi']:
        st.error("Anda tidak memiliki akses.")
        st.stop()
    
    vehicles = db_vehicles.get_vehicles(mode=st.session_state.db_mode)
    
    if vehicles.empty:
        st.warning("Belum ada data kendaraan.")
        return
    
    active_vehicles = vehicles[vehicles['status'] == 'Aktif'] if 'status' in vehicles.columns else pd.DataFrame()
    vehicle_id = st.selectbox(
        "Pilih Kendaraan",
        active_vehicles['vehicle_id'].tolist() if not active_vehicles.empty else vehicles['vehicle_id'].tolist()
    )
    
    vehicle_data = vehicles[vehicles['vehicle_id'] == vehicle_id].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Odometer", f"{vehicle_data['last_odometer']:,} km")
    col2.metric("Merek/Model", f"{vehicle_data['brand']} {vehicle_data['model']}")
    col3.metric("Plat Nomor", vehicle_data['plate_number'])
    
    st.markdown("---")
    
    with st.form("service_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        service_date = col1.date_input("Tanggal Servis*", datetime.now())
        odometer = col2.number_input("Odometer (km)*", min_value=0, step=1000, value=int(vehicle_data['last_odometer']))
        
        components = db_vehicles.get_vehicle_components(mode=st.session_state.db_mode)
        component_list = components['component_name'].tolist() if not components.empty else []
        component_name = st.selectbox("Komponen*", component_list + ["Lainnya"])
        
        col3, col4 = st.columns(2)
        service_type = col3.selectbox("Jenis Servis*", ["Servis Rutin", "Perbaikan", "Penggantian Komponen", "Lainnya"])
        mechanic = col4.text_input("Montir/Bengkel*", value="Bengkel Resmi")
        
        col5, col6 = st.columns(2)
        cost = col5.number_input("Biaya (Rp)*", min_value=0, step=50000, value=0)
        
        notes = st.text_area("Catatan", height=100)
        
        if st.form_submit_button("SIMPAN SERVIS"):
            if all([vehicle_id, component_name, service_type, mechanic]):
                try:
                    db_vehicles.add_vehicle_service((
                        vehicle_id, str(service_date), odometer, service_type, component_name,
                        0, 0, 0, 0, 0, 0, cost, mechanic, notes
                    ), mode=st.session_state.db_mode)
                    
                    if odometer > vehicle_data['last_odometer']:
                        db_vehicles.update_vehicle_odometer(vehicle_id, odometer, mode=st.session_state.db_mode)
                    
                    st.success("Data servis berhasil disimpan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan: {e}")
            else:
                st.error("Mohon isi field bertanda *")