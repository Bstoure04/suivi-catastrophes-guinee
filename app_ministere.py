import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit_authenticator as stauth
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Ministère de l'Environnement - Guinée", layout="wide")

# --- 2. SYSTÈME D'AUTHENTIFICATION (SIMULÉ) ---
# Dans une version réelle, on chargerait le fichier config.yaml ici
names = ['Administrateur Principal', 'Agent Conakry', 'Agent Nzérékoré']
usernames = ['admin', 'agent_ckry', 'agent_zaly']
passwords = ['admin123', 'conakry2024', 'forestiere2024']

# Hachage des mots de passe (pour le prototype)
hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    {'credentials': {'usernames': {u: {'name': n, 'password': p} for u, n, p in zip(usernames, names, hashed_passwords)}},
     'cookie': {'expiry_days': 30, 'key': 'secret_key', 'name': 'mde_auth'}},
    'mde_dashboard', 'auth_key', cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login('Connexion au Portail Ministériel', 'main')

# --- 3. LOGIQUE DE L'APPLICATION ---
if authentication_status:
    st.sidebar.title(f"Bienvenue, {name}")
    authenticator.logout('Déconnexion', 'sidebar')

    # Initialisation de la base de données en mémoire
    if 'db' not in st.session_state:
        st.session_state.db = pd.DataFrame(columns=[
            "ID", "Agent", "Type", "Région Naturelle", "Ville", "Date", "Alerte", "Lat", "Lon", "Description"
        ])

    st.title("🇬🇳 Système National de Suivi des Catastrophes")

    # --- ONGLETS ---
    tab1, tab2 = st.tabs(["📝 Saisie des Données", "📊 Tableau de Bord & Carte"])

    with tab1:
        st.header("Enregistrement d'un nouvel incident")
        with st.form("form_incid"):
            col1, col2 = st.columns(2)
            with col1:
                t_cata = st.selectbox("Type", ["Inondation", "Feu de brousse", "Sécheresse", "Éboulement", "Pollution"])
                r_nat = st.selectbox("Région Naturelle", ["Guinée Maritime", "Moyenne Guinée", "Haute Guinée", "Guinée Forestière"])
                ville = st.text_input("Préfecture / Ville")
            with col2:
                date_ev = st.date_input("Date", datetime.now())
                niv = st.select_slider("Gravité", options=["Faible", "Moyenne", "Élevée", "Critique"])
                lat = st.number_input("Latitude", value=9.509, format="%.4f")
                lon = st.number_input("Longitude", value=-13.712, format="%.4f")
            
            desc = st.text_area("Observations et impacts constatés")
            if st.form_submit_button("Transmettre au Ministère"):
                new_entry = {
                    "ID": len(st.session_state.db)+1, "Agent": name, "Type": t_cata, 
                    "Région Naturelle": r_nat, "Ville": ville, "Date": date_ev, 
                    "Alerte": niv, "Lat": lat, "Lon": lon, "Description": desc
                }
                st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_entry])], ignore_index=True)
                st.success("Donnée sécurisée et enregistrée.")

    with tab2:
        df = st.session_state.db
        if not df.empty:
            st.header("Analyse et Visualisation")
            
            # --- FILTRES DYNAMIQUES ---
            c1, c2 = st.columns(2)
            with c1:
                f_type = st.multiselect("Filtrer par Type", df["Type"].unique())
            with c2:
                f_reg = st.multiselect("Filtrer par Région", df["Région Naturelle"].unique())

            dff = df.copy()
            if f_type: dff = dff[dff["Type"].isin(f_type)]
            if f_reg: dff = dff[dff["Région Naturelle"].isin(f_reg)]

            # --- CARTE INTERACTIVE ---
            m = folium.Map(location=[10.5, -11.0], zoom_start=7)
            for _, row in dff.iterrows():
                color = "red" if row["Alerte"] == "Critique" else "orange" if row["Alerte"] == "Élevée" else "blue"
                folium.Marker(
                    [row["Lat"], row["Lon"]],
                    popup=f"<b>{row['Type']}</b> - {row['Ville']}",
                    icon=folium.Icon(color=color)
                ).add_to(m)
            
            st_folium(m, width=1000, height=450)
            st.dataframe(dff, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour le moment.")

elif authentication_status == False:
    st.error('Identifiants incorrects.')