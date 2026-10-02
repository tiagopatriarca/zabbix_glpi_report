import streamlit as st
import pandas as pd
import datetime
from utils.database import get_clients_for_user, get_glpi_configs
from utils.glpi_api import GLPIClient

st.set_page_config(page_title="Relatório GLPI", page_icon="🎫", layout="wide")

if not st.session_state.get('user'):
    st.warning("Por favor, faça login na tela inicial.")
    st.stop()

st.title("🎫 Relatório de Atendimentos - GLPI")

# --- Seleção de Cliente e Integração ---
user = st.session_state.user
clientes = get_clients_for_user(user['id'], user['is_admin'])

if not clientes:
    st.warning("Você não tem acesso a nenhum cliente.")
    st.stop()

client_dict = {c['name']: c['id'] for c in clientes}
selected_client = st.sidebar.selectbox("1. Selecione o Cliente", options=list(client_dict.keys()))
client_id = client_dict[selected_client]

configs = get_glpi_configs(client_id)
if not configs:
    st.warning("Este cliente não possui integrações GLPI cadastradas.")
    st.stop()

config_dict = {cfg['name']: cfg for cfg in configs}
selected_config_name = st.sidebar.selectbox("2. Selecione a Instância GLPI", options=list(config_dict.keys()))
cfg = config_dict[selected_config_name]

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
            
            # --- PDF Export com Modelo Gerencial JSON (Paisagem) ---
            from utils.pdf_gerencial import A4GerencialPDF
            
            dados_gerenciais = {
                "relatorio": {
                    "cabecalho": {
                        "empresa": selected_client,
                        "logo_url": "data/logo.png",
                        "tipo_documento": "RELATÓRIO TÉCNICO",
                        "data": datetime.date.today().strftime("%d/%m/%Y")
                    },
                    "titulo": {
                        "principal": f"Relação de chamados da {selected_entity_name}",
                        "subtitulo": f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
                    },
                    "rodape": {
                        "texto": f"{selected_client} - Gestão de infraestrutura",
                        "exibir_paginacao": True
                    }
                }
            }

            pdf = A4GerencialPDF(dados_gerenciais, orientation='L')
            pdf.render_report()
            
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
