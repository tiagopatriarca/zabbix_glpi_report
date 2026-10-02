import streamlit as st
from utils.database import get_db, hash_password, update_client, update_zabbix_config, update_glpi_config, update_user

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
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cadastrar Cliente")
        with st.form("add_client_form"):
            c_name = st.text_input("Nome do Cliente")
            if st.form_submit_button("Adicionar Cliente"):
                if c_name:
                    conn = get_db()
                    conn.execute("INSERT INTO clients (name) VALUES (?)", (c_name,))
                    conn.commit()
                    st.success("Cliente adicionado!")
                    st.rerun()
    with col2:
        st.subheader("Editar Cliente Existente")
        clients = fetch_clients()
        if clients:
            client_dict = {c['name']: c for c in clients}
            edit_client_name = st.selectbox("Selecione o Cliente", options=list(client_dict.keys()), key="sel_edit_client")
            c_data = client_dict[edit_client_name]
            with st.form("edit_client_form"):
                new_c_name = st.text_input("Novo Nome", value=c_data['name'])
                if st.form_submit_button("Salvar Alteração"):
                    if new_c_name:
                        update_client(c_data['id'], new_c_name)
                        st.success("Cliente atualizado!")
                        st.rerun()

# --- Aba de Integrações ---
with tabs[1]:
    st.subheader("Gerenciar Zabbix & GLPI")
    clients = fetch_clients()
    if not clients:
        st.info("Cadastre um cliente primeiro.")
    else:
        client_dict = {c['name']: c['id'] for c in clients}
        selected_client = st.selectbox("Selecione o Cliente", options=list(client_dict.keys()), key="integ_client_sel")
        client_id = client_dict[selected_client]
        
        st.markdown("### ➕ Nova Integração")
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
                    st.rerun()
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
                    st.rerun()
                    
        st.markdown("---")
        st.markdown("### ✏️ Editar Integrações Existentes")
        col_ez, col_eg = st.columns(2)
        conn = get_db()
        
        with col_ez:
            z_configs = [dict(r) for r in conn.execute("SELECT * FROM zabbix_configs WHERE client_id=?", (client_id,)).fetchall()]
            if z_configs:
                z_dict = {z['name']: z for z in z_configs}
                sel_z = st.selectbox("Editar Zabbix", options=list(z_dict.keys()))
                zd = z_dict[sel_z]
                with st.form("edit_zabbix"):
                    ez_name = st.text_input("Nome", value=zd['name'])
                    ez_url = st.text_input("URL", value=zd['url'])
                    ez_user = st.text_input("Usuário", value=zd['username'])
                    ez_pass = st.text_input("Senha (deixe em branco para não alterar)", type="password")
                    if st.form_submit_button("Atualizar Zabbix"):
                        final_pass = ez_pass if ez_pass else zd['password']
                        update_zabbix_config(zd['id'], ez_name, ez_url, ez_user, final_pass)
                        st.success("Zabbix atualizado!")
                        st.rerun()
            else:
                st.info("Sem Zabbix para este cliente.")
                
        with col_eg:
            g_configs = [dict(r) for r in conn.execute("SELECT * FROM glpi_configs WHERE client_id=?", (client_id,)).fetchall()]
            if g_configs:
                g_dict = {g['name']: g for g in g_configs}
                sel_g = st.selectbox("Editar GLPI", options=list(g_dict.keys()))
                gd = g_dict[sel_g]
                with st.form("edit_glpi"):
                    eg_name = st.text_input("Nome", value=gd['name'])
                    eg_url = st.text_input("URL", value=gd['url'])
                    eg_utoken = st.text_input("User Token", value=gd['user_token'])
                    eg_atoken = st.text_input("App Token", value=gd['app_token'])
                    if st.form_submit_button("Atualizar GLPI"):
                        update_glpi_config(gd['id'], eg_name, eg_url, eg_utoken, eg_atoken)
                        st.success("GLPI atualizado!")
                        st.rerun()
            else:
                st.info("Sem GLPI para este cliente.")

# --- Aba de Usuários ---
with tabs[2]:
    col_nu, col_eu = st.columns(2)
    with col_nu:
        st.subheader("Criar Usuário")
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
    with col_eu:
        st.subheader("Editar Usuário")
        conn = get_db()
        users_all = [dict(r) for r in conn.execute("SELECT id, username, is_admin FROM users").fetchall()]
        if users_all:
            u_all_dict = {u['username']: u for u in users_all}
            sel_u_edit = st.selectbox("Selecione o Usuário", options=list(u_all_dict.keys()))
            ud = u_all_dict[sel_u_edit]
            with st.form("edit_user_form"):
                eu_name = st.text_input("Nome de Usuário", value=ud['username'])
                eu_pass = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
                eu_admin = st.checkbox("É Administrador?", value=bool(ud['is_admin']))
                if st.form_submit_button("Atualizar Usuário"):
                    if eu_name:
                        update_user(ud['id'], eu_name, eu_pass, 1 if eu_admin else 0)
                        st.success("Usuário atualizado!")
                        st.rerun()
                        
    st.markdown("---")
    st.subheader("Permissões de Acesso (Usuários vs Clientes)")
    users_normal = [dict(r) for r in conn.execute("SELECT id, username FROM users WHERE is_admin=0").fetchall()]
    
    if users_normal and clients:
        u_dict = {u['username']: u['id'] for u in users_normal}
        c_dict = {c['name']: c['id'] for c in clients}
        
        sel_u = st.selectbox("Selecione o Usuário Comum", options=list(u_dict.keys()), key="perm_u")
        sel_c = st.selectbox("Selecione o Cliente que ele pode acessar", options=list(c_dict.keys()), key="perm_c")
        
        col_g, col_r = st.columns([1,3])
        with col_g:
            if st.button("Conceder Acesso"):
                try:
                    conn.execute("INSERT INTO user_clients (user_id, client_id) VALUES (?, ?)", (u_dict[sel_u], c_dict[sel_c]))
                    conn.commit()
                    st.success("Acesso concedido!")
                except:
                    st.info("Este usuário já tem acesso a este cliente.")
        with col_r:
            if st.button("Remover Acesso"):
                conn.execute("DELETE FROM user_clients WHERE user_id=? AND client_id=?", (u_dict[sel_u], c_dict[sel_c]))
                conn.commit()
                st.warning("Acesso removido!")
