import streamlit as st     
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import re
from dotenv import load_dotenv
import os
from carregar_frame import carregar_dados_brutos, montar_df_resumido

# Carrega as variáveis de ambiente
load_dotenv()

# Configura a chave da API Gemini
chave_api = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=chave_api)

# Modelo Gemini
modelo_gemini = genai.GenerativeModel("gemini-2.5-flash")

# Inicializa estado da sessão
if "iniciou_aplicacao" not in st.session_state:
    st.session_state.iniciou_aplicacao = False
if "formulario_enviado" not in st.session_state:
    st.session_state.formulario_enviado = False
if "curriculo_texto" not in st.session_state:
    st.session_state.curriculo_texto = ""
if "descricao_vaga" not in st.session_state:
    st.session_state.descricao_vaga = ""

# ----------------------------
# CABEÇALHO / ABERTURA DO SITE
# ----------------------------
st.markdown("""
    <div style='text-align: center; padding: 30px 0 10px 0;'>
        <img src='https://raw.githubusercontent.com/SandersonSB/Datathon/main/IA_Gemini_3x0r2u3x0r2u3x0r.png' width='240'/>
        <h1 style='font-size: 42px; color:  #FFA500; margin-bottom: 10px;'>IA na Decision</h1>
        <h4 style='color: #FF8C00; font-weight: normal;'>Análise inteligente de currículos com apoio de inteligência artificial</h4>
        <hr style='border: 1px solid #ddd; margin-top: 20px;'/>
    </div>
""", unsafe_allow_html=True)

# ----------------------------
# TELA DE INÍCIO
# ----------------------------
if not st.session_state.iniciou_aplicacao:
    st.markdown("""
    ### 👋 Bem-vindo à plataforma IA na Decision

    Essa plataforma usa **inteligência artificial** para comparar currículos com descrições de vagas, gerar relatórios automáticos e oferecer insights personalizados.

    Clique no botão abaixo para começar.
    """)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Iniciar", use_container_width=True):
            st.session_state.iniciou_aplicacao = True

