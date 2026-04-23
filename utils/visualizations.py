"""
Visualization Functions using Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from config.settings import COLORS


def create_health_gauge(health_score, title="Health Score"):
    """Create gauge chart for health score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=health_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': COLORS['primary']}},
        delta={'reference': 75},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': COLORS['primary']},
            'steps': [
                {'range': [0, 50], 'color': COLORS['danger']},
                {'range': [50, 70], 'color': COLORS['warning']},
                {'range': [70, 85], 'color': '#fd7e14'},
                {'range': [85, 100], 'color': COLORS['success']}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 65
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_correlation_heatmap(logs):
    """Create correlation heatmap"""
    numeric_cols = ['health_score', 'delta_t', 'amp_kompresor', 'low_p',
                   'high_p', 'temp_outdoor', 'sparepart_cost']
    
    available_cols = [col for col in numeric_cols if col in logs.columns]
    corr_matrix = logs[available_cols].corr()
    
    fig = px.imshow(
        corr_matrix,
        text_auto='.2f',
        color_continuous_scale='RdBu_r',
        title='Korelasi Antar Parameter',
        aspect="auto"
    )
    fig.update_layout(height=400)
    return fig


def create_3d_scatter(logs):
    """Create 3D scatter plot for multivariate analysis"""
    if len(logs) > 500:
        logs = logs.tail(500)
    
    fig = px.scatter_3d(
        logs,
        x='amp_kompresor',
        y='delta_t',
        z='health_score',
        color='health_score',
        size='sparepart_cost' if 'sparepart_cost' in logs.columns else None,
        hover_name='asset_id',
        title='Analisis Multivariat: Arus vs Delta T vs Health Score',
        color_continuous_scale='RdYlGn',
        opacity=0.7
    )
    fig.update_layout(height=500)
    return fig


def create_degradation_timeline(asset_id, logs):
    """Create degradation timeline with confidence bands"""
    asset_logs = logs[logs['asset_id'] == asset_id].copy()
    if asset_logs.empty:
        return None
    
    asset_logs['tanggal'] = pd.to_datetime(asset_logs['tanggal'])
    asset_logs = asset_logs.sort_values('tanggal')
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Health Score Trend', 'Delta T Trend', 'Ampere Trend'),
        shared_xaxes=True,
        vertical_spacing=0.08
    )
    
    # Health Score
    fig.add_trace(
        go.Scatter(
            x=asset_logs['tanggal'],
            y=asset_logs['health_score'],
            mode='lines+markers',
            name='Health Score',
            line=dict(color=COLORS['success'], width=2),
            marker=dict(size=6, color=COLORS['success'])
        ),
        row=1, col=1
    )
    
    if len(asset_logs) >= 5:
        x_numeric = list(range(len(asset_logs)))
        z = np.polyfit(x_numeric, asset_logs['health_score'].values, 1)
        trend = np.poly1d(z)
        fig.add_trace(
            go.Scatter(
                x=asset_logs['tanggal'],
                y=trend(x_numeric),
                mode='lines',
                name='Trend',
                line=dict(color='red', dash='dash', width=2)
            ),
            row=1, col=1
        )
    
    # Delta T
    fig.add_trace(
        go.Scatter(
            x=asset_logs['tanggal'],
            y=asset_logs['delta_t'],
            mode='lines+markers',
            name='Delta T',
            line=dict(color=COLORS['info'], width=2),
            marker=dict(size=6, color=COLORS['info'])
        ),
        row=2, col=1
    )
    
    # Ampere
    fig.add_trace(
        go.Scatter(
            x=asset_logs['tanggal'],
            y=asset_logs['amp_kompresor'],
            mode='lines+markers',
            name='Ampere',
            line=dict(color='#fd7e14', width=2),
            marker=dict(size=6, color='#fd7e14')
        ),
        row=3, col=1
    )
    
    fig.add_hline(y=65, line_dash="dash", line_color="red", row=1, col=1,
                  annotation_text="Critical", annotation_position="bottom right")
    fig.add_hline(y=8, line_dash="dash", line_color="orange", row=2, col=1,
                  annotation_text="Minimum", annotation_position="bottom right")
    fig.add_hline(y=25, line_dash="dash", line_color="red", row=3, col=1,
                  annotation_text="Warning", annotation_position="bottom right")
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text=f"Degradasi Timeline - {asset_id}",
        hovermode='x unified'
    )
    
    return fig


