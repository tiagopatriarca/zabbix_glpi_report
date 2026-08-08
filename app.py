import streamlit as st

st.set_page_config(
    page_title="Gerador de Relatórios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Gerador de Relatórios Integrado")
st.markdown("""
Bem-vindo ao sistema de geração de relatórios!

Utilize o menu lateral para navegar entre:
- **⚙️ Configurações:** Configure os acessos ao Zabbix e ao GLPI.
- **📈 Relatório Zabbix:** Gere relatórios de infraestrutura e performance.
- **🎫 Relatório GLPI:** Gere relatórios de chamados e atendimento.

**Dica:** Antes de começar, certifique-se de configurar as credenciais de acesso na aba de Configurações.
""")
