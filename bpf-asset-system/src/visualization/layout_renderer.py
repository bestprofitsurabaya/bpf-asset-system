"""
AC Layout Renderer
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from PIL import Image
import json
from typing import Dict, Optional, Tuple

from src.utils.helpers import get_health_color, get_health_status

class ACLayoutRenderer:
    """AC Layout renderer for interactive floor plan"""
    
    def __init__(self, static_dir: Path, config_dir: Path):
        self.static_dir = static_dir
        self.config_dir = config_dir
        self.config_path = config_dir / 'ac_layout_config.json'
    
    def load_config(self) -> Dict:
        """Load AC layout configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
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
    
    def save_config(self, config: Dict) -> bool:
        """Save AC layout configuration"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Gagal menyimpan konfigurasi: {e}")
            return False
    
    def get_ac_health_info(self, asset_id: str, logs: pd.DataFrame,
                          assets: pd.DataFrame) -> Tuple[str, str, float, str]:
        """Get health status info for AC unit"""
        color = '#6c757d'
        status = 'No Data'
        health = 0
        tooltip = 'Belum ada data maintenance'
        
        if not logs.empty:
            asset_logs = logs[logs['asset_id'] == asset_id]
            if not asset_logs.empty:
                latest = asset_logs.iloc[-1]
                health = latest['health_score'] if 'health_score' in latest else 0
                color = get_health_color(health)
                status = get_health_status(health)
                
                delta_t = latest['delta_t'] if 'delta_t' in latest else 0
                amp = latest['amp_kompresor'] if 'amp_kompresor' in latest else 0
                last_date = latest['tanggal'] if 'tanggal' in latest else 'Unknown'
                tooltip = f'Delta T: {delta_t:.1f}C | Amp: {amp:.1f}A | Last: {last_date}'
        
        return color, status, health, tooltip
    
    def render_indoor_layout(self, logs: pd.DataFrame, assets: pd.DataFrame) -> Optional[go.Figure]:
        """Render indoor layout with AC markers"""
        config = self.load_config()
        indoor_config = config.get('indoor', {})
        
        if not indoor_config:
            return None
        
        bg_path = self.static_dir.parent / indoor_config.get('background', '')
        use_image_background = bg_path.exists()
        
        fig = go.Figure()
        
        if use_image_background:
            try:
                img = Image.open(bg_path)
                fig.add_layout_image(
                    dict(
                        source=img,
                        xref="x",
                        yref="y",
                        x=0,
                        y=indoor_config.get('height', 700),
                        sizex=indoor_config.get('width', 1000),
                        sizey=indoor_config.get('height', 700),
                        sizing="stretch",
                        layer="below"
                    )
                )
            except Exception as e:
                st.warning(f"Gagal memuat gambar background: {e}")
        
        # Add AC units
        for ac in indoor_config.get('ac_units', []):
            asset_id = ac['asset_id']
            color, status, health, tooltip = self.get_ac_health_info(asset_id, logs, assets)
            
            asset_info = assets[assets['asset_id'] == asset_id] if not assets.empty else pd.DataFrame()
            location = asset_info['lokasi'].iloc[0] if not asset_info.empty else ac.get('room', asset_id)
            room = ac.get('room', location)
            
            # Determine marker symbol
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
                y=[indoor_config.get('height', 700) - ac['y']],
                mode='markers+text',
                marker=dict(
                    size=size,
                    color=color,
                    symbol=symbol,
                    line=dict(width=2, color='white')
                ),
                text=[ac.get('label', asset_id[-2:])],
                textposition="top center",
                textfont=dict(size=11, color='black', family='Arial Black'),
                name=asset_id,
                hovertemplate=f"<b>{asset_id}</b><br>Ruangan: {room}<br>Status: {status}<br>Health: {health:.0f}%<br>{tooltip}<extra></extra>"
            ))
        
        fig.update_layout(
            width=indoor_config.get('width', 1000),
            height=indoor_config.get('height', 700),
            xaxis=dict(range=[0, indoor_config.get('width', 1000)], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[0, indoor_config.get('height', 700)], showgrid=False, zeroline=False, visible=False),
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            title="Layout Indoor - Status AC",
            hovermode='closest'
        )
        
        return fig
    
    def render_outdoor_grid(self, logs: pd.DataFrame, assets: pd.DataFrame):
        """Render outdoor grid layout"""
        config = self.load_config()
        outdoor_config = config.get('outdoor', {})
        
        if not outdoor_config:
            st.info("Konfigurasi layout outdoor belum tersedia.")
            return
        
        st.markdown("""
        <style>
        .outdoor-grid-container {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 15px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
            border: 2px solid #003366;
        }
        .outdoor-unit {
            aspect-ratio: 1;
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            padding: 10px;
        }
        .outdoor-unit:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .outdoor-unit .unit-number {
            font-size: 2em;
            font-weight: bold;
        }
        .outdoor-unit .unit-status {
            font-size: 0.8em;
            margin-top: 5px;
        }
        .btu-60 { background-color: #437c4d; }
        .btu-100 { background-color: #f1e05a; color: black; text-shadow: none; }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="outdoor-grid-container">', unsafe_allow_html=True)
        
        grid_items = {}
        for ac in outdoor_config.get('ac_units', []):
            key = f"{ac.get('grid_row', 1)}_{ac.get('grid_col', 1)}"
            grid_items[key] = ac
        
        for row in range(1, 3):
            for col in range(1, 6):
                key = f"{row}_{col}"
                ac = grid_items.get(key)
                
                if ac:
                    asset_id = ac['asset_id']
                    color, status, health, tooltip = self.get_ac_health_info(asset_id, logs, assets)
                    
                    capacity_class = "btu-100" if ac.get('capacity') == "100.000 Btu/h" else "btu-60"
                    
                    status_badge = ""
                    if status in ['Critical', 'Severe']:
                        status_badge = "RED"
                    elif status == 'Warning':
                        status_badge = "YELLOW"
                    elif status == 'Good':
                        status_badge = "GREEN"
                    
                    st.markdown(f"""
                    <div class="outdoor-unit {capacity_class}" title="{asset_id} - Health: {health:.0f}% - {tooltip}">
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
    
    def render_legend(self):
        """Render status legend"""
        st.markdown("### Legenda Status AC")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#f0fff4; border-radius:10px;">
                <h3 style="color:#28a745;">GREEN - GOOD</h3>
                <p>Health > 80%</p>
                <p>Aman, operasi normal</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#fffbf0; border-radius:10px;">
                <h3 style="color:#ffc107;">YELLOW - WARNING</h3>
                <p>Health 60-80%</p>
                <p>Perlu perhatian</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#fff5f0; border-radius:10px;">
                <h3 style="color:#fd7e14;">ORANGE - CRITICAL</h3>
                <p>Health 40-60%</p>
                <p>Segera tindak lanjut</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#fff5f5; border-radius:10px;">
                <h3 style="color:#dc3545;">RED - SEVERE</h3>
                <p>Health < 40%</p>
                <p>STOP OPERASI!</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown("""
            <div style="text-align:center; padding:10px; background:#f8f9fa; border-radius:10px;">
                <h3 style="color:#6c757d;">WHITE - NO DATA</h3>
                <p>Belum ada log</p>
                <p>Perlu input data</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_status_table(self, logs: pd.DataFrame, assets: pd.DataFrame) -> pd.DataFrame:
        """Render status summary table"""
        config = self.load_config()
        indoor_config = config.get('indoor', {})
        
        status_data = []
        for ac in indoor_config.get('ac_units', []):
            asset_id = ac['asset_id']
            color, status, health, tooltip = self.get_ac_health_info(asset_id, logs, assets)
            
            asset_info = assets[assets['asset_id'] == asset_id] if not assets.empty else pd.DataFrame()
            location = asset_info['lokasi'].iloc[0] if not asset_info.empty else ac.get('room', '-')
            
            status_emoji = "GREEN" if status == 'Good' else "YELLOW" if status == 'Warning' else "ORANGE" if status == 'Critical' else "RED" if status == 'Severe' else "WHITE"
            
            status_data.append({
                'Status': status_emoji,
                'Asset ID': asset_id,
                'Label': ac.get('label', '-'),
                'Ruangan': ac.get('room', location),
                'Health': f"{health:.0f}%" if health > 0 else "N/A",
                'Kondisi': status
            })
        
        return pd.DataFrame(status_data)