import streamlit as st
import pandas as pd
import datetime
from utils.config import get_glpi_config
from utils.glpi_api import GLPIClient
from utils.pdf_generator import A4ReportPDF

st.set_page_config(page_title="Relatório GLPI", page_icon="🎫", layout="wide")

st.title("🎫 Relatório de Atendimentos - GLPI")

cfg = get_glpi_config()
if not cfg.get("url") or not cfg.get("user_token") or not cfg.get("app_token"):
    st.warning("Configurações do GLPI não encontradas. Vá até a aba de Configurações.")
    st.stop()

try:
    glpi = GLPIClient(cfg["url"], cfg["user_token"], cfg["app_token"])
except Exception as e:
    st.error(f"Erro ao conectar no GLPI: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filtros do Relatório")

entities = glpi.get_entities()
entity_options = {e["name"]: e["id"] for e in entities}

if not entity_options:
    st.sidebar.warning("Nenhuma entidade encontrada ou falta de permissão.")
    st.stop()

selected_entity_name = st.sidebar.selectbox("Selecione a Entidade", options=list(entity_options.keys()))
selected_entity_id = entity_options[selected_entity_name]

# Date range
today = datetime.date.today()
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Data Inicial", today - datetime.timedelta(days=30))
end_date = col2.date_input("Data Final", today)

generate_btn = st.sidebar.button("Gerar Relatório")

# --- Report Body ---
if generate_btn:
    st.markdown("---")
    st.markdown(f"## Relação de chamados da {selected_entity_name}")
    st.markdown(f"**Período:** {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    
    with st.spinner("Buscando chamados no GLPI..."):
        tickets = glpi.get_tickets(selected_entity_id, start_date, end_date)
        
        if not tickets:
            st.info("Nenhum chamado encontrado para esta entidade neste período.")
        else:
            df_tickets = pd.DataFrame(tickets)
            
            # Show Metrics
            total_tickets = len(df_tickets)
            st.markdown(f"**Total de Chamados:** {total_tickets}")
            
            st.dataframe(df_tickets, use_container_width=True)
            
            # PDF Export
            pdf = A4ReportPDF(
                title=f"Relacao de chamados da {selected_entity_name}",
                subtitle=f"Periodo: {start_date} a {end_date}"
            )
            pdf.alias_nb_pages()
            pdf.add_page()
            
            pdf.add_table(df_tickets)
            
            pdf_bytes = bytes(pdf.output())
            
            st.download_button(
                label="📥 Exportar Relatório para PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_GLPI_{selected_entity_name}.pdf",
                mime="application/pdf"
            )

# Sempre feche a sessão ao fim
glpi.kill_session()
