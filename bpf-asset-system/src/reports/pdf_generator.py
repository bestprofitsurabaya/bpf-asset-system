"""
PDF Report Generator using FPDF
"""

from fpdf import FPDF
from datetime import datetime
import base64
from pathlib import Path
import pandas as pd
from typing import Dict, Optional
import streamlit as st

class PDFReport(FPDF):
    """Custom PDF Report class with header and footer"""
    
    def __init__(self, logo_path: Optional[Path] = None):
        super().__init__()
        self.logo_path = logo_path
    
    def header(self):
        """PDF header with logo and title"""
        if self.logo_path and self.logo_path.exists():
            self.image(str(self.logo_path), x=10, y=8, w=30)
        
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, 'PT BESTPROFIT FUTURES SURABAYA', 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.set_text_color(204, 0, 0)
        self.cell(0, 8, 'LAPORAN ASSET MANAGEMENT', 0, 1, 'C')
        self.set_draw_color(204, 0, 0)
        self.line(10, 28, 200, 28)
        self.ln(10)
    
    def footer(self):
        """PDF footer with page number and date"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        self.cell(0, 10, f'Dicetak: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'R')


class PDFGenerator:
    """PDF Report Generator"""
    
    def __init__(self, static_dir: Path):
        self.static_dir = static_dir
        self.logo_path = static_dir / 'logo.png'
    
    def generate_ac_report(self, logs: pd.DataFrame, asset_filter: str = "Semua",
                          date_range: str = "Semua") -> PDFReport:
        """Generate PDF report for AC maintenance"""
        pdf = PDFReport(self.logo_path)
        pdf.add_page()
        
        # Report info
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f'Periode: {date_range} | Asset: {asset_filter}', 0, 1, 'L')
        pdf.ln(5)
        
        # Summary
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'RINGKASAN', 1, 1, 'L', True)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        avg_health = logs['health_score'].mean() if 'health_score' in logs.columns else 0
        avg_delta = logs['delta_t'].mean() if 'delta_t' in logs.columns else 0
        total_cost = logs['sparepart_cost'].sum() if 'sparepart_cost' in logs.columns else 0
        
        pdf.cell(60, 7, f'Total Maintenance: {len(logs)} log', 0, 0)
        pdf.cell(60, 7, f'Rata-rata Health Score: {avg_health:.1f}%', 0, 1)
        pdf.cell(60, 7, f'Total Biaya Sparepart: Rp {total_cost:,.0f}', 0, 0)
        pdf.cell(60, 7, f'Rata-rata Delta T: {avg_delta:.1f} C', 0, 1)
        pdf.ln(5)
        
        # Table header
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        
        headers = ['Tanggal', 'Asset ID', 'Teknisi', 'Delta T', 'Health', 'Status']
        widths = [30, 50, 45, 25, 20, 25]
        
        for i, header in enumerate(headers):
            pdf.cell(widths[i], 8, header, 1, 0, 'C', True)
        pdf.ln()
        
        # Table data
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(0, 0, 0)
        
        logs_to_show = logs.head(50)
        
        for _, row in logs_to_show.iterrows():
            if 'tanggal' in row:
                tanggal_val = row['tanggal']
                if hasattr(tanggal_val, 'strftime'):
                    tanggal_str = tanggal_val.strftime('%Y-%m-%d')
                else:
                    tanggal_str = str(tanggal_val)[:10]
            else:
                tanggal_str = ''
            
            pdf.cell(widths[0], 7, tanggal_str, 1, 0, 'C')
            
            asset_id_str = str(row['asset_id'])[:20] if 'asset_id' in row else ''
            pdf.cell(widths[1], 7, asset_id_str, 1, 0, 'L')
            
            teknisi_str = str(row['teknisi'])[:15] if 'teknisi' in row else ''
            pdf.cell(widths[2], 7, teknisi_str, 1, 0, 'L')
            
            delta_val = row['delta_t'] if 'delta_t' in row else 0
            pdf.cell(widths[3], 7, f"{delta_val:.1f}", 1, 0, 'C')
            
            health = row['health_score'] if 'health_score' in row else 0
            if health >= 70:
                pdf.set_text_color(40, 167, 69)
            elif health >= 50:
                pdf.set_text_color(255, 193, 7)
            else:
                pdf.set_text_color(220, 53, 69)
            pdf.cell(widths[4], 7, f"{health}%", 1, 0, 'C')
            pdf.set_text_color(0, 0, 0)
            
            test_val = row['test_run'] if 'test_run' in row else ''
            pdf.cell(widths[5], 7, str(test_val)[:10], 1, 0, 'C')
            pdf.ln()
        
        if len(logs) > 50:
            pdf.set_font('Arial', 'I', 9)
            pdf.cell(0, 7, f'... dan {len(logs) - 50} data lainnya', 0, 1, 'C')
        
        # Footer signature
        pdf.ln(15)
        pdf.set_font('Arial', '', 10)
        pdf.cell(90, 7, 'Mengetahui,', 0, 0, 'C')
        pdf.cell(90, 7, 'Dibuat oleh,', 0, 1, 'C')
        pdf.ln(10)
        pdf.cell(90, 7, '_________________', 0, 0, 'C')
        pdf.cell(90, 7, '_________________', 0, 1, 'C')
        pdf.cell(90, 7, 'Manager Operasional', 0, 0, 'C')
        pdf.cell(90, 7, 'Teknisi', 0, 1, 'C')
        
        return pdf
    
    def generate_vehicle_report(self, vehicles: pd.DataFrame,
                               health_data: Dict) -> PDFReport:
        """Generate PDF report for vehicles"""
        pdf = PDFReport(self.logo_path)
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f'Tanggal Cetak: {datetime.now().strftime("%d %B %Y")}', 0, 1, 'L')
        pdf.ln(5)
        
        # Summary
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'RINGKASAN KENDARAAN', 1, 1, 'L', True)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        total_vehicles = len(vehicles)
        aktif_count = len(vehicles[vehicles['status'] == 'Aktif']) if 'status' in vehicles.columns else 0
        total_odometer = vehicles['last_odometer'].sum() if 'last_odometer' in vehicles.columns else 0
        
        pdf.cell(50, 7, f'Total Kendaraan: {total_vehicles}', 0, 0)
        pdf.cell(50, 7, f'Aktif: {aktif_count}', 0, 1)
        pdf.cell(50, 7, f'Total Odometer: {total_odometer:,.0f} km', 0, 1)
        pdf.ln(5)
        
        # Vehicle details
        for idx, (_, row) in enumerate(vehicles.iterrows()):
            if idx > 0 and idx % 5 == 0:
                pdf.add_page()
            
            health = health_data.get(row['vehicle_id'], {})
            
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 8, f"{row['vehicle_id']} - {row['brand']} {row['model']} ({row['year']})", 0, 1, 'L')
            
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(60, 6, f"Plat: {row['plate_number']}", 0, 0)
            pdf.cell(60, 6, f"Odometer: {row['last_odometer']:,.0f} km", 0, 1)
            pdf.cell(60, 6, f"Status: {row['status']}", 0, 0)
            
            if health:
                health_score = health.get('health_score', 0)
                if health_score >= 80:
                    pdf.set_text_color(40, 167, 69)
                elif health_score >= 60:
                    pdf.set_text_color(255, 193, 7)
                else:
                    pdf.set_text_color(220, 53, 69)
                pdf.cell(60, 6, f"Health Score: {health_score:.0f}%", 0, 1)
                pdf.set_text_color(0, 0, 0)
            
            pdf.ln(3)
            
            if health and health.get('next_services'):
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(200, 200, 200)
                pdf.cell(70, 6, 'Komponen', 1, 0, 'L', True)
                pdf.cell(50, 6, 'Pemakaian', 1, 0, 'C', True)
                pdf.cell(60, 6, 'Status', 1, 1, 'C', True)
                
                pdf.set_font('Arial', '', 9)
                for comp in health['next_services'][:5]:
                    comp_name = str(comp['component'])[:25]
                    pdf.cell(70, 6, comp_name, 1, 0, 'L')
                    pdf.cell(50, 6, f"{comp['usage_percent']:.0f}%", 1, 0, 'C')
                    status_str = str(comp['status'])[:20]
                    pdf.cell(60, 6, status_str, 1, 1, 'L')
            
            pdf.ln(5)
        
        return pdf
    
    def generate_executive_summary(self, summary: Dict) -> PDFReport:
        """Generate PDF for executive summary"""
        pdf = PDFReport(self.logo_path)
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, 'EXECUTIVE SUMMARY', 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f'Periode: {summary["period"]} | Tanggal: {summary["report_date"]}', 0, 1, 'L')
        pdf.ln(5)
        
        # Key Metrics
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'KEY METRICS', 1, 1, 'L', True)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(60, 7, f'Total Unit AC: {summary["ac_units"]}', 0, 0)
        pdf.cell(60, 7, f'Total Kendaraan: {summary["vehicles"]}', 0, 1)
        pdf.cell(60, 7, f'Total Maintenance AC: {summary["total_ac_maintenance"]}', 0, 0)
        pdf.cell(60, 7, f'Total Servis Kendaraan: {summary["total_vehicle_services"]}', 0, 1)
        pdf.cell(60, 7, f'Rata-rata Health Score AC: {summary["avg_ac_health"]:.1f}%', 0, 0)
        pdf.cell(60, 7, f'Total Biaya: {summary["cost_display"]}', 0, 1)
        pdf.ln(5)
        
        # Critical Units
        if summary.get("critical_ac_units"):
            pdf.set_font('Arial', 'B', 10)
            pdf.set_fill_color(220, 53, 69)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, 'UNIT AC KRITIS', 1, 1, 'L', True)
            
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(0, 0, 0)
            for unit in summary["critical_ac_units"]:
                pdf.cell(0, 7, f"{unit['asset_id']} - {unit['location']} - Health: {unit['health_score']:.0f}%", 0, 1)
            pdf.ln(5)
        
        # Vehicle Summary
        if summary.get("vehicle_health_summary"):
            pdf.set_font('Arial', 'B', 10)
            pdf.set_fill_color(0, 51, 102)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, 'STATUS KENDARAAN', 1, 1, 'L', True)
            
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(0, 0, 0)
            for v in summary["vehicle_health_summary"]:
                pdf.cell(0, 7, f"{v['vehicle_id']} - {v['name']} - Health: {v['health_score']:.0f}% - {v['status']}", 0, 1)
            pdf.ln(5)
        
        return pdf
    
    def get_download_link(self, pdf: PDFReport, filename: str) -> str:
        """Generate download link for PDF"""
        pdf_string = pdf.output(dest='S')
        b64 = base64.b64encode(pdf_string.encode('latin-1')).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none;padding:12px 24px;background:#CC0000;color:white;border-radius:8px;display:inline-block;">Download PDF: {filename}</a>'
        return href