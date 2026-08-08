from fpdf import FPDF
import pandas as pd
import os

class A4ReportPDF(FPDF):
    def __init__(self, title, subtitle):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.title_text = title
        self.subtitle_text = subtitle

    def header(self):
        # Arial bold 15
        self.set_font('helvetica', 'B', 15)
        # Title
        self.cell(0, 10, self.title_text, 0, 1, 'C')
        # Subtitle
        self.set_font('helvetica', '', 12)
        self.cell(0, 10, self.subtitle_text, 0, 1, 'C')
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('helvetica', 'I', 8)
        # Page number
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

    def add_table(self, dataframe, title=""):
        if title:
            self.set_font('helvetica', 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
            self.ln(2)

        self.set_font('helvetica', 'B', 10)
        
        # Calculate column widths
        col_widths = []
        if not dataframe.empty:
            total_width = 190 # A4 width is 210, margins are 10 each
            col_width = total_width / len(dataframe.columns)
            
            # Header
            for col in dataframe.columns:
                self.cell(col_width, 8, str(col), 1, 0, 'C')
            self.ln()
            
            # Rows
            self.set_font('helvetica', '', 9)
            for index, row in dataframe.iterrows():
                for item in row:
                    self.cell(col_width, 8, str(item)[:30], 1, 0, 'C') # Truncate long strings
                self.ln()
        else:
            self.set_font('helvetica', 'I', 10)
            self.cell(0, 10, "Sem dados disponíveis.", 0, 1, 'L')
        self.ln(5)
        
    def add_image(self, image_path, title=""):
        if title:
            self.set_font('helvetica', 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
            self.ln(2)
        
        if os.path.exists(image_path):
            # width 190mm fits A4
            self.image(image_path, x=10, w=190)
            self.ln(5)