else:
    # ----------------------------
    # ABAS DE FUNCIONALIDADES
    # ----------------------------
    abas = st.tabs([
        "Introdução",
        "Análise Rápida",
        "Banco de Currículos"
    ])

    # ----------------------------
    # ABA 1 - INTRODUÇÃO
    # ----------------------------
    with abas[0]:
        st.header("Bem-vindo ao IA na Decision!")
        st.markdown("""
        Esta plataforma foi criada para facilitar a triagem e análise de currículos usando tecnologias modernas de IA.

        **Principais funcionalidades:**
        - 🔍 Análise individual de currículos com comparação à vaga.
        - 🧠 Geração de relatórios com pontuação e sugestões.
        - 📁 Análise em massa de currículos já armazenados.

        Use as abas acima para começar!
        """)

    # ----------------------------
    # FUNÇÕES AUXILIARES
    # ----------------------------
    def extrair_texto_pdf(arquivo_pdf):
        try:
            return extract_text(arquivo_pdf)
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {str(e)}")
            return ""

    def calcular_similaridade(texto1, texto2):
        modelo_bert = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        emb1 = modelo_bert.encode([texto1])
        emb2 = modelo_bert.encode([texto2])
        return cosine_similarity(emb1, emb2)[0][0]

    def gerar_relatorio(curriculo, descricao):
        prompt = f"""
# Contexto:
Você é um Analisador de Currículo com IA. Será fornecido um currículo e uma descrição de vaga.

# Instruções:
- Avalie o currículo com base nas habilidades, experiências e aderência à vaga.
- Para cada ponto-chave, forneça uma nota de 0 a 5, um emoji (✅, ❌, ⚠️) e uma explicação.
- Finalize com a seção "Sugestões para melhorar seu currículo".

# Currículo do Candidato:
{curriculo}

# Descrição da Vaga:
{descricao}
"""
        try:
            resposta = modelo_gemini.generate_content(prompt)
            return resposta.text
        except Exception as e:
            return f"Erro ao chamar a API do Gemini: {e}"

    def extrair_pontuacoes(texto):
        padrao = r'(\d+(?:\.\d+)?)/5'
        correspondencias = re.findall(padrao, texto)
        return [float(p) for p in correspondencias]

    # ----------------------------
    # ABA 2 - ANÁLISE RÁPIDA
    # ----------------------------
    with abas[1]:
        if not st.session_state.formulario_enviado:
            with st.form("formulario_curriculo"):
                arquivo_curriculo = st.file_uploader("📄 Envie seu currículo em PDF", type="pdf")
                descricao_input = st.text_area("📝 Cole aqui a descrição da vaga:", placeholder="Descrição da vaga...")

                enviado = st.form_submit_button("Analisar")
                if enviado:
                    if arquivo_curriculo and descricao_input.strip():
                        st.info("Extraindo informações do currículo...")
                        st.session_state.curriculo_texto = extrair_texto_pdf(arquivo_curriculo)
                        st.session_state.descricao_vaga = descricao_input
                        st.session_state.formulario_enviado = True
                    else:
                        st.warning("Por favor, envie o currículo e a descrição da vaga.")

        if st.session_state.formulario_enviado:
            progresso = st.info("Gerando análises e pontuações...")

            similaridade = calcular_similaridade(st.session_state.curriculo_texto, st.session_state.descricao_vaga)

            col1, col2 = st.columns(2)
            with col1:
                st.write("🎯 Pontuação de similaridade (sistemas ATS):")
                st.subheader(f"{similaridade:.2f}")

            relatorio = gerar_relatorio(st.session_state.curriculo_texto, st.session_state.descricao_vaga)
            pontuacoes = extrair_pontuacoes(relatorio)
            media_final = sum(pontuacoes) / (5 * len(pontuacoes)) if pontuacoes else 0

            with col2:
                st.write("📊 Pontuação média da IA:")
                st.subheader(f"{media_final:.2f}")

            progresso.success("✅ Análise concluída com sucesso!")

            st.subheader("📃 Relatório da IA:")
            st.markdown(f"""
                <div style='text-align: left; background-color: #000000; padding: 10px; border-radius: 10px; margin: 5px 0; color: white; white-space: pre-wrap;'>
                    {relatorio}
                </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📥 Baixar Relatório",
                data=relatorio,
                file_name="relatorio_curriculo.txt"
            )

    # ----------------------------
    # ABA 3 - BANCO DE CURRÍCULOS
    # ----------------------------
    with abas[2]:
        st.header("📁 Banco de Currículos")

        st.markdown("""
        Visualize os candidatos e currículos disponíveis na base.
        Use os filtros abaixo antes de carregar os dados para evitar lentidão.
        """)

        @st.cache_data
        def carregar_base():
            return carregar_dados_brutos()

        df_candidatos, df_applicants, df_vagas = carregar_base()

        with st.form("filtros_candidatos"):
            col1, col2 = st.columns(2)

            with col1:
                vagas_disp = df_candidatos['titulo_vaga'].dropna().unique().tolist()
                vaga_selecionada = st.selectbox("Filtrar por vaga", ["Todas"] + sorted(vagas_disp))

            with col2:
                recrutadores = df_candidatos['recrutador'].dropna().unique().tolist()
                recrutador_sel = st.selectbox("Filtrar por recrutador", ["Todos"] + sorted(recrutadores))

            aplicar = st.form_submit_button("🔍 Aplicar Filtros")

        if aplicar:
            if vaga_selecionada == "Todas" and recrutador_sel == "Todos":
                st.warning("⚠️ Por favor, selecione pelo menos um filtro para visualizar os dados.")
            else:
                if vaga_selecionada != "Todas":
                    df_candidatos = df_candidatos[df_candidatos["titulo_vaga"] == vaga_selecionada]

                if recrutador_sel != "Todos":
                    df_candidatos = df_candidatos[df_candidatos["recrutador"] == recrutador_sel]

                with st.spinner("🔄 Processando base filtrada..."):
                    df_final = montar_df_resumido(df_candidatos, df_applicants, df_vagas)

                st.success(f"✅ {len(df_final)} registros encontrados após o filtro.")
                st.dataframe(df_final, use_container_width=True)

                csv = df_final.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Baixar resultados em CSV",
                    data=csv,
                    file_name="resultados_filtrados.csv",
                    mime="text/csv"
                )
        else:
            st.info("Aplique filtros e clique no botão para carregar os dados.")

# ----------------------------
# RODAPÉ INSTITUCIONAL
# ----------------------------
st.markdown("""
<hr/>
<div style='text-align: center; font-size: 14px; color: #95a5a6; padding: 10px 0;'>
    Desenvolvido por <strong>Decision AI</strong> • © 2025 • Todos os direitos reservados
</div>
""", unsafe_allow_html=True)
