"""
Edit/Delete Data Module (Admin Only)
"""

import streamlit as st
import pandas as pd

import database.crud_ac as db_ac
import database.crud_vehicles as db_vehicles
from database.engine import backup_database


def render_edit_data():
    """Render Edit/Delete Data"""
    
    st.title("Koreksi Data")
    
    if st.session_state.user_role not in ['admin']:
        st.error("Hanya admin yang dapat mengedit/menghapus data.")
        st.stop()
    
    tab_ac, tab_vehicle, tab_bulk = st.tabs(["Hapus Log AC", "Hapus Servis Kendaraan", "Bulk Operations"])
    
    with tab_ac:
        logs = db_ac.get_all_logs(mode=st.session_state.db_mode)
        if not logs.empty:
            st.warning("Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
            
            asset_filter = st.selectbox("Filter by Asset", ["All"] + logs['asset_id'].unique().tolist(), key="ac_filter")
            
            filtered_logs = logs if asset_filter == "All" else logs[logs['asset_id'] == asset_filter]
            
            if not filtered_logs.empty:
                sel = st.selectbox(
                    "Pilih Log AC",
                    filtered_logs.apply(lambda x: f"ID: {x['id']} - {x['asset_id']} - {x['tanggal']} - Teknisi: {x['teknisi']}", axis=1)
                )
                l_id = int(sel.split(" - ")[0].replace("ID: ", ""))
                
                log_detail = filtered_logs[filtered_logs['id'] == l_id].iloc[0]
                st.json(log_detail.to_dict())
                
                if st.button("HAPUS LOG AC PERMANEN", type="primary"):
                    if st.session_state.db_mode == 'real':
                        confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi", key="ac_confirm")
                        if confirm == "HAPUS":
                            db_ac.delete_log(l_id, mode=st.session_state.db_mode)
                            st.success("Log Terhapus!")
                            st.rerun()
                    else:
                        db_ac.delete_log(l_id, mode=st.session_state.db_mode)
                        st.success("Log Terhapus!")
                        st.rerun()
        else:
            st.info("Tidak ada log AC")
    
    with tab_vehicle:
        services = db_vehicles.get_vehicle_services(mode=st.session_state.db_mode)
        if not services.empty:
            st.warning("Hati-hati! Data yang dihapus tidak dapat dikembalikan.")
            
            vehicle_filter = st.selectbox("Filter by Vehicle", ["All"] + services['vehicle_id'].unique().tolist(), key="vh_filter")
            
            filtered_services = services if vehicle_filter == "All" else services[services['vehicle_id'] == vehicle_filter]
            
            if not filtered_services.empty:
                sel = st.selectbox(
                    "Pilih Servis Kendaraan",
                    filtered_services.apply(lambda x: f"ID: {x['id']} - {x['vehicle_id']} - {x['component_name']} - {x['service_date']} - Rp {x['cost']:,.0f}", axis=1)
                )
                s_id = int(sel.split(" - ")[0].replace("ID: ", ""))
                
                service_detail = filtered_services[filtered_services['id'] == s_id].iloc[0]
                st.json(service_detail.to_dict())
                
                if st.button("HAPUS SERVIS KENDARAAN", type="primary"):
                    if st.session_state.db_mode == 'real':
                        confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi", key="vh_confirm")
                        if confirm == "HAPUS":
                            db_vehicles.delete_vehicle_service(s_id, mode=st.session_state.db_mode)
                            st.success("Servis kendaraan terhapus!")
                            st.rerun()
                    else:
                        db_vehicles.delete_vehicle_service(s_id, mode=st.session_state.db_mode)
                        st.success("Servis kendaraan terhapus!")
                        st.rerun()
        else:
            st.info("Tidak ada data servis kendaraan")
    
    with tab_bulk:
        st.subheader("Bulk Operations")
        st.warning("Operasi bulk akan mempengaruhi banyak data sekaligus. Gunakan dengan hati-hati!")
        
        if st.button("Backup Database"):
            backup_path = backup_database(st.session_state.db_mode)
            if backup_path:
                st.success(f"Database dibackup ke: {backup_path}")
            else:
                st.error("Backup gagal")
        
        st.markdown("---")
        st.markdown("### Hapus Log Lama")
        
        days_to_keep = st.number_input("Hapus log lebih lama dari (hari)", min_value=30, value=365)
        
        if st.button("Hapus Log Lama"):
            if st.session_state.db_mode == 'real':
                confirm = st.text_input("Ketik 'HAPUS SEMUA LOG LAMA' untuk konfirmasi", key="bulk_confirm")
                if confirm == "HAPUS SEMUA LOG LAMA":
                    deleted = db_ac.delete_old_logs(days_to_keep, mode=st.session_state.db_mode)
                    st.success(f"{deleted} log berhasil dihapus!")
            else:
                deleted = db_ac.delete_old_logs(days_to_keep, mode=st.session_state.db_mode)
                st.success(f"{deleted} log berhasil dihapus!")