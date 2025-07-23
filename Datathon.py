import streamlit as st  # Biblioteca para criar app web simples e interativo
from pdfminer.high_level import extract_text  # Para ler texto dentro de arquivos PDF
from sentence_transformers import SentenceTransformer  # Para transformar texto em números (embeddings)
from sklearn.metrics.pairwise import cosine_similarity  # Para calcular similaridade entre textos
import google.generativeai as genai  # Para usar IA Gemini do Google
import re  # Para encontrar padrões em texto
from dotenv import load_dotenv  # Para carregar variáveis secretas do sistema
import os  # Para acessar essas variáveis
from carregar_frame import carregar_dados_brutos, montar_df_resumido  # Funções customizadas para carregar dados

# Carrega variáveis de ambiente (ex: chave da API)
load_dotenv()

# Pega a chave da API Gemini e configura a biblioteca para usar
chave_api = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=chave_api)

# Define o modelo Gemini que será usado para gerar relatórios inteligentes
modelo_gemini = genai.GenerativeModel("gemini-2.5-flash")

# Inicializa variáveis que vão guardar o estado do app para saber o que o usuário fez
if "iniciou_aplicacao" not in st.session_state:
    st.session_state.iniciou_aplicacao = False
if "formulario_enviado" not in st.session_state:
    st.session_state.formulario_enviado = False
if "curriculo_texto" not in st.session_state:
    st.session_state.curriculo_texto = ""
if "descricao_vaga" not in st.session_state:
    st.session_state.descricao_vaga = ""

# Exibe o cabeçalho com logo e título centralizado
st.markdown("""
    <div style='text-align: center; padding: 30px 0 10px 0;'>
        <img src='https://raw.githubusercontent.com/SandersonSB/Datathon/main/IA_Gemini_3x0r2u3x0r2u3x0r.png' width='240'/>
        <h1 style='font-size: 42px; color:  #FFA500; margin-bottom: 10px;'>IA na Decision</h1>
        <h4 style='color: #FF8C00;'>Análise inteligente de currículos com apoio de inteligência artificial</h4>
        <hr style='border: 1px solid #ddd; margin-top: 20px;'/>
    </div>
""", unsafe_allow_html=True)

# Tela inicial de boas-vindas e botão para começar
if not st.session_state.iniciou_aplicacao:
    st.markdown("""
    ### 👋 Bem-vindo à plataforma IA na Decision

    Essa plataforma usa **inteligência artificial** para comparar currículos com descrições de vagas, gerar relatórios e dar insights.

    Clique no botão abaixo para começar.
    """)
    if st.button("🚀 Iniciar"):
        st.session_state.iniciou_aplicacao = True

