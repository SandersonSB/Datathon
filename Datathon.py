pip install pdfminer.six
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

# Carrega a chave da API do Gemini
chave_api = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=chave_api)

# Inicializa o modelo do Gemini
modelo_gemini = genai.GenerativeModel("gemini-2.5-flash")

# Inicializa estados de sessão
if "formulario_enviado" not in st.session_state:
    st.session_state.formulario_enviado = False
if "curriculo_texto" not in st.session_state:
    st.session_state.curriculo_texto = ""
if "descricao_vaga" not in st.session_state:
    st.session_state.descricao_vaga = ""

# Título do app
st.title("Analisador de Currículo com IA 🧠📄")

# Função para extrair texto de um PDF
def extrair_texto_pdf(arquivo_pdf):
    try:
        return extract_text(arquivo_pdf)
    except Exception as e:
        st.error(f"Erro ao extrair texto do PDF: {str(e)}")
        return ""

# Função para calcular similaridade usando BERT
def calcular_similaridade(texto1, texto2):
    modelo_bert = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    emb1 = modelo_bert.encode([texto1])
    emb2 = modelo_bert.encode([texto2])
    return cosine_similarity(emb1, emb2)[0][0]

# Função para gerar o relatório com o Gemini
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

# Função para extrair as pontuações x/5 do texto
def extrair_pontuacoes(texto):
    padrao = r'(\d+(?:\.\d+)?)/5'
    correspondencias = re.findall(padrao, texto)
    return [float(p) for p in correspondencias]

# Exibir o formulário se ainda não foi enviado
if not st.session_state.formulario_enviado:
    with st.form("formulario_curriculo"):
        arquivo_curriculo = st.file_uploader("Envie seu currículo em PDF", type="pdf")
        st.session_state.descricao_vaga = st.text_area("Cole aqui a descrição da vaga:", placeholder="Descrição da vaga...")

        enviado = st.form_submit_button("Analisar")
        if enviado:
            if arquivo_curriculo and st.session_state.descricao_vaga:
                st.info("Extraindo informações do currículo...")
                st.session_state.curriculo_texto = extrair_texto_pdf(arquivo_curriculo)
                st.session_state.formulario_enviado = True
                st.rerun()
            else:
                st.warning("Por favor, envie o currículo e a descrição da vaga.")

# Exibir os resultados
if st.session_state.formulario_enviado:
    progresso = st.info("Gerando análises e pontuações...")

    # Similaridade entre currículo e descrição
    similaridade = calcular_similaridade(st.session_state.curriculo_texto, st.session_state.descricao_vaga)

    col1, col2 = st.columns(2, border=True)
    with col1:
        st.write("Pontuação de similaridade (usada por alguns sistemas ATS):")
        st.subheader(f"{similaridade:.2f}")

    # Chamada da API Gemini para análise detalhada
    relatorio = gerar_relatorio(st.session_state.curriculo_texto, st.session_state.descricao_vaga)

    # Cálculo da média das notas
    pontuacoes = extrair_pontuacoes(relatorio)
    media_final = sum(pontuacoes) / (5 * len(pontuacoes)) if pontuacoes else 0

    with col2:
        st.write("Pontuação média baseada na análise da IA:")
        st.subheader(f"{media_final:.2f}")

    progresso.success("Análise concluída com sucesso!")

    # Exibir relatório
    st.subheader("Relatório de Análise Gerado pela IA:")
    st.markdown(f"""
        <div style='text-align: left; background-color: #000000; padding: 10px; border-radius: 10px; margin: 5px 0; color: white;'>
            {relatorio}
        </div>
    """, unsafe_allow_html=True)

    # Botão para download do relatório
    st.download_button(
        label="Baixar Relatório",
        data=relatorio,
        file_name="relatorio_curriculo.txt",
        icon="📥",
    )