def create_radar_chart(asset_readings, asset_id):
    """Create radar chart for multi-parameter comparison"""
    categories = ['Health Score', 'Delta T', 'Efisiensi',
                 'Arus Normal', 'Tekanan Stabil', 'Drainase']
    
    health = asset_readings.get('health_score', 0)
    delta_t = min(100, asset_readings.get('delta_t', 0) * 8.33)
    efisiensi = min(100, max(0, 100 - abs(asset_readings.get('amp_kompresor', 15) - 15) * 5))
    arus_normal = min(100, max(0, 100 - abs(asset_readings.get('amp_kompresor', 15) - 15) * 4))
    tekanan = min(100, max(0, 100 - abs(asset_readings.get('low_p', 140) - 140) * 2))
    drainase = 100 if asset_readings.get('drainage') == 'Lancar' else 50
    
    values = [health, delta_t, efisiensi, arus_normal, tekanan, drainase]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=asset_id,
        line=dict(color=COLORS['primary'], width=2),
        fillcolor=f"rgba(0, 51, 102, 0.3)"
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[80, 80, 80, 80, 80, 80],
        theta=categories,
        fill='none',
        name='Target Minimum',
        line=dict(color=COLORS['success'], dash='dash', width=2)
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=f"Multi-Parameter Analysis - {asset_id}",
        showlegend=True,
        height=400
    )
    
    return fig


def create_cost_analysis_charts(services):
    """Create cost analysis charts"""
    if services.empty:
        return None, None
    
    vehicle_cost = services.groupby('vehicle_id')['cost'].sum().sort_values(ascending=True)
    
    fig_vehicle = go.Figure()
    fig_vehicle.add_trace(go.Bar(
        x=vehicle_cost.values,
        y=vehicle_cost.index,
        orientation='h',
        marker_color=COLORS['primary'],
        text=vehicle_cost.values,
        texttemplate='Rp %{text:,.0f}',
        textposition='outside'
    ))
    fig_vehicle.update_layout(
        title='Biaya Servis per Kendaraan',
        xaxis_title='Total Biaya (Rp)',
        height=400,
        margin=dict(l=150)
    )
    
    component_cost = services.groupby('component_name')['cost'].sum().sort_values(ascending=True)
    
    fig_component = go.Figure()
    fig_component.add_trace(go.Bar(
        x=component_cost.values,
        y=component_cost.index,
        orientation='h',
        marker_color=COLORS['secondary'],
        text=component_cost.values,
        texttemplate='Rp %{text:,.0f}',
        textposition='outside'
    ))
    fig_component.update_layout(
        title='Biaya Servis per Komponen',
        xaxis_title='Total Biaya (Rp)',
        height=400,
        margin=dict(l=150)
    )
    
    return fig_vehicle, fig_component


def create_monthly_trend_chart(services):
    """Create monthly cost trend chart"""
    if services.empty:
        return None
    
    services['service_date'] = pd.to_datetime(services['service_date'])
    monthly_cost = services.groupby(services['service_date'].dt.to_period('M'))['cost'].sum().reset_index()
    monthly_cost['service_date'] = monthly_cost['service_date'].astype(str)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_cost['service_date'],
        y=monthly_cost['cost'],
        mode='lines+markers',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=10, color=COLORS['secondary']),
        fill='tozeroy',
        fillcolor=f"rgba(0, 51, 102, 0.1)"
    ))
    fig.update_layout(
        title='Tren Biaya Servis Bulanan',
        xaxis_title='Bulan',
        yaxis_title='Total Biaya (Rp)',
        height=350
    )
    
    return fig