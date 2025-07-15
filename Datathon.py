import streamlit as st
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import re
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Chave API Gemini
chave_api = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=chave_api)

# Modelo Gemini
modelo_gemini = genai.GenerativeModel("gemini-2.5-flash")

# Estados de sessão
if "formulario_enviado" not in st.session_state:
    st.session_state.formulario_enviado = False
if "curriculo_texto" not in st.session_state:
    st.session_state.curriculo_texto = ""
if "descricao_vaga" not in st.session_state:
    st.session_state.descricao_vaga = ""

st.title("Analisador de Currículo com IA 🧠📄")

# Abas
abas = st.tabs([
    "Introdução",
    "Análise Pontual",
    "Analisar currículos em massa no nosso banco de dados"
])

# Aba 1 - Introdução
with abas[0]:
    st.header("Bem-vindo ao Analisador de Currículos com IA!")
    st.markdown("""
    Esta ferramenta foi criada para facilitar a análise de currículos utilizando inteligência artificial avançada.
    
    **O que você pode fazer aqui?**
    - Analisar currículos enviados em PDF comparando com a descrição da vaga.
    - Buscar e consultar os currículos já armazenados na base de dados.
    - Analisar currículos em massa do nosso banco de dados para obter insights rápidos e eficientes.
    
    Utilize as abas acima para navegar entre as funcionalidades.
    """)

# Funções usadas na análise pontual
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

# Aba 2 - Análise Pontual
with abas[1]:
    if not st.session_state.formulario_enviado:
        with st.form("formulario_curriculo"):
            arquivo_curriculo = st.file_uploader("Envie seu currículo em PDF", type="pdf")
            st.session_state.descricao_vaga = st.text_area("Cole aqui a descrição da vaga:", placeholder="Descrição da vaga...")

            enviado = st.form_submit_button("Analisar")
            if enviado:
                if arquivo_curriculo and st.session_state.descricao_vaga.strip() != "":
                    st.info("Extraindo informações do currículo...")
                    st.session_state.curriculo_texto = extrair_texto_pdf(arquivo_curriculo)
                    st.session_state.formulario_enviado = True
                    st.experimental_rerun()
                else:
                    st.warning("Por favor, envie o currículo e a descrição da vaga.")

    if st.session_state.formulario_enviado:
        progresso = st.info("Gerando análises e pontuações...")

        similaridade = calcular_similaridade(st.session_state.curriculo_texto, st.session_state.descricao_vaga)

        col1, col2 = st.columns(2)
        with col1:
            st.write("Pontuação de similaridade (usada por alguns sistemas ATS):")
            st.subheader(f"{similaridade:.2f}")

        relatorio = gerar_relatorio(st.session_state.curriculo_texto, st.session_state.descricao_vaga)
        pontuacoes = extrair_pontuacoes(relatorio)
        media_final = sum(pontuacoes) / (5 * len(pontuacoes)) if pontuacoes else 0

        with col2:
            st.write("Pontuação média baseada na análise da IA:")
            st.subheader(f"{media_final:.2f}")

        progresso.success("Análise concluída com sucesso!")

        st.subheader("Relatório de Análise Gerado pela IA:")
        st.markdown(f"""
            <div style='text-align: left; background-color: #000000; padding: 10px; border-radius: 10px; margin: 5px 0; color: white; white-space: pre-wrap;'>
                {relatorio}
            </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="Baixar Relatório",
            data=relatorio,
            file_name="relatorio_curriculo.txt",
            icon="📥",
        )

# Aba 3 - Análise em Massa
with abas[2]:
    st.header("Analisar Currículos em Massa no Nosso Banco de Dados")
    st.markdown("""
    Nesta aba, você poderá analisar vários currículos simultaneamente, diretamente da nossa base de dados.

    **Funcionalidades previstas:**
    - Carregar ou conectar-se à base de currículos.
    - Filtrar por critérios específicos (exemplo: área, experiência, formação).
    - Gerar relatórios consolidados com análises de IA para múltiplos currículos.
    
    **Em desenvolvimento!**

    Para maiores informações ou sugestões, entre em contato com o time responsável.
    """)

    # Exemplo de botão (sem funcionalidade real ainda)
    if st.button("Iniciar análise em massa (em breve)"):
        st.info("Funcionalidade em desenvolvimento. Aguarde as próximas atualizações!")

