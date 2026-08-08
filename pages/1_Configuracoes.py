import streamlit as st
from utils.config import get_zabbix_config, get_glpi_config, save_config, load_config

st.set_page_config(page_title="Configurações", page_icon="⚙️")

st.title("⚙️ Configurações de API")

st.markdown("""
Nesta tela, você deve configurar os dados de acesso para as APIs do Zabbix e do GLPI.
Esses dados ficarão salvos localmente no arquivo `config.json`.
""")

config = load_config()
zabbix_cfg = config.get("zabbix", {})
glpi_cfg = config.get("glpi", {})

# Zabbix Config
st.header("Zabbix")
with st.expander("Como criar o usuário no Zabbix", expanded=False):
    st.markdown("""
    **Zabbix 5.x / 6.x / 7.x:**
    1. Acesse o Zabbix com uma conta de Super Administrador.
    2. Vá em **Administração** -> **Usuários** (ou Administration -> Users).
    3. Crie um novo usuário (ex: `api_user`).
    4. Na aba **Permissões**, atribua uma função (Role) que tenha acesso de leitura (Super Admin ou Admin com permissões nos grupos necessários).
    5. Crie um **Token de API** (em Administração -> Geral -> Tokens de API ou na seção de usuário). Se estiver usando uma versão mais antiga, você pode usar Login e Senha diretamente.
    """)

with st.form("zabbix_form"):
    st.subheader("Credenciais Zabbix")
    zb_url = st.text_input("URL do Zabbix (ex: http://meuzabbix.com/zabbix)", value=zabbix_cfg.get("url", ""))
    zb_user = st.text_input("Usuário", value=zabbix_cfg.get("user", ""))
    zb_pass = st.text_input("Senha", type="password", value=zabbix_cfg.get("password", ""))
    # zb_token = st.text_input("Token de API (Opcional se usar senha)", type="password", value=zabbix_cfg.get("token", ""))
    
    zb_submit = st.form_submit_button("Salvar Configurações do Zabbix")
    
    if zb_submit:
        config["zabbix"] = {
            "url": zb_url,
            "user": zb_user,
            "password": zb_pass
        }
        save_config(config)
        st.success("Configurações do Zabbix salvas com sucesso!")

# GLPI Config
st.header("GLPI")
with st.expander("Como criar as credenciais de API no GLPI", expanded=False):
    st.markdown("""
    **GLPI 9.5 / 10.x:**
    1. Acesse o GLPI como Super-Admin.
    2. Vá em **Configurar** -> **Geral** -> aba **API**.
    3. Habilite a **API REST** e marque "Ativar o login com credenciais" (Enable login with credentials).
    4. Crie um **Cliente API (App-Token)**. Clique no botão de mais, defina um nome e copie o App-Token gerado.
    5. Vá no seu **Perfil de Usuário** (Canto superior direito -> Preferências).
    6. Na aba **Chaves de API (API Keys)**, gere um **User-Token** (Token de API).
    """)

with st.form("glpi_form"):
    st.subheader("Credenciais GLPI")
    gl_url = st.text_input("URL do GLPI (ex: http://meuglpi.com/apirest.php)", value=glpi_cfg.get("url", ""))
    gl_user_token = st.text_input("User Token", type="password", value=glpi_cfg.get("user_token", ""))
    gl_app_token = st.text_input("App Token", type="password", value=glpi_cfg.get("app_token", ""))
    
    gl_submit = st.form_submit_button("Salvar Configurações do GLPI")
    
    if gl_submit:
        config["glpi"] = {
            "url": gl_url,
            "user_token": gl_user_token,
            "app_token": gl_app_token
        }
        save_config(config)
        st.success("Configurações do GLPI salvas com sucesso!")
