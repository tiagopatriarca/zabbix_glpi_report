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
        
        import os
        import uuid
        
        # Lista para armazenar os caminhos das imagens geradas
        chart_images = []
        
        # Função auxiliar para buscar e desenhar gráficos
        def plot_metric(search_terms, title, chart_type="line", multi=False):
            found_items = []
            for term in search_terms:
                items = zapi.search_items_by_name(selected_host_id, term)
                if items:
                    if multi:
                        found_items.extend(items)
                    else:
                        found_items.append(items[0])
                        break
            
            if not found_items:
                st.info(f"Nenhum item encontrado para: {title}")
                return None
                
            fig = None
            if chart_type == "line":
                if multi:
                    # Multiplas linhas no mesmo grafico
                    fig = px.line(title=title)
                    has_data = False
                    for item in found_items:
                        df = zapi.get_history_data(item["itemid"], item["value_type"], start_dt, end_dt)
                        if not df.empty:
                            has_data = True
                            fig.add_scatter(x=df["time"], y=df["value"], mode="lines", name=item["name"])
                    if not has_data:
                        st.warning(f"Sem dados de histórico para {title}")
                        return None
                    fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                else:
                    item = found_items[0]
                    df = zapi.get_history_data(item["itemid"], item["value_type"], start_dt, end_dt)
                    if df.empty:
                        st.warning(f"Sem dados de histórico para {item['name']}")
                        return None
                    fig = px.line(df, x="time", y="value", title=f"{title} - {item['name']}")
                    if item["units"]:
                        fig.update_yaxes(title_text=item["units"])
                        
            elif chart_type == "pie":
                # Grafico de pizza (geralmente usado para uso de disco, que vem em porcentagem)
                item = found_items[0]
                if "lastvalue" in item and item["lastvalue"]:
                    used = float(item["lastvalue"])
                    free = 100.0 - used if used <= 100 else 0
                    labels = ['Utilizado', 'Livre']
                    values = [used, free]
                    fig = px.pie(values=values, names=labels, title=f"{title} ({item['name']})", color_discrete_sequence=['#ff4b4b', '#00bfa0'])
                else:
                    st.warning(f"Sem valor recente para montar a pizza de {title}")
                    return None
                    
            if fig:
                fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
                
                # Salvar imagem para o PDF
                try:
                    img_path = f"data/temp_{uuid.uuid4().hex[:8]}.png"
                    fig.write_image(img_path, width=800, height=400)
                    chart_images.append(img_path)
                except Exception as e:
                    st.error(f"Erro ao exportar imagem do gráfico: {str(e)}")
            
            return fig

        st.markdown("### 📊 Gráficos de Desempenho")
        
        # Linha 1: Processador e Memória
        col_cpu, col_mem = st.columns(2)
        with col_cpu:
            plot_metric(["CPU utilization", "CPU", "Processador"], "Processador", "line")
        with col_mem:
            plot_metric(["Memory utilization", "Available memory", "Total memory", "Memória"], "Memória", "line")
            
        # Linha 2: Discos
        st.markdown("#### Discos")
        col_disk1, col_disk2 = st.columns(2)
        with col_disk1:
            plot_metric(["Space utilization", "Free disk space", "Used disk space", "Espaço livre", "Espaço utilizado", "Uso de disco", "Disco", "Disk", "vfs.fs"], "Espaço em Disco", chart_type="pie")
            
        # Linha 3: Placas de Rede (Agrupadas por Interface)
        st.markdown("#### Tráfego de Rede")
        
        # Agrupar itens de rede por interface
        network_interfaces = {}
        net_items = zapi.search_items_by_name(selected_host_id, "Bits received") + zapi.search_items_by_name(selected_host_id, "Bits sent")
        if not net_items:
            net_items = zapi.search_items_by_name(selected_host_id, "Traffic in") + zapi.search_items_by_name(selected_host_id, "Traffic out")
            
        for item in net_items:
            # Extrair um nome limpo para agrupar (removendo as palavras padrao)
            clean_name = item["name"].replace("Bits received", "").replace("Bits sent", "").replace("Traffic in", "").replace("Traffic out", "").replace("Interface", "").replace(":", "").replace("()", "").replace("<", "").replace(">", "").strip()
            if not clean_name: clean_name = "Rede Padrão"
            
            if clean_name not in network_interfaces:
                network_interfaces[clean_name] = {"in": None, "out": None}
                
            if "received" in item["name"].lower() or "in" in item["name"].lower():
                network_interfaces[clean_name]["in"] = item
            else:
                network_interfaces[clean_name]["out"] = item
                
        if not network_interfaces:
            st.info("Nenhum item de rede encontrado.")
        else:
            for iface_name, items in network_interfaces.items():
                fig = px.line(title=f"Tráfego - {iface_name}")
                has_data = False
                
                # Plot IN
                if items["in"]:
                    df_in = zapi.get_history_data(items["in"]["itemid"], items["in"]["value_type"], start_dt, end_dt)
                    if not df_in.empty:
                        has_data = True
                        fig.add_scatter(x=df_in["time"], y=df_in["value"], mode="lines", name="Entrada (In)", line=dict(color="#00bfa0"))
                
                # Plot OUT
                if items["out"]:
                    df_out = zapi.get_history_data(items["out"]["itemid"], items["out"]["value_type"], start_dt, end_dt)
                    if not df_out.empty:
                        has_data = True
                        fig.add_scatter(x=df_out["time"], y=df_out["value"], mode="lines", name="Saída (Out)", line=dict(color="#ff4b4b"))
                        
                if has_data:
                    if items["in"] and items["in"]["units"]: fig.update_yaxes(title_text=items["in"]["units"])
                    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)
                    try:
                        img_path = f"data/temp_{uuid.uuid4().hex[:8]}.png"
                        fig.write_image(img_path, width=800, height=400)
                        chart_images.append(img_path)
                    except:
                        pass

        st.markdown("---")
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
        
        # Adiciona imagens dos gráficos no PDF (lado a lado)
        if chart_images:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Graficos de Desempenho', ln=True)
            
            x_pos = [10, 105]
            y = pdf.get_y()
            for i, img in enumerate(chart_images):
                if i > 0 and i % 2 == 0:
                    y += 55
                    if y > 230:
                        pdf.add_page()
                        y = 20
                try:
                    pdf.image(img, x=x_pos[i % 2], y=y, w=90)
                except Exception:
                    pass
            # Ajustar ponteiro Y proximo apos as imagens (considerando que há imagens)
            final_y = y + 60 if len(chart_images) > 0 else y
            if final_y > 250:
                pdf.add_page()
                final_y = 20
            pdf.set_y(final_y)
                
        pdf.add_table(df_active, "Alertas Ativos")
        pdf.add_table(df_history, "Historico de Alertas")
        
        pdf_bytes = bytes(pdf.output())
        
        # Limpar imagens temporárias
        for img in chart_images:
            if os.path.exists(img):
                os.remove(img)
        
        st.download_button(
            label="📥 Exportar Relatório para PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_Zabbix_{selected_host_name}.pdf",
            mime="application/pdf"
        )
