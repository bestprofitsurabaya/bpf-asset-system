"""
AC Layout Interactive Module
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from PIL import Image
import plotly.graph_objects as go

import database.crud_ac as db_ac
from config.settings import STATIC_DIR, CONFIG_DIR
from utils.helpers import load_ac_layout_config


def get_ac_health_status(asset_id, logs):
    """Get health status color and info for AC unit"""
    if logs.empty:
        return '#6c757d', 'No Data', 0, 'Unknown'
    
    asset_logs = logs[logs['asset_id'] == asset_id]
    if asset_logs.empty:
        return '#6c757d', 'No Data', 0, 'Unknown'
    
    latest = asset_logs.iloc[-1]
    health_score = latest['health_score'] if 'health_score' in latest else 0
    delta_t = latest['delta_t'] if 'delta_t' in latest else 0
    amp = latest['amp_kompresor'] if 'amp_kompresor' in latest else 0
    last_date = latest['tanggal'] if 'tanggal' in latest else 'Unknown'
    
    if health_score >= 80:
        return '#28a745', 'Good', health_score, f'Delta T: {delta_t:.1f}C | Amp: {amp:.1f}A | Last: {last_date}'
    elif health_score >= 60:
        return '#ffc107', 'Warning', health_score, f'Delta T: {delta_t:.1f}C | Amp: {amp:.1f}A | Last: {last_date}'
    elif health_score >= 40:
        return '#fd7e14', 'Critical', health_score, f'Delta T: {delta_t:.1f}C | Amp: {amp:.1f}A | Last: {last_date}'
    else:
        return '#dc3545', 'Severe', health_score, f'Delta T: {delta_t:.1f}C | Amp: {amp:.1f}A | Last: {last_date}'


def render_layout_ac():
    """Render AC Layout Interactive"""
    
    st.title("Layout Tata Letak AC Interaktif")
    st.markdown("### Graha Bukopin - Lantai 11")
    
    layout_config = load_ac_layout_config()
    logs = db_ac.get_all_logs(mode=st.session_state.db_mode)
    assets = db_ac.get_assets(mode=st.session_state.db_mode)
    
    tab_indoor, tab_outdoor, tab_legend, tab_config = st.tabs([
        "Layout Indoor",
        "Layout Outdoor",
        "Legenda & Status",
        "Konfigurasi"
    ])
    
    with tab_indoor:
        if layout_config and 'indoor' in layout_config:
            indoor_config = layout_config['indoor']
            bg_path = STATIC_DIR / 'layout_indoor.jpg'
            use_image_background = bg_path.exists()
            
            if use_image_background:
                st.markdown("#### Denah Indoor dengan Status AC")
                st.info("Klik dan hover pada marker untuk melihat detail AC")
                
                fig = go.Figure()
                
                try:
                    img = Image.open(bg_path)
                    fig.add_layout_image(
                        dict(
                            source=img,
                            xref="x",
                            yref="y",
                            x=0,
                            y=indoor_config['height'],
                            sizex=indoor_config['width'],
                            sizey=indoor_config['height'],
                            sizing="stretch",
                            layer="below"
                        )
                    )
                except Exception as e:
                    st.warning(f"Gagal memuat gambar background: {e}")
                
                for ac in indoor_config['ac_units']:
                    asset_id = ac['asset_id']
                    color, status, health, tooltip_info = get_ac_health_status(asset_id, logs)
                    
                    asset_info = assets[assets['asset_id'] == asset_id]
                    location = asset_info['lokasi'].iloc[0] if not asset_info.empty else ac.get('room', asset_id)
                    room = ac.get('room', location)
                    
                    if status == 'Good':
                        symbol = 'circle'
                        size = 18
                    elif status == 'Warning':
                        symbol = 'triangle-up'
                        size = 20
                    elif status == 'Critical':
                        symbol = 'diamond'
                        size = 22
                    else:
                        symbol = 'x'
                        size = 18
                    
                    fig.add_trace(go.Scatter(
                        x=[ac['x']],
                        y=[indoor_config['height'] - ac['y']],
                        mode='markers+text',
                        marker=dict(
                            size=size,
                            color=color,
                            symbol=symbol,
                            line=dict(width=2, color='white')
                        ),
                        text=[ac.get('label', asset_id[-2:])],
                        textposition="top center",
                        textfont=dict(size=10, color='black', family='Arial Black'),
                        name=asset_id,
                        hovertemplate=f"<b>{asset_id}</b><br>Ruangan: {room}<br>Status: {status}<br>Health: {health:.0f}%<br>{tooltip_info}<extra></extra>"
                    ))
                
                fig.update_layout(
                    width=indoor_config['width'],
                    height=indoor_config['height'],
                    xaxis=dict(range=[0, indoor_config['width']], showgrid=False, zeroline=False, visible=False),
                    yaxis=dict(range=[0, indoor_config['height']], showgrid=False, zeroline=False, visible=False),
                    showlegend=False,
                    margin=dict(l=0, r=0, t=30, b=0),
                    title="Layout Indoor - Status AC",
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Gambar layout indoor tidak ditemukan di: {bg_path}")
                st.markdown("Silakan upload gambar di tab **Konfigurasi**")
        else:
            st.warning("Konfigurasi layout indoor belum tersedia.")
    
    with tab_outdoor:
        st.markdown("#### Layout Unit Outdoor")
        
        if layout_config and 'outdoor' in layout_config:
            outdoor_config = layout_config['outdoor']
            
            st.markdown('<div class="outdoor-grid-container">', unsafe_allow_html=True)
            
            grid_items = {}
            for ac in outdoor_config['ac_units']:
                key = f"{ac['grid_row']}_{ac['grid_col']}"
                grid_items[key] = ac
            
            for row in range(1, 3):
                for col in range(1, 6):
                    key = f"{row}_{col}"
                    ac = grid_items.get(key)
                    
                    if ac:
                        asset_id = ac['asset_id']
                        color, status, health, tooltip_info = get_ac_health_status(asset_id, logs)
                        
                        asset_info = assets[assets['asset_id'] == asset_id]
                        location = asset_info['lokasi'].iloc[0] if not asset_info.empty else '-'
                        
                        capacity_class = "btu-100" if ac.get('capacity') == "100.000 Btu/h" else "btu-60"
                        
                        status_badge = ""
                        if status == 'Critical' or status == 'Severe':
                            status_badge = "RED"
                        elif status == 'Warning':
                            status_badge = "YELLOW"
                        elif status == 'Good':
                            status_badge = "GREEN"
                        
                        st.markdown(f"""
                        <div class="outdoor-unit {capacity_class}" title="{asset_id} - {location} - Health: {health:.0f}%">
                            <div class="unit-number">{ac['label']} {status_badge}</div>
                            <div class="unit-status">{status}</div>
                            <small>{health:.0f}%</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="outdoor-unit" style="background:#ccc; color:#666;">
                            <div class="unit-number">-</div>
                            <div class="unit-status">Kosong</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### Keterangan Kapasitas")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div style="background:#437c4d; padding:10px; border-radius:5px; color:white;">60.000 Btu/h</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div style="background:#f1e05a; padding:10px; border-radius:5px; color:black;">100.000 Btu/h</div>', unsafe_allow_html=True)
        else:
            st.warning("Konfigurasi layout outdoor belum tersedia.")
    
    with tab_legend:
        st.markdown("### Legenda Status AC")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#f0fff4; border-radius:10px;">
                <h3 style="color:#28a745;">GOOD</h3>
                <p>Health > 80%</p>
                <p>Aman, operasi normal</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#fffbf0; border-radius:10px;">
                <h3 style="color:#ffc107;">WARNING</h3>
                <p>Health 60-80%</p>
                <p>Perlu perhatian</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#fff5f0; border-radius:10px;">
                <h3 style="color:#fd7e14;">CRITICAL</h3>
                <p>Health 40-60%</p>
                <p>Segera tindak lanjut</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#fff5f5; border-radius:10px;">
                <h3 style="color:#dc3545;">SEVERE</h3>
                <p>Health < 40%</p>
                <p>STOP OPERASI!</p>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#f8f9fa; border-radius:10px;">
                <h3 style="color:#6c757d;">NO DATA</h3>
                <p>Belum ada log</p>
                <p>Perlu input data</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### Ringkasan Status Semua Unit AC")
        
        status_data = []
        if layout_config and 'indoor' in layout_config:
            for ac in layout_config['indoor']['ac_units']:
                asset_id = ac['asset_id']
                color, status, health, tooltip_info = get_ac_health_status(asset_id, logs)
                asset_info = assets[assets['asset_id'] == asset_id]
                location = asset_info['lokasi'].iloc[0] if not asset_info.empty else ac.get('room', '-')
                
                if status == 'Good':
                    status_emoji = "GREEN"
                elif status == 'Warning':
                    status_emoji = "YELLOW"
                elif status == 'Critical':
                    status_emoji = "ORANGE"
                elif status == 'Severe':
                    status_emoji = "RED"
                else:
                    status_emoji = "GRAY"
                
                status_data.append({
                    'Status': status_emoji,
                    'Asset ID': asset_id,
                    'Label': ac.get('label', '-'),
                    'Ruangan': ac.get('room', location),
                    'Health': f"{health:.0f}%" if health > 0 else "N/A",
                    'Kondisi': status
                })
        
        if status_data:
            status_df = pd.DataFrame(status_data)
            st.dataframe(status_df, use_container_width=True, hide_index=True)
    
    with tab_config:
        st.markdown("### Konfigurasi Layout AC")
        
        st.markdown("""
        **Panduan Setup Layout:**
        
        1. Upload gambar layout (JPG/PNG) untuk indoor
        2. Edit file `config/ac_layout_config.json` untuk mengatur posisi AC
        3. Refresh halaman untuk melihat perubahan
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            uploaded_indoor = st.file_uploader("Upload Layout Indoor", type=['jpg', 'jpeg', 'png'], key="indoor_upload")
            if uploaded_indoor:
                save_path = STATIC_DIR / 'layout_indoor.jpg'
                with open(save_path, 'wb') as f:
                    f.write(uploaded_indoor.getbuffer())
                st.success(f"Layout indoor tersimpan!")
                st.image(uploaded_indoor, caption="Preview Indoor", use_column_width=True)
        
        with col2:
            uploaded_logo = st.file_uploader("Upload Logo Aplikasi (PNG)", type=['png'], key="logo_upload")
            if uploaded_logo:
                save_path = STATIC_DIR / 'logo.png'
                with open(save_path, 'wb') as f:
                    f.write(uploaded_logo.getbuffer())
                st.success("Logo tersimpan!")
                st.image(uploaded_logo, caption="Preview Logo", width=180)
        
        st.markdown("---")
        st.markdown("### Konfigurasi Saat Ini")
        
        if layout_config:
            st.json(layout_config)
        else:
            st.info("Belum ada konfigurasi.")