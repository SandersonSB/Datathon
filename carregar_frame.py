# carregar_frame.py

import gdown
import json
import pandas as pd
import ijson
import os
import gc

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
        if not os.path.exists(outputs[key]):
            gdown.download(f"https://drive.google.com/uc?id={file_ids[key]}", outputs[key], quiet=False)

def carregar_prospects_streaming():
    registros = []
    with open('prospects.json', 'r', encoding='utf-8') as f:
        parser = ijson.kvitems(f, '')
        for codigo_vaga, info_vaga in parser:
            titulo = info_vaga.get('titulo', '')
            modalidade = info_vaga.get('modalidade', '')
            for prospect in info_vaga.get('prospects', []):
                prospect['codigo_vaga'] = codigo_vaga
                prospect['titulo_vaga'] = titulo
                prospect['modalidade'] = modalidade
                registros.append(prospect)
    return pd.DataFrame(registros)

def carregar_applicants_streaming():
    registros = []
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
            registros.append(registro)
    return pd.DataFrame(registros)

def carregar_vagas():
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

    return pd.DataFrame(vagas_lista)

def montar_df_resumido(df_candidatos, df_applicants, df_vagas):
    df_candidatos['codigo_profissional'] = df_candidatos['codigo'].astype(str)
    df_applicants['codigo_profissional'] = df_applicants['codigo_profissional'].astype(str)
    df = pd.merge(df_candidatos, df_applicants, on='codigo_profissional', how='left')

    df['codigo_vaga'] = df['codigo_vaga'].astype(str)
    df_vagas['id_vaga'] = df_vagas['id_vaga'].astype(str)
    df = pd.merge(df, df_vagas, left_on='codigo_vaga', right_on='id_vaga', how='left')

    if 'nome_x' in df.columns:
        df = df.rename(columns={'nome_x': 'nome'})

    colunas_resumo = [
        'nome', 'codigo', 'situacao_candidado', 'data_candidatura', 'recrutador',
        'codigo_vaga', 'titulo_vaga', 'email', 'cv_pt', 'id_vaga',
        'perfil_vaga__principais_atividades',
        'perfil_vaga__competencia_tecnicas_e_comportamentais',
        'perfil_vaga__demais_observacoes',
        'perfil_vaga__viagens_requeridas',
        'perfil_vaga__equipamentos_necessarios'
    ]

    return df[colunas_resumo].copy()

def carregar_dados_brutos():
    if os.path.exists("dados_resumidos.parquet"):
        return pd.read_parquet("dados_resumidos.parquet")

    baixar_arquivos()

    df_candidatos = carregar_prospects_streaming()
    df_applicants = carregar_applicants_streaming()
    df_vagas = carregar_vagas()

    df_resumido = montar_df_resumido(df_candidatos, df_applicants, df_vagas)

    # Libera memória
    del df_candidatos, df_applicants, df_vagas
    gc.collect()

    df_resumido.to_parquet("dados_resumidos.parquet")

    return df_resumido
