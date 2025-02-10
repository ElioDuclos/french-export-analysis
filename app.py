import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Analyses Douanes France")

def load_data():
    export_data = pd.read_csv(
        "REGIONAL_CPF4PAYSE.txt", 
        sep=";", 
        encoding="utf-8",
        names=['flux', 'trimestre', 'annee', 'dept', 'region', 'a129', 'cpf4', 'pays', 'valeur', 'masse'],
        dtype={'region': str}  # Convert region to string
    )

    
    pays_ref = pd.read_csv("Libelle_PAYS.txt", sep=";", encoding="latin1",
                          names=['code', 'libelle', 'debut', 'fin'])
    
    cpf4_ref = pd.read_csv("Libelle_CPF4_rev2.1.txt", sep=";", encoding="latin1",
                          names=['code', 'libelle', 'debut', 'fin'])
    
    
    regions_ref = pd.read_csv("Departement_region.txt", sep=";", encoding="utf-8",
                            names=['dept', 'dept_nom', 'region', 'region_nom'],
                            dtype={'region': str})  # Ensure consistent type
    
    return export_data, pays_ref, cpf4_ref, regions_ref
def show_regional_analysis(filtered_data, regions_ref):
    # Ensure consistent types before merging
    merged_data = filtered_data.merge(
        regions_ref[['region', 'region_nom']].drop_duplicates(), 
        on='region', 
        how='left'
    )
    # Add error checking
    if merged_data.empty:
        st.error("No data found after merging. Check your merge conditions.")
        return
    region_agg = merged_data.groupby('region_nom')['valeur'].sum().reset_index()
    
    # Bar Chart
    fig_bar = px.bar(region_agg.sort_values('valeur', ascending=False),
                     x='region_nom', 
                     y='valeur',
                     title="Exportations par Région",
                     labels={'region_nom': 'Région', 'valeur': 'Valeur des Exportations (€)'})
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Manually define regions for France
    regions_france = {
        'Hauts-de-France': [50.9, 2.3],
        'Normandie': [49.2, 0.1],
        'Grand Est': [48.7, 4.5],
        'Bourgogne - Franche-Comté': [47.3, 4.8],
        'Centre-Val de Loire': [47.3, 1.9],
        'Ile-de-France': [48.8, 2.3],
        'Bretagne': [48.1, -3.1],
        'Pays de la Loire': [47.5, -0.7],
        'Nouvelle-Aquitaine': [45.7, 0.1],
        'Occitanie': [43.6, 2.2],
        'Auvergne - Rhône-Alpes': [45.5, 4.7],
        'Provence-Alpes-Côte d\'Azur': [43.5, 5.4],
        'Corse': [42.2, 9.0]
    }
    
    # Create a DataFrame with coordinates
    region_agg['lat'] = region_agg['region_nom'].map(lambda x: regions_france.get(x, [None])[0])
    region_agg['lon'] = region_agg['region_nom'].map(lambda x: regions_france.get(x, [None, None])[1])
    
    # Remove rows with missing coordinates
    region_agg_mapped = region_agg.dropna(subset=['lat', 'lon'])
    
    # Create scatter map
    fig_map = go.Figure(data=go.Scattergeo(
        lon=region_agg_mapped['lon'],
        lat=region_agg_mapped['lat'],
        text=region_agg_mapped['region_nom'] + '<br>Exportations: ' + region_agg_mapped['valeur'].apply(lambda x: f'{x/1e6:.2f}M€'),
        mode='markers',
        marker=dict(
            size=10,
            color=region_agg_mapped['valeur'],
            colorscale='Viridis',
            colorbar_title='Valeur des Exportations (€)',
            showscale=True
        )
    ))
    
    fig_map.update_layout(
        title='Exportations par Région',
        geo_scope='europe',
        height=800,  # Hauteur en pixels
        width=1200   # Largeur en pixels
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Display total values for reference
    st.write("Valeurs totales des exportations par région :")
    st.dataframe(region_agg.sort_values('valeur', ascending=False))

def show_country_analysis(filtered_data, pays_ref):
    merged_data = filtered_data.merge(pays_ref, left_on='pays', right_on='code')
    country_agg = merged_data.groupby('libelle')['valeur'].sum().nlargest(10)
    
    fig = px.bar(country_agg,
                 title="Top 10 Pays Destinataires",
                 labels={'value': 'Valeur (€)', 'libelle': 'Pays'})
    st.plotly_chart(fig, use_container_width=True)

def show_product_analysis(filtered_data, cpf4_ref):
    merged_data = filtered_data.merge(cpf4_ref, left_on='cpf4', right_on='code')
    product_agg = merged_data.groupby('libelle')['valeur'].sum().nlargest(10)
    
    fig = px.pie(product_agg,
                 title="Top 10 Produits Exportés",
                 values=product_agg.values,
                 names=product_agg.index)
    st.plotly_chart(fig, use_container_width=True)

def main():
    export_data, pays_ref, cpf4_ref, regions_ref = load_data()

    st.title("Analyse des Exportations Françaises")

    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        available_years = sorted(export_data['annee'].unique())
        annee = st.selectbox("Année", available_years)

    with col2:
        # Filter trimesters only for the selected year
        available_trimesters = sorted(export_data[export_data['annee'] == annee]['trimestre'].unique())

        if len(available_trimesters) < 4:
            st.warning(f"Seulement {len(available_trimesters)} trimestre(s) disponible(s) pour {annee}")

        trimestre = st.selectbox("Trimestre", available_trimesters)
    # Filtrage des données
    filtered_data = export_data[
        (export_data['annee'] == annee) & 
        (export_data['trimestre'] == trimestre)
    ]

    # KPIs
    total_value = filtered_data['valeur'].sum()
    avg_value = filtered_data['valeur'].mean()
    total_weight = filtered_data['masse'].sum()

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Valeur Totale", f"{total_value/1e9:.2f}B€")
    with kpi2:
        st.metric("Valeur Moyenne", f"{avg_value/1e6:.2f}M€")
    with kpi3:
        st.metric("Masse Totale", f"{total_weight/1e6:.2f}T")

    # Onglets d'analyse
    tab1, tab2, tab3 = st.tabs(["Régions", "Pays", "Produits"])

    with tab1:
        show_regional_analysis(filtered_data, regions_ref)

    with tab2:
        show_country_analysis(filtered_data, pays_ref)

    with tab3:
        show_product_analysis(filtered_data, cpf4_ref)

    if st.checkbox("Afficher les données détaillées"):
        detailed_data = (filtered_data
            .merge(regions_ref, left_on='dept', right_on='dept')
            .merge(pays_ref, left_on='pays', right_on='code', suffixes=('', '_pays'))
            .merge(cpf4_ref, left_on='cpf4', right_on='code', suffixes=('', '_cpf4'))
            [['region_nom', 'libelle', 'libelle_cpf4', 'valeur', 'masse']]
            .rename(columns={
                'region_nom': 'Région',
                'libelle': 'Pays',
                'libelle_cpf4': 'Produit',
                'valeur': 'Valeur (€)',
                'masse': 'Masse (kg)'
            })
        )
        st.dataframe(detailed_data)

if __name__ == "__main__":
    main()