else:
    # Cria as abas (menu) para as funcionalidades do app
    abas = st.tabs(["Introdução", "Análise Rápida", "Banco de Currículos"])

    # Aba 1: Introdução com explicação simples do que o app faz
    with abas[0]:
        st.header("Bem-vindo ao IA na Decision!")
        st.markdown("""
        Esta plataforma ajuda a analisar currículos usando inteligência artificial.

        Funcionalidades:
        - 🔍 Análise rápida e individual de currículos
        - 🧠 Relatórios automáticos com notas e sugestões
        - 📁 Visualização e filtros para muitos currículos armazenados
        """)

    # Função para ler o texto de um arquivo PDF (currículo)
    def extrair_texto_pdf(arquivo_pdf):
        try:
            return extract_text(arquivo_pdf)
        except Exception as e:
            st.error(f"Erro ao extrair texto do PDF: {str(e)}")
            return ""

    # Função para calcular quão parecido dois textos são, usando IA
    def calcular_similaridade(texto1, texto2):
        modelo_bert = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        emb1 = modelo_bert.encode([texto1])
        emb2 = modelo_bert.encode([texto2])
        return cosine_similarity(emb1, emb2)[0][0]

    # Função que usa a IA Gemini para gerar um relatório inteligente do currículo versus a vaga
    def gerar_relatorio(curriculo, descricao):
        prompt = f"""
# Contexto:
Você é um Analisador de Currículo com IA.

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

    # Função para extrair as notas que aparecem no relatório gerado (ex: "4.5/5")
    def extrair_pontuacoes(texto):
        padrao = r'(\d+(?:\.\d+)?)/5'
        correspondencias = re.findall(padrao, texto)
        return [float(p) for p in correspondencias]

    # Aba 2: Onde o usuário envia currículo e descrição da vaga para análise rápida
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

            # Calcula a similaridade entre currículo e vaga
            similaridade = calcular_similaridade(st.session_state.curriculo_texto, st.session_state.descricao_vaga)

            col1, col2 = st.columns(2)
            with col1:
                st.write("🎯 Pontuação de similaridade (sistemas ATS):")
                st.subheader(f"{similaridade:.2f}")

            # Gera o relatório pela IA
            relatorio = gerar_relatorio(st.session_state.curriculo_texto, st.session_state.descricao_vaga)
            pontuacoes = extrair_pontuacoes(relatorio)
            media_final = sum(pontuacoes) / (5 * len(pontuacoes)) if pontuacoes else 0

            with col2:
                st.write("📊 Pontuação média da IA:")
                st.subheader(f"{media_final:.2f}")

            progresso.success("✅ Análise concluída com sucesso!")

            # Mostra o relatório formatado
            st.subheader("📃 Relatório da IA:")
            st.markdown(f"""
                <div style='background-color: #000; padding: 10px; border-radius: 10px; color: white; white-space: pre-wrap;'>
                    {relatorio}
                </div>
            """, unsafe_allow_html=True)

            # Botão para baixar o relatório
            st.download_button(
                label="📥 Baixar Relatório",
                data=relatorio,
                file_name="relatorio_curriculo.txt"
            )

# Aba 3: Visualizar e filtrar vários currículos já armazenados
with abas[2]:
    st.header("📁 Banco de Currículos")
    st.markdown("Visualize candidatos e use filtros para evitar lentidão.")

    @st.cache_data
    def carregar_base():
        return carregar_dados_brutos()

    df_resumido = carregar_base()

    with st.form("filtros_candidatos"):
        col1, col2 = st.columns(2)
        with col1:
            vagas_disp = df_resumido['titulo_vaga'].dropna().unique().tolist()
            vaga_selecionada = st.selectbox("Filtrar por vaga", ["Todas"] + sorted(vagas_disp))
        with col2:
            recrutadores = df_resumido['recrutador'].dropna().unique().tolist()
            recrutador_sel = st.selectbox("Filtrar por recrutador", ["Todos"] + sorted(recrutadores))
        aplicar = st.form_submit_button("🔍 Aplicar Filtros")

    if aplicar:
        if vaga_selecionada == "Todas" and recrutador_sel == "Todos":
            st.warning("⚠️ Por favor, selecione pelo menos um filtro para visualizar os dados.")
        else:
            if vaga_selecionada != "Todas":
                df_resumido = df_resumido[df_resumido["titulo_vaga"] == vaga_selecionada]
            if recrutador_sel != "Todos":
                df_resumido = df_resumido[df_resumido["recrutador"] == recrutador_sel]

            df_final = df_resumido.copy()
            st.success(f"✅ {len(df_final)} registros encontrados.")

            st.subheader("🎯 Similaridade (BERT) e Nota da IA Gemini")

            @st.cache_resource
            def carregar_modelo_bert():
                return SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

            modelo_bert = carregar_modelo_bert()

            def gerar_nota_gemini(cv_name, cv_text, job_description):
                prompt = (
                    f"Você é um avaliador de currículos.\n\n"
                    f"Avalie o quanto o CV abaixo se encaixa na vaga descrita. "
                    f"Baseie-se apenas nas informações fornecidas.\n\n"
                    f"Descrição da vaga:\n{job_description}\n\n"
                    f"Currículo de {cv_name}:\n{cv_text}\n\n"
                    f"Com base nessas informações, dê uma nota de similaridade entre 0.0 e 1.0 "
                    f"(sendo 1.0 totalmente compatível e 0.0 nada compatível).\n"
                    f"**Retorne apenas a nota numérica**, sem explicações nem texto adicional."
                )
                try:
                    resposta = modelo_gemini.generate_content(prompt)
                    texto = resposta.text.strip()
                    match = re.search(r"(\d\.\d+|\d)", texto)
                    if match:
                        return min(1.0, max(0.0, float(match.group(1))))
                    else:
                        return None
                except Exception as e:
                    print(f"Erro ao gerar nota do Gemini: {e}")
                    return None

            resultados_similaridade = []
            notas_gemini = []

            progresso = st.progress(0, text="🔄 Calculando similaridade e nota da IA Gemini...")

            for i, (_, row) in enumerate(df_final.iterrows()):
                cv_text = str(row.get("cv_pt", ""))
                job_desc = str(row.get("perfil_vaga__principais_atividades", ""))
                cv_name = str(row.get("nome", ""))

                if cv_text.strip() and job_desc.strip():
                    emb1 = modelo_bert.encode([cv_text])
                    emb2 = modelo_bert.encode([job_desc])
                    score = cosine_similarity(emb1, emb2)[0][0]
                    resultados_similaridade.append(round(score, 4))

                    nota = gerar_nota_gemini(cv_name, cv_text, job_desc)
                    notas_gemini.append(round(nota, 4) if nota is not None else None)
                else:
                    resultados_similaridade.append(None)
                    notas_gemini.append(None)

                progresso.progress((i + 1) / len(df_final), text=f"🔄 Processando {i+1}/{len(df_final)}")

            progresso.empty()

            df_final["similaridade_cv_vaga"] = resultados_similaridade
            df_final["nota_gemini_cv_vaga"] = notas_gemini
            df_final2 = df_final.sort_values(by="similaridade_cv_vaga", ascending=False)

            st.dataframe(
                df_final2[[
                    "nome", "codigo", "titulo_vaga", "recrutador",
                    "similaridade_cv_vaga", "nota_gemini_cv_vaga"
                ]],
                use_container_width=True
            )

            csv = df_final2.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar resultados em CSV",
                data=csv,
                file_name="resultados_filtrados.csv",
                mime="text/csv"
            )
    else:
        st.info("Aplique filtros e clique no botão para carregar os dados.")


# Rodapé institucional simples no final da página
st.markdown("""
<hr/>
<div style='text-align: center; font-size: 14px; color: #95a5a6; padding: 10px 0;'>
    Desenvolvido por <strong>Decision AI</strong> • © 2025 • Todos os direitos reservados
</div>
""", unsafe_allow_html=True)
