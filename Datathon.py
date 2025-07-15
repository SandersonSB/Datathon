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
            # Verifica se ambos estão como "Todos"
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

                # Exportação
                csv = df_final.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Baixar resultados em CSV",
                    data=csv,
                    file_name="resultados_filtrados.csv",
                    mime="text/csv"
                )
        else:
            st.info("Aplique filtros e clique no botão para carregar os dados.")
