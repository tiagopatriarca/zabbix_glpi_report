import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from utils.config import get_zabbix_config
from utils.zabbix_api import ZabbixClient
from utils.pdf_generator import A4ReportPDF
import io

st.set_page_config(page_title="Relatório Zabbix", page_icon="📈", layout="wide")

st.title("📈 Relatório de Infraestrutura - Zabbix")

cfg = get_zabbix_config()
if not cfg.get("url") or not cfg.get("user") or not cfg.get("password"):
    st.warning("Configurações do Zabbix não encontradas. Vá até a aba de Configurações.")
    st.stop()

# Initialize Zabbix Client
try:
    zapi = ZabbixClient(cfg["url"], cfg["user"], cfg["password"])
except Exception as e:
    st.error(f"Erro ao conectar no Zabbix: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filtros do Relatório")

# Fetch Hostgroups
groups = zapi.get_hostgroups()
group_options = {g["name"]: g["groupid"] for g in groups}
selected_group_name = st.sidebar.selectbox("Selecione o Grupo de Hosts", options=list(group_options.keys()))

selected_group_id = group_options[selected_group_name]

# Fetch Hosts for selected group
hosts = zapi.get_hosts_by_group(selected_group_id)
host_options = {h["name"]: h["hostid"] for h in hosts}

if not host_options:
    st.sidebar.warning("Nenhum host encontrado neste grupo.")
    st.stop()

selected_host_name = st.sidebar.selectbox("Selecione o Host", options=list(host_options.keys()))
selected_host_id = host_options[selected_host_name]

# Date range
today = datetime.date.today()
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Data Inicial", today - datetime.timedelta(days=7))
end_date = col2.date_input("Data Final", today)

start_dt = datetime.datetime.combine(start_date, datetime.time.min)
end_dt = datetime.datetime.combine(end_date, datetime.time.max)

generate_btn = st.sidebar.button("Gerar Relatório")

# --- Report Body ---
if generate_btn:
    st.markdown("---")
    st.subheader(f"Grupo: {selected_group_name}")
    st.markdown(f"#### Host: {selected_host_name}")
    st.markdown(f"**Período:** {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
    
    with st.spinner("Buscando dados no Zabbix..."):
        # We need item keys for CPU, Memory, Disk, Network.
        # This can vary greatly depending on Zabbix templates. We'll try common keys.
        cpu_items = zapi.get_items_by_key(selected_host_id, "system.cpu.util")
        mem_items = zapi.get_items_by_key(selected_host_id, "vm.memory.util")
        
        # In a real scenario, network keys might be net.if.in, net.if.out
        # For simplicity, we just render mock charts if no data is found, or skip them.
        
        # Alertas Ativos
        st.markdown("### 🔴 Alertas Ativos")
        active_alerts = zapi.get_active_alerts(selected_host_id)
        if active_alerts:
            df_active = pd.DataFrame(active_alerts)
            st.dataframe(df_active, use_container_width=True)
        else:
            st.success("Nenhum alerta ativo no momento.")
            df_active = pd.DataFrame()

        # Histórico de Alertas
        st.markdown("### 📜 Histórico de Alertas no Período")
        history_alerts = zapi.get_alerts_history(selected_host_id, start_dt, end_dt)
        if history_alerts:
            df_history = pd.DataFrame(history_alerts)
            st.dataframe(df_history, use_container_width=True)
        else:
            st.info("Nenhum alerta ocorreu neste período.")
            df_history = pd.DataFrame()
            
        # PDF Export
        pdf = A4ReportPDF(
            title=f"Relatorio Zabbix - {selected_group_name}",
            subtitle=f"Host: {selected_host_name} | Período: {start_date} a {end_date}"
        )
        pdf.alias_nb_pages()
        pdf.add_page()
        
        pdf.add_table(df_active, "Alertas Ativos")
        pdf.add_table(df_history, "Historico de Alertas")
        
        pdf_bytes = bytes(pdf.output())
        
        st.download_button(
            label="📥 Exportar Relatório para PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_Zabbix_{selected_host_name}.pdf",
            mime="application/pdf"
        )
