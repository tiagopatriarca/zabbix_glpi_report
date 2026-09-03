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
