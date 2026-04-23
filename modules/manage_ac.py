"""
Manage AC Assets Module
"""

import streamlit as st
import pandas as pd

import database.crud_ac as db_ac


def render_manage_ac():
    """Render Manage AC Assets"""
    
    st.title("Manajemen Spesifikasi Aset AC")
    
    if st.session_state.user_role not in ['admin', 'manager']:
        st.error("Anda tidak memiliki akses untuk mengelola data master.")
        st.stop()
    
    tab_view, tab_add, tab_edit = st.tabs(["View Assets", "Add New Asset", "Edit/Delete Asset"])
    
    with tab_view:
        as_df = db_ac.get_assets(mode=st.session_state.db_mode)
        if not as_df.empty:
            st.dataframe(
                as_df,
                column_config={
                    "asset_id": "Asset ID",
                    "merk": "Merk",
                    "tipe": "Tipe",
                    "kapasitas": "Kapasitas",
                    "lokasi": "Lokasi",
                    "refrigerant": "Refrigerant",
                    "status": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Belum ada data aset AC")
    
    with tab_add:
        with st.form("add_asset_form"):
            st.markdown("### Tambah Aset AC Baru")
            
            col1, col2 = st.columns(2)
            new_id = col1.text_input("Asset ID*", placeholder="Contoh: AC-16-NEW")
            new_merk = col1.text_input("Merk*", value="Daikin")
            new_tipe = col2.text_input("Tipe*", placeholder="Split Duct / Split Wall")
            new_kap = col2.text_input("Kapasitas*", placeholder="Contoh: 60.000 Btu/h")
            
            col3, col4 = st.columns(2)
            new_lok = col3.text_input("Lokasi*", placeholder="Detail ruangan")
            new_ref = col4.text_input("Refrigerant*", value="R32")
            
            if st.form_submit_button("TAMBAH ASET"):
                if all([new_id, new_merk, new_tipe, new_kap, new_lok, new_ref]):
                    try:
                        db_ac.add_asset(
                            (new_id, new_merk, new_tipe, new_kap, new_lok, new_ref),
                            mode=st.session_state.db_mode
                        )
                        st.success(f"Aset {new_id} berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menambah aset: {e}")
                else:
                    st.error("Mohon isi semua field yang bertanda *")
    
    with tab_edit:
        as_df = db_ac.get_assets(mode=st.session_state.db_mode)
        if not as_df.empty:
            sel_as = st.selectbox("Pilih Aset AC untuk Edit", as_df['asset_id'].tolist())
            curr = as_df[as_df['asset_id'] == sel_as].iloc[0]
            
            with st.form("edit_as_form"):
                col1, col2 = st.columns(2)
                m_merk = col1.text_input("Merk", value=curr['merk'])
                m_tipe = col1.text_input("Tipe", value=curr['tipe'])
                m_kap = col2.text_input("Kapasitas", value=curr['kapasitas'])
                m_lok = col2.text_input("Detail Lokasi", value=curr['lokasi'])
                m_ref = st.text_input("Refrigerant", value=curr['refrigerant'])
                
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.form_submit_button("UPDATE SPESIFIKASI"):
                    db_ac.update_asset(
                        sel_as, (m_merk, m_tipe, m_kap, m_lok, m_ref),
                        mode=st.session_state.db_mode
                    )
                    st.success("Spesifikasi Berhasil Diperbarui!")
                    st.rerun()
                
                if col_btn2.form_submit_button("HAPUS ASET", type="secondary"):
                    if st.session_state.db_mode == 'real':
                        confirm = st.text_input("Ketik 'HAPUS' untuk konfirmasi")
                        if confirm == "HAPUS":
                            db_ac.delete_asset(sel_as, mode=st.session_state.db_mode)
                            st.success("Aset berhasil dihapus!")
                            st.rerun()
                    else:
                        db_ac.delete_asset(sel_as, mode=st.session_state.db_mode)
                        st.success("Aset berhasil dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada data aset AC")