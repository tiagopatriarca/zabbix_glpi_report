from fpdf import FPDF
import os

class A4GerencialPDF(FPDF):
    def __init__(self, data_json):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.data = data_json.get("relatorio", {})
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        cabecalho = self.data.get("cabecalho", {})
        
        # Logo
        logo_url = cabecalho.get("logo_url", "")
        if logo_url and os.path.exists(logo_url):
            try:
                self.image(logo_url, 10, 8, 33)
            except:
                pass
                
        # Cabecalho Direita
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 5, cabecalho.get("empresa", ""), border=0, ln=1, align='R')
        
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 5, cabecalho.get("tipo_documento", ""), border=0, ln=1, align='R')
        self.cell(0, 5, cabecalho.get("data", ""), border=0, ln=1, align='R')
        
        self.ln(10)
        # Linha
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        rodape = self.data.get("rodape", {})
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        texto = rodape.get("texto", "")
        
        if rodape.get("exibir_paginacao", True):
            self.cell(0, 10, f'{texto} | Página {self.page_no()}/{{nb}}', 0, 0, 'C')
        else:
            self.cell(0, 10, texto, 0, 0, 'C')

    def render_report(self):
        self.add_page()
        self.set_text_color(0, 0, 0)
        
        titulo = self.data.get("titulo", {})
        self.set_font('helvetica', 'B', 18)
        self.cell(0, 10, titulo.get("principal", ""), 0, 1, 'C')
        self.set_font('helvetica', '', 12)
        self.cell(0, 10, titulo.get("subtitulo", ""), 0, 1, 'C')
        self.ln(10)
        
        secoes = self.data.get("secoes", {})
        
        # 1. Resumo Executivo
        resumo = secoes.get("resumo_executivo", {})
        if resumo:
            self._render_section_title(resumo.get("titulo", ""))
            self.set_font('helvetica', '', 10)
            # FPDF2 might prefer encoding fixes if passing accents, but we will pass standard strings
            self.multi_cell(0, 6, resumo.get("conteudo", ""))
            self.ln(5)
            for anexo in resumo.get("anexos", []):
                self.set_font('helvetica', 'I', 10)
                self.cell(0, 10, anexo.get("descricao", ""), 1, 1, 'C')
            self.ln(5)
            
        # 2. Analise Infra
        infra = secoes.get("analise_infraestrutura", {})
        if infra:
            self._render_section_title(infra.get("titulo", ""))
            self.set_font('helvetica', '', 10)
            self.multi_cell(0, 6, infra.get("descricao", ""))
            self.ln(5)
            
            for item in infra.get("itens", []):
                self.set_font('helvetica', 'B', 10)
                # Guarda pos Y atual
                y_before = self.get_y()
                
                self.cell(60, 8, item.get("equipamento", ""), border=0)
                
                cor = item.get("cor_status", "black")
                if cor == "green": self.set_text_color(0, 150, 0)
                elif cor == "orange": self.set_text_color(255, 140, 0)
                elif cor == "red": self.set_text_color(220, 0, 0)
                else: self.set_text_color(0, 0, 0)
                
                self.cell(25, 8, f"[{item.get('status', '')}]", border=0)
                self.set_text_color(0, 0, 0)
                
                self.set_font('helvetica', '', 10)
                # Usa X=95 para observações
                self.set_xy(95, y_before)
                self.multi_cell(0, 8, item.get("observacoes", ""))
                self.ln(2)
            self.ln(5)
            
        # 3. Ações
        acoes = secoes.get("acoes_realizadas", {})
        if acoes:
            self._render_section_title(acoes.get("titulo", ""))
            self.set_font('helvetica', '', 10)
            self.multi_cell(0, 6, acoes.get("descricao", ""))
            self.ln(3)
            
            for acao in acoes.get("lista_acoes", []):
                self.set_x(10)
                self.cell(5, 6, "-", 0, 0)
                self.multi_cell(0, 6, acao)
            self.ln(5)
            
        # 4. Recomendações
        recom = secoes.get("recomendacoes", {})
        if recom:
            self._render_section_title(recom.get("titulo", ""))
            self.set_font('helvetica', '', 10)
            self.multi_cell(0, 6, recom.get("descricao", ""))
            self.ln(3)
            
            for rec in recom.get("lista_recomendacoes", []):
                self.set_font('helvetica', 'B', 10)
                self.cell(0, 6, rec.get("acao", ""), 0, 1)
                self.set_font('helvetica', '', 10)
                self.multi_cell(0, 6, rec.get("detalhe", ""))
                self.ln(2)
            self.ln(10)
            
        # Assinatura
        ass = self.data.get("assinatura", {})
        if ass:
            self.ln(20)
            self.set_draw_color(0, 0, 0)
            self.line(60, self.get_y(), 150, self.get_y())
            self.ln(2)
            self.set_font('helvetica', 'B', 10)
            self.cell(0, 5, ass.get("equipe", ""), 0, 1, 'C')
            self.set_font('helvetica', '', 10)
            self.cell(0, 5, ass.get("departamento", ""), 0, 1, 'C')
            
    def _render_section_title(self, text):
        self.set_font('helvetica', 'B', 14)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, text, 0, 1, 'L', fill=True)
        self.ln(3)

    def add_table(self, dataframe, title=""):
        if title:
            self.set_font('helvetica', 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
            self.ln(2)

        self.set_font('helvetica', 'B', 10)
        
        if not dataframe.empty:
            total_width = 190
            col_width = total_width / len(dataframe.columns)
            
            for col in dataframe.columns:
                self.cell(col_width, 8, str(col), 1, 0, 'C')
            self.ln()
            
            self.set_font('helvetica', '', 9)
            for index, row in dataframe.iterrows():
                for item in row:
                    self.cell(col_width, 8, str(item)[:30], 1, 0, 'C')
                self.ln()
        else:
            self.set_font('helvetica', 'I', 10)
            self.cell(0, 10, "Sem dados disponíveis.", 0, 1, 'L')
        self.ln(5)
        
    def add_image(self, image_path, title="", w=190, x=10, y=None):
        if title:
            self.set_font('helvetica', 'B', 12)
            self.cell(0, 10, title, 0, 1, 'L')
            self.ln(2)
        
        if os.path.exists(image_path):
            if y is not None:
                self.image(image_path, x=x, y=y, w=w)
            else:
                self.image(image_path, x=x, w=w)
                self.ln(5)
