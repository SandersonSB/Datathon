# carregar_frame.py

import gdown
import json
import pandas as pd
import ijson

def baixar_arquivos():
    file_ids = {
        'prospects': '1gggiyvLEP68yqZR20zji7d17tzUfBnib',
        'applicants': '169owq4_yYCwbvMaep1QbC9B59KrNcRBn',
        'vagas': '1lJTVnG9WOBpqQUsDEu9umllp3BhLR1TA'
    }

    outputs = {
        'prospects': 'prospects.json',
        'applicants': 'applicants.json',
        'vagas': 'vagas.json'
    }

    for key in file_ids:
        gdown.download(f"https://drive.google.com/uc?id={file_ids[key]}", outputs[key], quiet=False)

def carregar_dados_brutos():
    baixar_arquivos()

    # === PROSPECTS ===
    with open('prospects.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)

    registros = []
    for codigo_vaga, info_vaga in dados.items():
        titulo = info_vaga.get('titulo', '')
        modalidade = info_vaga.get('modalidade', '')
        for prospect in info_vaga.get('prospects', []):
            prospect['codigo_vaga'] = codigo_vaga
            prospect['titulo_vaga'] = titulo
            prospect['modalidade'] = modalidade
            registros.append(prospect)

    df_candidatos = pd.DataFrame(registros)

    # === APPLICANTS ===
    registros_applicants = []
    with open('applicants.json', 'r', encoding='utf-8') as f:
        parser = ijson.kvitems(f, '')
        for codigo_profissional, dados in parser:
            infos_basicas = dados.get('infos_basicas', {})
            informacoes_profissionais = dados.get('informacoes_profissionais', {})
            formacao_e_idiomas = dados.get('formacao_e_idiomas', {})
            cv_pt = dados.get('cv_pt', '')

            registro = {
                'codigo_profissional': codigo_profissional,
                'nome': infos_basicas.get('nome'),
                'email': infos_basicas.get('email'),
                'telefone': infos_basicas.get('telefone'),
                'titulo_profissional': informacoes_profissionais.get('titulo_profissional'),
                'area_atuacao': informacoes_profissionais.get('area_atuacao'),
                'nivel_academico': formacao_e_idiomas.get('nivel_academico'),
                'nivel_ingles': formacao_e_idiomas.get('nivel_ingles'),
                'nivel_espanhol': formacao_e_idiomas.get('nivel_espanhol'),
                'cv_pt': cv_pt
            }

            registros_applicants.append(registro)

    df_applicants = pd.DataFrame(registros_applicants)

    # === VAGAS ===
    with open('vagas.json', 'r', encoding='utf-8') as f:
        vagas_dict = json.load(f)

    vagas_lista = []
    for id_vaga, conteudo in vagas_dict.items():
        vaga_flat = {'id_vaga': id_vaga}
        for secao, dados_secao in conteudo.items():
            if isinstance(dados_secao, dict):
                for chave, valor in dados_secao.items():
                    coluna = f'{secao}__{chave}'.strip()
                    vaga_flat[coluna] = valor
            else:
                vaga_flat[secao] = dados_secao
        vagas_lista.append(vaga_flat)

    df_vagas = pd.DataFrame(vagas_lista)

    return df_candidatos, df_applicants, df_vagas


def montar_df_resumido(df_candidatos, df_applicants, df_vagas):
    # MERGES
    df_candidatos['codigo_profissional'] = df_candidatos['codigo'].astype(str)
    df_applicants['codigo_profissional'] = df_applicants['codigo_profissional'].astype(str)
    df_principal = pd.merge(df_candidatos, df_applicants, on='codigo_profissional', how='left')

    df_principal['codigo_vaga'] = df_principal['codigo_vaga'].astype(str)
    df_vagas['id_vaga'] = df_vagas['id_vaga'].astype(str)
    df_principal = pd.merge(df_principal, df_vagas, left_on='codigo_vaga', right_on='id_vaga', how='left')

    # Renomear 'nome_x' para 'nome' para evitar erro no app principal
    if 'nome_x' in df_principal.columns:
        df_principal = df_principal.rename(columns={'nome_x': 'nome'})

    # RESUMO
    colunas_resumo = [
        'nome', 'codigo', 'situacao_candidado', 'data_candidatura', 'recrutador',
        'codigo_vaga', 'titulo_vaga', 'email', 'cv_pt', 'id_vaga',
        'perfil_vaga__principais_atividades',
        'perfil_vaga__competencia_tecnicas_e_comportamentais',
        'perfil_vaga__demais_observacoes',
        'perfil_vaga__viagens_requeridas',
        'perfil_vaga__equipamentos_necessarios'
    ]

    return df_principal[colunas_resumo].copy()
