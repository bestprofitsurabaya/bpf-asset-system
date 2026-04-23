"""
Maintenance Recommendations Module
"""

import streamlit as st
import database.crud_ac as db_ac
from utils.alerts import generate_maintenance_recommendations


def render_recommendations():
    """Render Maintenance Recommendations"""
    
    st.title("Rekomendasi Maintenance Cerdas")
    
    st.markdown("""
    Sistem ini secara otomatis menganalisis data maintenance dan memberikan rekomendasi 
    tindakan yang perlu dilakukan berdasarkan kondisi aktual aset.
    """)
    
    recommendations = generate_maintenance_recommendations(mode=st.session_state.db_mode)
    
    if recommendations:
        st.markdown(f"### Ditemukan {len(recommendations)} Rekomendasi")
        
        priority_filter = st.multiselect(
            "Filter by Priority",
            ['Critical', 'High', 'Medium', 'Normal'],
            default=['Critical', 'High']
        )
        
        filtered_recs = [r for r in recommendations if r['priority'] in priority_filter]
        
        for rec in filtered_recs:
            priority = rec.get('priority', 'Normal')
            asset_id = rec.get('asset_id', 'Unknown')
            urgency_days = rec.get('urgency_days', 0)
            estimated_cost = rec.get('estimated_cost', 0)
            actions = rec.get('actions', [])
            
            if priority == 'Critical':
                priority_color = '#dc3545'
                expander_label = f"{asset_id} - PRIORITAS: CRITICAL (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
            elif priority == 'High':
                priority_color = '#fd7e14'
                expander_label = f"{asset_id} - Prioritas: High (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
            elif priority == 'Medium':
                priority_color = '#ffc107'
                expander_label = f"{asset_id} - Prioritas: Medium (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
            else:
                priority_color = '#28a745'
                expander_label = f"{asset_id} - Prioritas: Normal (dalam {urgency_days} hari) - Est: Rp {estimated_cost:,.0f}"
            
            with st.expander(expander_label):
                st.markdown(f"""
                <div style="border-left: 5px solid {priority_color}; padding-left: 15px;">
                    <h4>Tindakan yang Direkomendasikan:</h4>
                    <ul>
                """, unsafe_allow_html=True)
                
                for action in actions:
                    st.markdown(f"<li>{action}</li>", unsafe_allow_html=True)
                
                st.markdown("</ul></div>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Tandai Selesai", key=f"done_{asset_id}"):
                        st.success(f"Rekomendasi untuk {asset_id} ditandai selesai")
                
                with col2:
                    if st.button(f"Jadwalkan Ulang", key=f"reschedule_{asset_id}"):
                        st.info(f"Jadwal untuk {asset_id} diundur 7 hari")
    else:
        st.success("Tidak ada rekomendasi maintenance saat ini. Semua aset dalam kondisi baik!")