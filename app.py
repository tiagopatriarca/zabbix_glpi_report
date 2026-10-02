import streamlit as st
from utils.database import init_db, authenticate

st.set_page_config(
    page_title="Gerador de Relatórios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Banco de Dados
init_db()

# Gerenciamento de Sessão
if "user" not in st.session_state:
    st.session_state.user = None

def do_login():
    username = st.session_state.login_user
    password = st.session_state.login_pass
    user = authenticate(username, password)
    if user:
        st.session_state.user = user
    else:
        st.error("Usuário ou senha inválidos.")

def do_logout():
    st.session_state.user = None
    st.rerun()

if not st.session_state.user:
    # Esconder sidebar na tela de login
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: none;}
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Acesso ao Sistema")
        st.markdown("Insira suas credenciais para continuar.")
        
        with st.form("login_form"):
            st.text_input("Usuário", key="login_user")
            st.text_input("Senha", type="password", key="login_pass")
            submit = st.form_submit_button("Entrar")
            if submit:
                do_login()
                if st.session_state.user:
                    st.rerun()
else:
    st.sidebar.markdown(f"**Logado como:** {st.session_state.user['username']}")
    if st.sidebar.button("Sair"):
        do_logout()
        
    st.title("📊 Painel Principal")
    st.markdown(f"""
    Bem-vindo(a) **{st.session_state.user['username']}**!
    
    Utilize o menu lateral para acessar os relatórios.
    """)
    if st.session_state.user.get('is_admin'):
        st.info("Você é um administrador. Acesse a tela de **Administração** para gerenciar Clientes, Usuários e Integrações.")


st.markdown("---")
st.subheader("🛠️ Teste de Relatório Gerencial (Modelo)")
st.markdown("Clique abaixo para gerar um PDF usando o modelo JSON fornecido para o Relatório de Gestão.")

import json
from utils.pdf_gerencial import A4GerencialPDF

json_modelo = """
{
    "relatorio": {
        "cabecalho": {
            "empresa": "TI Plus",
            "logo_url": "",
            "tipo_documento": "RELATÓRIO TÉCNICO",
            "data": "2026-08-17"
        },
        "titulo": {
            "principal": "Relatório de Gestão",
            "subtitulo": "Infraestrutura de TI e Serviços Técnicos"
        },
        "secoes": {
            "resumo_executivo": {
                "titulo": "1. Resumo Executivo",
                "conteudo": "Este espaço é destinado a um resumo claro e conciso sobre as atividades realizadas, o estado atual da infraestrutura e os principais pontos de atenção. Ele serve como uma visão geral rápida para a diretoria ou cliente.",
                "anexos": [
                    {
                        "tipo": "grafico_placeholder",
                        "descricao": "[ Inserir gráfico de desempenho, SLA ou resumo geral aqui ]"
                    }
                ]
            },
            "analise_infraestrutura": {
                "titulo": "2. Análise de Infraestrutura",
                "descricao": "Abaixo está o detalhamento do status dos principais ativos de TI gerenciados pela TI Plus. O monitoramento contínuo permite ações proativas em caso de falhas incipientes.",
                "itens": [
                    {
                        "equipamento": "Servidor Principal (SRV-01)",
                        "status": "Operacional",
                        "cor_status": "green",
                        "observacoes": "Uptime de 99.9%. Uso de CPU estável em 45%."
                    },
                    {
                        "equipamento": "Link de Internet Dedicado",
                        "status": "Atenção",
                        "cor_status": "orange",
                        "observacoes": "Picos de latência identificados durante o horário de pico."
                    },
                    {
                        "equipamento": "Storage / SAN",
                        "status": "Operacional",
                        "cor_status": "green",
                        "observacoes": "Espaço livre atual: 3.2 TB (40% de capacidade)."
                    },
                    {
                        "equipamento": "Rotinas de Backup",
                        "status": "Sucesso",
                        "cor_status": "green",
                        "observacoes": "Todos os backups diários e semanais íntegros e validados."
                    }
                ]
            },
            "acoes_realizadas": {
                "titulo": "3. Ações Realizadas",
                "descricao": "Relação das principais manutenções preventivas, corretivas e atualizações aplicadas durante o período de abrangência deste relatório:",
                "lista_acoes": [
                    "Atualização crítica de segurança no firewall de borda.",
                    "Revisão e limpeza física dos switches no rack de telecomunicações.",
                    "Auditoria de permissões de usuários no Active Directory.",
                    "Instalação de patches do Windows Server em ambiente de homologação."
                ]
            },
            "recomendacoes": {
                "titulo": "4. Recomendações e Próximos Passos",
                "descricao": "Com base na análise de infraestrutura, recomendamos as seguintes ações para o próximo ciclo, visando a melhoria da performance, segurança e mitigação de riscos:",
                "lista_recomendacoes": [
                    {
                        "acao": "Upgrade de Link",
                        "detalhe": "Avaliar a contratação de um link de contingência para evitar lentidão nos horários de pico."
                    },
                    {
                        "acao": "Políticas de Senha",
                        "detalhe": "Implementar exigência de Múltiplos Fatores de Autenticação (MFA) para acessos VPN."
                    },
                    {
                        "acao": "Treinamento",
                        "detalhe": "Conduzir uma campanha de conscientização contra phishing para os colaboradores."
                    }
                ]
            }
        },
        "assinatura": {
            "equipe": "Equipe TI Plus",
            "departamento": "Gestão de Infraestrutura e Suporte"
        },
        "rodape": {
            "texto": "TI Plus - Gestão de infraestrutura",
            "exibir_paginacao": true
        }
    }
}
"""

if st.button("Gerar Teste - PDF Gerencial"):
    try:
        dados = json.loads(json_modelo)
        pdf = A4GerencialPDF(dados)
        pdf.render_report()
        pdf_bytes = bytes(pdf.output())
        
        st.download_button(
            label="📥 Baixar PDF Modelo Gerencial",
            data=pdf_bytes,
            file_name="Relatorio_Gerencial_Modelo.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Erro ao gerar o PDF: {e}")
