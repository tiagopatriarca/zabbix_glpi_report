import streamlit as st
from utils.database import get_db, hash_password

st.set_page_config(page_title="Administração", page_icon="⚙️", layout="wide")

if not st.session_state.get('user'):
    st.warning("Por favor, faça login na tela inicial.")
    st.stop()

if not st.session_state.user.get('is_admin'):
    st.error("Acesso negado. Apenas administradores podem acessar esta página.")
    st.stop()

st.title("⚙️ Administração do Sistema")
st.markdown("Gerencie clientes, integrações e usuários.")

tabs = st.tabs(["🏢 Clientes", "🌐 Integrações", "👥 Usuários"])

def fetch_clients():
    c = get_db().cursor()
    c.execute("SELECT * FROM clients")
    return [dict(row) for row in c.fetchall()]

# --- Aba de Clientes ---
with tabs[0]:
    st.subheader("Gerenciar Clientes")
    with st.form("add_client_form"):
        c_name = st.text_input("Nome do Cliente")
        if st.form_submit_button("Adicionar Cliente"):
            if c_name:
                conn = get_db()
                conn.execute("INSERT INTO clients (name) VALUES (?)", (c_name,))
                conn.commit()
                st.success("Cliente adicionado!")
                st.rerun()
    
    clients = fetch_clients()
    if clients:
        for cl in clients:
            st.write(f"- {cl['name']}")

# --- Aba de Integrações ---
with tabs[1]:
    st.subheader("Configurar Zabbix & GLPI")
    clients = fetch_clients()
    if not clients:
        st.info("Cadastre um cliente primeiro.")
    else:
        client_dict = {c['name']: c['id'] for c in clients}
        selected_client = st.selectbox("Selecione o Cliente", options=list(client_dict.keys()))
        client_id = client_dict[selected_client]
        
        col_z, col_g = st.columns(2)
        with col_z:
            st.markdown("#### Zabbix")
            with st.form("add_zabbix"):
                z_name = st.text_input("Nome/Identificação (Ex: Zabbix Matriz)")
                z_url = st.text_input("URL do Zabbix (ex: http://ip/zabbix)")
                z_user = st.text_input("Usuário")
                z_pass = st.text_input("Senha", type="password")
                if st.form_submit_button("Salvar Zabbix"):
                    conn = get_db()
                    conn.execute("INSERT INTO zabbix_configs (client_id, name, url, username, password) VALUES (?, ?, ?, ?, ?)", 
                                 (client_id, z_name, z_url, z_user, z_pass))
                    conn.commit()
                    st.success("Zabbix configurado!")
        with col_g:
            st.markdown("#### GLPI")
            with st.form("add_glpi"):
                g_name = st.text_input("Nome/Identificação (Ex: GLPI Matriz)")
                g_url = st.text_input("URL do GLPI (ex: http://ip/glpi/apirest.php)")
                g_utoken = st.text_input("User Token")
                g_atoken = st.text_input("App Token")
                if st.form_submit_button("Salvar GLPI"):
                    conn = get_db()
                    conn.execute("INSERT INTO glpi_configs (client_id, name, url, user_token, app_token) VALUES (?, ?, ?, ?, ?)", 
                                 (client_id, g_name, g_url, g_utoken, g_atoken))
                    conn.commit()
                    st.success("GLPI configurado!")

# --- Aba de Usuários ---
with tabs[2]:
    st.subheader("Gerenciar Usuários")
    with st.form("add_user"):
        u_name = st.text_input("Nome de Usuário (Login)")
        u_pass = st.text_input("Senha", type="password")
        u_admin = st.checkbox("É Administrador?")
        if st.form_submit_button("Criar Usuário"):
            if u_name and u_pass:
                conn = get_db()
                try:
                    conn.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)", 
                                 (u_name, hash_password(u_pass), 1 if u_admin else 0))
                    conn.commit()
                    st.success("Usuário criado!")
                    st.rerun()
                except Exception as e:
                    st.error("Erro (usuário já existe?)")
                    
    st.markdown("---")
    st.subheader("Permissões de Acesso (Usuários vs Clientes)")
    conn = get_db()
    users = [dict(r) for r in conn.execute("SELECT id, username FROM users WHERE is_admin=0").fetchall()]
    
    if users and clients:
        u_dict = {u['username']: u['id'] for u in users}
        c_dict = {c['name']: c['id'] for c in clients}
        
        sel_u = st.selectbox("Selecione o Usuário Comum", options=list(u_dict.keys()))
        sel_c = st.selectbox("Selecione o Cliente que ele pode acessar", options=list(c_dict.keys()))
        
        if st.button("Conceder Acesso"):
            try:
                conn.execute("INSERT INTO user_clients (user_id, client_id) VALUES (?, ?)", (u_dict[sel_u], c_dict[sel_c]))
                conn.commit()
                st.success("Acesso concedido!")
            except:
                st.info("Este usuário já tem acesso a este cliente.")
