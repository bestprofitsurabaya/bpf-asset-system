"""
Input AC Maintenance Log Module
"""

import streamlit as st
from datetime import datetime

import database.crud_ac as db_ac
from utils.anomaly import detect_anomalies_realtime


def render_input_ac():
    """Render Input AC Log Form"""
    
    st.title("Form Servis Berkala AC (SOW BPF)")
    
    if st.session_state.user_role not in ['admin', 'teknisi']:
        st.error("Anda tidak memiliki akses untuk input data maintenance.")
        st.stop()
    
    assets = db_ac.get_assets(mode=st.session_state.db_mode)
    
    if assets.empty:
        st.warning("Belum ada data aset AC. Silakan tambahkan terlebih dahulu.")
        return
    
    with st.form("input_log_form", clear_on_submit=True):
        st.markdown("### Informasi Dasar")
        col1, col2 = st.columns(2)
        a_id = col1.selectbox("ID Aset AC*", assets['asset_id'].tolist())
        tek = col1.text_input("Nama Teknisi*", value=st.session_state.username)
        tgl = col2.date_input("Tanggal Pelaksanaan*", datetime.now())
        
        asset_info = assets[assets['asset_id'] == a_id].iloc[0]
        st.info(f"Lokasi: {asset_info['lokasi']} | Kapasitas: {asset_info['kapasitas']}")
        
        st.markdown("---")
        st.markdown("### Parameter Pengukuran")
        
        col3, col4, col5, col6 = st.columns(4)
        v_supply = col3.number_input("Voltase (V)", value=380.0, min_value=0.0, step=1.0)
        amp = col4.number_input("Arus Listrik (A)", min_value=0.0, step=0.1, value=15.0)
        low_p = col5.number_input("Pressure Low (Psi)", value=140.0, min_value=0.0, step=1.0)
        high_p = col6.number_input("Pressure High (Psi)", value=350.0, min_value=0.0, step=1.0)
        
        col7, col8, col9 = st.columns(3)
        t_ret = col7.number_input("Suhu Return (C)*", min_value=0.0, max_value=50.0, step=0.1, value=24.0)
        t_sup = col8.number_input("Suhu Supply (C)*", min_value=0.0, max_value=50.0, step=0.1, value=14.0)
        t_out = col9.number_input("Suhu Outdoor (C)", min_value=0.0, max_value=50.0, step=0.1, value=32.0)
        
        col10, col11 = st.columns(2)
        drain = col10.selectbox("Drainase*", ["Lancar", "Tersumbat", "Perlu Pembersihan"])
        test = col11.selectbox("Status Run*", ["Normal", "Abnormal"])
        
        st.markdown("---")
        st.markdown("### Catatan & Biaya")
        
        col12, col13 = st.columns(2)
        sparepart_cost = col12.number_input("Biaya Sparepart (Rp)", min_value=0, step=50000, value=0)
        catatan = col13.text_area("Catatan LHO / Tindakan yang dilakukan", height=100)
        
        delta_t = t_ret - t_sup if t_ret > t_sup else 0
        
        health_score = 100
        
        if delta_t >= 12:
            health_score -= 0
        elif delta_t >= 10:
            health_score -= 10
        elif delta_t >= 8:
            health_score -= 20
        elif delta_t >= 6:
            health_score -= 35
        else:
            health_score -= 50
        
        if amp > 25:
            health_score -= 20
        elif amp > 20:
            health_score -= 10
        elif amp > 15:
            health_score -= 5
        
        if drain != "Lancar":
            health_score -= 15
        
        if low_p < 130 or low_p > 150:
            health_score -= 10
        
        health_score = max(0, min(100, health_score))
        
        # Real-time anomaly detection
        readings = {'amp_kompresor': amp, 'delta_t': delta_t, 'low_p': low_p}
        anomalies, severity = detect_anomalies_realtime(readings, a_id, st.session_state.db_mode)
        
        st.markdown("---")
        st.markdown("### Preview Health Score & Anomaly Detection")
        
        col_preview1, col_preview2, col_preview3 = st.columns(3)
        col_preview1.metric("Delta T", f"{delta_t:.1f}C")
        col_preview2.metric("Health Score", f"{health_score}/100")
        
        if severity == 'Critical':
            col_preview3.error(f"Anomali: {severity}")
        elif severity == 'High':
            col_preview3.warning(f"Anomali: {severity}")
        else:
            col_preview3.success(f"Status: {severity}")
        
        if anomalies:
            st.markdown("#### Detail Anomali:")
            for a in anomalies:
                st.markdown(f"- **{a['parameter']}**: {a['message']}")
        
        st.markdown("---")
        
        if st.form_submit_button("SIMPAN DATA MAINTENANCE", use_container_width=True):
            if all([a_id, tek, t_ret, t_sup]):
                try:
                    db_ac.add_log((
                        a_id, str(tgl), tek, v_supply, amp, low_p,
                        t_ret, t_sup, delta_t, drain, test, health_score,
                        sparepart_cost, catatan
                    ), mode=st.session_state.db_mode)
                    st.success("Laporan Maintenance Berhasil Disimpan!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan data: {e}")
            else:
                st.error("Mohon isi semua field yang bertanda *")