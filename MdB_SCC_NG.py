import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from io import StringIO

# Configuration de la page
st.set_page_config(
    page_title="Screener d'Actions Avancé",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_screener_config():
    """Charge la configuration des setups de screening"""
    url = "https://gist.githubusercontent.com/traderLaval/9eaa7bc9f0aac2b276f59594e00f9207/raw/screener_setups.json"
    try:
        response = requests.get(url)
        return json.loads(response.text)
    except:
        return {
            "setups": {
                "setup01": {"name": "MM200_Cross_Up", "output_file": "mm200_cross_up.csv", "description": "Close a franchi la MM200 jours à la hausse"},
                "setup02": {"name": "MM200_Cross_Up_MACD_Up", "output_file": "mm200_cross_up_macd_up.csv", "description": "MM200 + MACD haussier"},
                "setup03": {"name": "MM200_Cross_Up_WMA12_Up", "output_file": "mm200_cross_up_wma12_up.csv", "description": "MM200 + WMA12 ascendante"},
                "setup04": {"name": "Weekly_SuperTrend_Cross", "output_file": "weekly_supertrend_cross.csv", "description": "SuperTrend hebdomadaire franchi"},
                "setup05": {"name": "Above_Weekly_Below_Daily_SuperTrend", "output_file": "above_weekly_below_daily_supertrend.csv", "description": "Entre SuperTrend hebdo et daily"},
                "setup09": {"name": "new_high_50_days", "output_file": "new_high_50_days.csv", "description": "Nouveau plus haut 50 jours"},
                "setup10": {"name": "new_high_100_days", "output_file": "new_high_100_days.csv", "description": "Nouveau plus haut 100 jours"},
                "setup11": {"name": "new_high_200_days", "output_file": "new_high_200_days.csv", "description": "Nouveau plus haut 200 jours"}
            }
        }


@st.cache_data
def load_screener_results(setup_name, output_file):
    """Charge les résultats d'un screener spécifique"""
    base_url = "https://gist.github.com/traderLaval/e4e5eee8d610dcdcaf716a52624334bb/raw/"
    try:
        response = requests.get(base_url + output_file)
        if response.status_code == 200:
            # Lire le CSV avec les bons paramètres
            screener_df = pd.read_csv(
                StringIO(response.text),
                sep=';',
                comment='#',
                encoding='utf-8',
                on_bad_lines='warn'
            )

            # Debug : afficher les colonnes disponibles
            st.sidebar.write(
                f"Colonnes dans {output_file}: {screener_df.columns.tolist()}")

            # Retourner la liste des noms
            if 'Name' in screener_df.columns:
                names = screener_df['Name'].dropna().tolist()
                return names
            elif 'name' in screener_df.columns:
                names = screener_df['name'].dropna().tolist()
                return names
            else:
                # Si pas de colonne Name, essayer d'autres possibilités
                st.sidebar.warning(
                    f"Colonnes disponibles: {screener_df.columns.tolist()}")
                return []
    except Exception as e:
        st.sidebar.error(f"Erreur lors du chargement de {output_file}: {e}")
    return []


@st.cache_data
def load_stocks_data():
    """Charge les données des actions"""
    url = "https://gist.githubusercontent.com/traderLaval/9eaa7bc9f0aac2b276f59594e00f9207/raw/zb_style_invest_sum.csv"
    try:
        response = requests.get(url)
        df = pd.read_csv(StringIO(response.text), sep=';')

        # Nettoyer les données
        df = df.dropna(subset=['Name', 'Symbol'])

        # S'assurer que Name ne contient qu'une seule valeur
        df['Name'] = df['Name'].astype(str).str.strip()

        # Gestion améliorée des colonnes PEA
        for col in ['PEA', 'PEA-PME']:
            if col in df.columns:
                df[col] = df[col].fillna('False')
                df[col] = df[col].astype(str).str.strip().str.lower() == 'true'

        # Remplacer les 'X' par True dans les colonnes de critères (styles d'investissement)
        criteria_columns = ['MBagger', 'ROE', 'grow', 'growR',
                            'mom', 'qual', 'qualR', 'small', 'trend', 'value']
        for col in criteria_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
                df[col] = df[col].astype(str).str.strip() == 'X'

        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()


def prepare_display_dataframe(df):
    """Prépare le DataFrame pour l'affichage avec les liens"""
    # Colonnes de base toujours affichées
    base_columns = ['Market', 'Name', 'Symbol', 'PEA', 'PEA-PME']

    # Ajouter TOUTES les colonnes de styles d'investissement
    style_columns = ['MBagger', 'ROE', 'grow', 'growR',
                     'mom', 'qual', 'qualR', 'small', 'trend', 'value']

    # Ajouter les colonnes de secteur et industrie
    sector_columns = ['Sector', 'Industry']

    # Construire la liste complète des colonnes à afficher
    all_columns = base_columns + style_columns + sector_columns

    # Filtrer les colonnes qui existent dans le DataFrame
    display_columns = [col for col in all_columns if col in df.columns]

    # Créer le DataFrame d'affichage
    display_df = df[display_columns].copy()

    # Créer la colonne graphique en première position
    if 'ZB URL' in df.columns:
        def create_chart_icon(url):
            if pd.isna(url) or url == '':
                return "➖"
            return "📊"

        # Insérer la colonne graphique en première position
        display_df.insert(0, '📊', df['ZB URL'].apply(create_chart_icon))

    # Formatage des colonnes booléennes (PEA et styles d'investissement)
    bool_columns = display_df.select_dtypes(include=['bool']).columns
    for col in bool_columns:
        display_df[col] = display_df[col].map(
            {True: '✅', False: '❌', pd.NA: '➖'})

    return display_df


def create_summary_charts(df):
    """Crée des graphiques de synthèse"""
    col1, col2 = st.columns(2)

    with col1:
        market_counts = df['Market'].value_counts().head(10)
        fig_market = px.bar(
            x=market_counts.values,
            y=market_counts.index,
            orientation='h',
            title="📈 Distribution par Marché (Top 10)",
            labels={'x': 'Nombre d\'actions', 'y': 'Marché'}
        )
        fig_market.update_layout(height=400)
        st.plotly_chart(fig_market, use_container_width=True)

    with col2:
        sector_counts = df['Sector'].value_counts().head(10)
        fig_sector = px.pie(
            values=sector_counts.values,
            names=sector_counts.index,
            title="🏭 Distribution par Secteur (Top 10)"
        )
        fig_sector.update_layout(height=400)
        st.plotly_chart(fig_sector, use_container_width=True)


def filter_by_setups(df, selected_setups, config):
    """Filtre les actions selon les setups sélectionnés"""
    if not selected_setups:
        return df

    # Charger les résultats réels des screeners
    all_names = set()

    for setup_name in selected_setups:
        # Trouver le setup correspondant dans la config
        for setup_id, setup_info in config["setups"].items():
            if setup_info["name"] == setup_name and "output_file" in setup_info:
                # Charger les noms du screener
                names = load_screener_results(
                    setup_name, setup_info["output_file"])
                if names:
                    all_names.update(names)
                    st.sidebar.success(
                        f"✅ {setup_name}: {len(names)} actions trouvées")
                else:
                    st.sidebar.warning(
                        f"⚠️ {setup_name}: Aucune action trouvée")
                break

    # Filtrer le DataFrame pour ne garder que les noms trouvés
    if all_names:
        # Utiliser la colonne Name pour le filtrage (comme dans votre code original)
        return df[df['Name'].isin(all_names)]
    else:
        return df


def main():
    # En-tête principal
    st.markdown("""
    <div class="main-header">
        <h1>📊 Les moulins du Bazacle</h1>
        <p>Analysez et filtrez les actions selon vos critères d'investissement</p>
    </div>
    """, unsafe_allow_html=True)

    # Chargement des données
    with st.spinner("Chargement des données..."):
        config = load_screener_config()
        df = load_stocks_data()

    if df.empty:
        st.error("Impossible de charger les données. Veuillez réessayer plus tard.")
        return

    # Sidebar pour les filtres
    with st.sidebar:
        st.header("🔍 Filtres")

        # Setups de screening
        st.subheader("📋 Setups de Screening")
        setup_options = {}
        for setup_id, setup_info in config["setups"].items():
            setup_options[setup_info["name"]] = setup_info.get(
                "description", setup_info["name"])

        selected_setups = st.multiselect(
            "Sélectionnez les setups :",
            options=list(setup_options.keys()),
            help="Choisissez un ou plusieurs setups de screening"
        )

        if selected_setups:
            st.write("**Descriptions des setups sélectionnés :**")
            for setup in selected_setups:
                st.write(f"• **{setup}**: {setup_options[setup]}")

        st.divider()

        # Filtres par marché - PAS DE SÉLECTION PAR DÉFAUT
        st.subheader("🏛️ Marchés")
        available_markets = sorted(df['Market'].dropna().unique())
        selected_markets = st.multiselect(
            "Sélectionnez les marchés :",
            options=available_markets
            # PAS de default pour afficher tout au démarrage
        )

        # Filtre PEA
        st.subheader("💼 Éligibilité PEA")

        if 'PEA' in df.columns:
            pea_true_count = df['PEA'].sum()
            st.write(f"🟢 **PEA Eligible**: {pea_true_count} actions")

        if 'PEA-PME' in df.columns:
            pea_pme_true_count = df['PEA-PME'].sum()
            st.write(f"🟡 **PEA-PME Eligible**: {pea_pme_true_count} actions")

        pea_filter = st.selectbox(
            "Filtre PEA :",
            options=["Tous", "PEA Eligible",
                     "Non PEA Eligible", "PEA-PME Eligible"]
        )

        # Critères d'investissement
        st.subheader("🎯 Critères d'Investissement")
        criteria_columns = ['MBagger', 'ROE', 'grow', 'growR',
                            'mom', 'qual', 'qualR', 'small', 'trend', 'value']
        available_criteria = [
            col for col in criteria_columns if col in df.columns]

        selected_criteria = st.multiselect(
            "Sélectionnez les critères :",
            options=available_criteria,
            help="Actions qui respectent au moins un de ces critères"
        )

        # Filtre par secteur
        st.subheader("🏭 Secteurs")
        available_sectors = sorted(df['Sector'].dropna().unique())
        selected_sector = st.selectbox(
            "Sélectionnez un secteur :",
            options=["Tous"] + available_sectors
        )

    # Application des filtres
    filtered_df = df.copy()

    # Filtre par setups EN PREMIER
    if selected_setups:
        filtered_df = filter_by_setups(filtered_df, selected_setups, config)

    # Filtre par marché - SEULEMENT si des marchés sont sélectionnés
    if selected_markets:  # Si la liste n'est pas vide
        filtered_df = filtered_df[filtered_df['Market'].isin(selected_markets)]

    # Filtre PEA
    if pea_filter == "PEA Eligible" and 'PEA' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['PEA'] == True]
    elif pea_filter == "Non PEA Eligible" and 'PEA' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['PEA'] == False]
    elif pea_filter == "PEA-PME Eligible" and 'PEA-PME' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['PEA-PME'] == True]

    # Filtre par critères
    if selected_criteria:
        criteria_mask = filtered_df[selected_criteria].any(axis=1)
        filtered_df = filtered_df[criteria_mask]

    # Filtre par secteur
    if selected_sector != "Tous":
        filtered_df = filtered_df[filtered_df['Sector'] == selected_sector]

    # Affichage des métriques
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 Total Actions",
            value=len(df),
            help="Nombre total d'actions dans la base"
        )

    with col2:
        st.metric(
            label="🎯 Actions Filtrées",
            value=len(filtered_df),
            delta=f"{len(filtered_df) - len(df):+d}"
        )

    with col3:
        pea_count = len(
            filtered_df[filtered_df['PEA'] == True]) if 'PEA' in filtered_df.columns else 0
        st.metric(
            label="💼 PEA Eligible",
            value=pea_count,
            help="Actions éligibles au PEA"
        )

    with col4:
        unique_markets = filtered_df['Market'].nunique()
        st.metric(
            label="🏛️ Marchés",
            value=unique_markets,
            help="Nombre de marchés différents"
        )

    # Onglets pour différentes vues
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Résultats", "📊 Graphiques", "📈 Analyse", "📁 Export"])

    with tab1:
        st.subheader("🎯 Actions Filtrées")

        if len(filtered_df) > 0:
            # Instructions d'utilisation
            st.info("💡 **Instructions :** Cliquez sur l'icône 📊 pour voir les graphiques ou sur le nom de l'entreprise pour accéder à sa fiche complète sur ZoneBourse.")

            # Préparer le DataFrame d'affichage
            display_df = prepare_display_dataframe(filtered_df)

            # Créer une copie pour manipuler les liens
            display_df_links = display_df.copy()

            # Configuration des colonnes avec liens
            column_config = {
                'Market': st.column_config.TextColumn("🏛️ Marché", width="small"),
                'Symbol': st.column_config.TextColumn("📌 Symbole", width="small"),
                'PEA': st.column_config.TextColumn("💼 PEA", width="small"),
                'PEA-PME': st.column_config.TextColumn("🟡 PEA-PME", width="small"),
                'Sector': st.column_config.TextColumn("🏭 Secteur", width="medium"),
                'Industry': st.column_config.TextColumn("🏢 Industrie", width="medium"),
                # Styles d'investissement
                'MBagger': st.column_config.TextColumn("🚀 MBagger", width="small"),
                'ROE': st.column_config.TextColumn("💰 ROE", width="small"),
                'grow': st.column_config.TextColumn("📈 Grow", width="small"),
                'growR': st.column_config.TextColumn("📊 GrowR", width="small"),
                'mom': st.column_config.TextColumn("⚡ Mom", width="small"),
                'qual': st.column_config.TextColumn("✨ Qual", width="small"),
                'qualR': st.column_config.TextColumn("⭐ QualR", width="small"),
                'small': st.column_config.TextColumn("🔍 Small", width="small"),
                'trend': st.column_config.TextColumn("📉 Trend", width="small"),
                'value': st.column_config.TextColumn("💎 Value", width="small")
            }

            # Configuration pour la colonne graphique
            if '📊' in display_df_links.columns and 'ZB URL' in filtered_df.columns:
                # Créer les URLs pour les graphiques
                chart_urls = []
                for idx in display_df_links.index:
                    zb_url = filtered_df.loc[idx, 'ZB URL']
                    if pd.isna(zb_url) or zb_url == '':
                        chart_urls.append(None)
                    else:
                        chart_urls.append(f"{zb_url.rstrip('/')}/graphiques/")

                display_df_links['📊'] = chart_urls

                column_config['📊'] = st.column_config.LinkColumn(
                    "📊",
                    help="Cliquer pour voir les graphiques",
                    display_text="📊",
                    width="small"
                )

            # Configuration pour la colonne Name avec lien
            if 'Name' in display_df_links.columns and 'ZB URL' in filtered_df.columns:
                # Préserver le nom original
                display_df_links['Name_Original'] = display_df_links['Name'].copy()

                # Remplacer par les URLs
                display_df_links['Name'] = filtered_df.loc[display_df_links.index, 'ZB URL']

                column_config['Name'] = st.column_config.LinkColumn(
                    "🏢 Nom",
                    help="Cliquer pour voir la fiche complète",
                    width="medium",
                    # Expression régulière pour extraire le nom de l'URL
                    display_text=r"/([^/]*?)(-\d+)?/$"
                )

            # Affichage du tableau avec configuration des liens
            st.dataframe(
                display_df_links,
                use_container_width=True,
                height=600,
                column_config=column_config,
                hide_index=True
            )

            # Possibilité de télécharger les résultats
            csv = filtered_df.to_csv(index=False, sep=';')
            st.download_button(
                label="📥 Télécharger les résultats (CSV)",
                data=csv,
                file_name=f"screener_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Aucune action ne correspond aux critères sélectionnés.")

    with tab2:
        st.subheader("📊 Visualisations")
        if len(filtered_df) > 0:
            create_summary_charts(filtered_df)

            # Graphiques PEA/PEA-PME
            col1, col2 = st.columns(2)

            with col1:
                if 'PEA' in filtered_df.columns:
                    pea_distribution = filtered_df['PEA'].value_counts()
                    fig_pea = px.pie(
                        values=pea_distribution.values,
                        names=[
                            'Non PEA' if not x else 'PEA Eligible' for x in pea_distribution.index],
                        title="💼 Répartition PEA"
                    )
                    st.plotly_chart(fig_pea, use_container_width=True)

            with col2:
                if 'PEA-PME' in filtered_df.columns:
                    pea_pme_distribution = filtered_df['PEA-PME'].value_counts()
                    fig_pea_pme = px.pie(
                        values=pea_pme_distribution.values,
                        names=[
                            'Non PEA-PME' if not x else 'PEA-PME Eligible' for x in pea_pme_distribution.index],
                        title="🟡 Répartition PEA-PME"
                    )
                    st.plotly_chart(fig_pea_pme, use_container_width=True)

            # Graphique des styles d'investissement
            st.subheader("🎯 Répartition des Styles d'Investissement")
            style_columns = ['MBagger', 'ROE', 'grow', 'growR',
                             'mom', 'qual', 'qualR', 'small', 'trend', 'value']
            style_data = []
            for style in style_columns:
                if style in filtered_df.columns:
                    count = filtered_df[style].sum()
                    style_data.append({'Style': style, 'Nombre': count})

            if style_data:
                style_df = pd.DataFrame(style_data)
                fig_styles = px.bar(
                    style_df,
                    x='Style',
                    y='Nombre',
                    title="Nombre d'actions par style d'investissement",
                    color='Nombre',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_styles, use_container_width=True)
        else:
            st.info("Sélectionnez des filtres pour voir les graphiques.")

    with tab3:
        st.subheader("📈 Analyse Avancée")
        if len(filtered_df) > 0:
            col1, col2 = st.columns(2)

            with col1:
                st.write("**📊 Statistiques par Marché**")
                market_stats = filtered_df.groupby(
                    'Market').size().sort_values(ascending=False)
                st.bar_chart(market_stats)

            with col2:
                st.write("**🏭 Top 10 Secteurs**")
                sector_stats = filtered_df['Sector'].value_counts().head(10)
                st.bar_chart(sector_stats)

            # Matrice de corrélation des styles d'investissement
            style_columns = ['MBagger', 'ROE', 'grow', 'growR',
                             'mom', 'qual', 'qualR', 'small', 'trend', 'value']
            available_styles = [
                col for col in style_columns if col in filtered_df.columns]

            if len(available_styles) > 1:
                st.write("**🔗 Corrélation entre Styles d'Investissement**")
                corr_matrix = filtered_df[available_styles].corr()
                fig_corr = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    title="Matrice de corrélation des styles"
                )
                st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Aucune donnée à analyser.")

    with tab4:
        st.subheader("📁 Export et Rapports")

        if len(filtered_df) > 0:
            # Résumé des filtres appliqués
            st.write("**📋 Filtres Appliqués :**")
            if selected_setups:
                st.write(f"• Setups: {', '.join(selected_setups)}")
            if selected_markets:
                st.write(f"• Marchés: {', '.join(selected_markets)}")
            if pea_filter != "Tous":
                st.write(f"• PEA: {pea_filter}")
            if selected_criteria:
                st.write(f"• Critères: {', '.join(selected_criteria)}")
            if selected_sector != "Tous":
                st.write(f"• Secteur: {selected_sector}")

            # Options d'export
            st.write("**📊 Options d'Export :**")

            # Export CSV complet
            csv_full = filtered_df.to_csv(index=False, sep=';')
            st.download_button(
                label="📥 Export CSV Complet",
                data=csv_full,
                file_name=f"screener_full_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

            # Export CSV simplifié
            simple_cols = ['Market', 'Name', 'Symbol',
                           'PEA', 'PEA-PME', 'Sector', 'ZB URL']
            simple_cols = [
                col for col in simple_cols if col in filtered_df.columns]
            csv_simple = filtered_df[simple_cols].to_csv(index=False, sep=';')
            st.download_button(
                label="📥 Export CSV Simplifié",
                data=csv_simple,
                file_name=f"screener_simple_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
