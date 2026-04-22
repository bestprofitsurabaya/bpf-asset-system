"""
AC Layout Interactive Page
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.crud import CRUDOperations
from src.database.engine import DatabaseEngine
from src.visualization.layout_renderer import ACLayoutRenderer


def show_ac_layout():
    """Display AC Layout Interactive page"""
    
    st.title("Layout Tata Letak AC Interaktif")
    st.markdown("### Graha Bukopin - Lantai 11")
    
    # Initialize
    db_engine = DatabaseEngine()
    crud = CRUDOperations(db_engine)
    mode = st.session_state.get('db_mode', 'real')
    
    static_dir = Path(__file__).parent.parent / 'static'
    config_dir = Path(__file__).parent.parent / 'config'
    
    renderer = ACLayoutRenderer(static_dir, config_dir)
    
    logs = crud.get_all_logs(mode)
    assets = crud.get_assets(mode)
    
    # Tabs
    tab_indoor, tab_outdoor, tab_legend, tab_config = st.tabs([
        "Layout Indoor",
        "Layout Outdoor",
        "Legenda & Status",
        "Konfigurasi"
    ])
    
    with tab_indoor:
        st.markdown("#### Denah Indoor dengan Status AC")
        st.info("Klik dan hover pada marker untuk melihat detail AC")
        
        fig = renderer.render_indoor_layout(logs, assets)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            config = renderer.load_config()
            indoor_config = config.get('indoor', {})
            bg_path = static_dir.parent / indoor_config.get('background', '')
            
            if not bg_path.exists():
                st.warning(f"Gambar layout indoor tidak ditemukan. Silakan upload di tab Konfigurasi.")
            else:
                st.warning("Konfigurasi layout indoor belum lengkap.")
    
    with tab_outdoor:
        st.markdown("#### Layout Unit Outdoor")
        renderer.render_outdoor_grid(logs, assets)
        
        st.markdown("---")
        st.markdown("### Keterangan Kapasitas")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="background:#437c4d; padding:15px; border-radius:8px; color:white; text-align:center;">
                <b>60.000 Btu/h</b>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background:#f1e05a; padding:15px; border-radius:8px; color:black; text-align:center;">
                <b>100.000 Btu/h</b>
            </div>
            """, unsafe_allow_html=True)
    
    with tab_legend:
        renderer.render_legend()
        
        st.markdown("---")
        st.markdown("### Ringkasan Status Semua Unit AC")
        
        status_df = renderer.render_status_table(logs, assets)
        if not status_df.empty:
            st.dataframe(
                status_df,
                column_config={
                    'Status': 'Status',
                    'Asset ID': 'Asset ID',
                    'Label': 'Label',
                    'Ruangan': 'Ruangan',
                    'Health': 'Health Score',
                    'Kondisi': 'Kondisi'
                },
                use_container_width=True,
                hide_index=True
            )
    
    with tab_config:
        st.markdown("### Konfigurasi Layout AC")
        
        st.markdown("""
        **Panduan Setup Layout:**
        
        1. Upload gambar layout indoor (JPG/PNG)
        2. Edit konfigurasi posisi AC di file JSON
        3. Refresh halaman untuk melihat perubahan
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_indoor = st.file_uploader(
                "Upload Layout Indoor",
                type=['jpg', 'jpeg', 'png'],
                key="indoor_upload"
            )
            
            if uploaded_indoor:
                save_path = static_dir / 'layout_indoor.jpg'
                with open(save_path, 'wb') as f:
                    f.write(uploaded_indoor.getbuffer())
                st.success("Layout indoor tersimpan!")
                st.image(uploaded_indoor, caption="Preview Indoor", use_column_width=True)
        
        with col2:
            uploaded_logo = st.file_uploader(
                "Upload Logo Aplikasi (PNG)",
                type=['png'],
                key="logo_upload"
            )
            
            if uploaded_logo:
                save_path = static_dir / 'logo.png'
                with open(save_path, 'wb') as f:
                    f.write(uploaded_logo.getbuffer())
                st.success("Logo tersimpan!")
                st.image(uploaded_logo, caption="Preview Logo", width=180)
        
        st.markdown("---")
        st.markdown("### Edit Konfigurasi")
        
        config = renderer.load_config()
        
        # Display and edit config
        config_str = json.dumps(config, indent=2, ensure_ascii=False)
        edited_config = st.text_area(
            "Konfigurasi (JSON format)",
            value=config_str,
            height=400,
            key="config_editor"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Simpan Konfigurasi", use_container_width=True):
                try:
                    new_config = json.loads(edited_config)
                    if renderer.save_config(new_config):
                        st.success("Konfigurasi berhasil disimpan!")
                        st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"Format JSON tidak valid: {e}")
        
        with col2:
            if st.button("Reset ke Default", use_container_width=True):
                default_config = {
                    "indoor": {
                        "background": "static/layout_indoor.jpg",
                        "width": 1000,
                        "height": 700,
                        "ac_units": []
                    },
                    "outdoor": {
                        "ac_units": []
                    }
                }
                if renderer.save_config(default_config):
                    st.success("Konfigurasi direset ke default!")
                    st.rerun()