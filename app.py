import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# --- CONFIGURACIÓN Y CONEXIÓN ---
def get_data():
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
        'https://spreadsheets.google.com/feeds', 
        'https://www.googleapis.com/auth/drive'
    ])
    client = gspread.authorize(creds)
    sh = client.open("BaseDatosOrdenes")
    sheet = sh.worksheet("Hoja1")
    return pd.DataFrame(sheet.get_all_records())

def limpiar_codigo(texto):
    match = re.findall(r'\d+', str(texto))
    return "".join(match) if match else None

# --- INTERFAZ ---
st.set_page_config(page_title="GO Service Pulse", layout="wide")

if 'role' not in st.session_state:
    st.session_state.role = "Usuario Final"

with st.sidebar:
    st.title("Acceso")
    st.session_state.role = st.selectbox("Perfil", ["Usuario Final", "Administrador"])

# --- LÓGICA USUARIO FINAL ---
if st.session_state.role == "Usuario Final":
    st.title("📦 GO Service Pulse - Seguimiento")
    codigo_input = st.text_input("Ingrese su código de cliente (ej: 0098001303)")
    
    if codigo_input:
        df = get_data()
        df['codigo_limpio'] = df['Codigo Clie May'].apply(limpiar_codigo)
        resultado = df[df['codigo_limpio'] == limpiar_codigo(codigo_input)]
        
        if not resultado.empty:
            st.success(f"Se encontraron {len(resultado)} órdenes.")
            st.table(resultado[['#Orden', 'Fecha', 'Estado', 'Producto', 'Observaciones']])
        else:
            st.warning("No se encontraron órdenes.")

# --- LÓGICA ADMINISTRADOR ---
elif st.session_state.role == "Administrador":
    st.title("⚙️ Panel de Administración")
    uploaded_file = st.file_uploader("Subir archivo de órdenes (CSV/XLSX)", type=['csv', 'xlsx'])
    
    if uploaded_file and st.button("Procesar e Importar"):
        df_nuevo = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df_actual = get_data()
        
        # Filtrar duplicados por #Orden
        existentes = df_actual['#Orden'].astype(str).tolist()
        df_a_subir = df_nuevo[~df_nuevo['#Orden'].astype(str).isin(existentes)]
        
        if not df_a_subir.empty:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
            client = gspread.authorize(creds)
            sh = client.open("BaseDatosOrdenes").worksheet("Hoja1")
            
            sh.append_rows(df_a_subir.fillna("").values.tolist())
            st.success(f"Se cargaron {len(df_a_subir)} órdenes nuevas.")
        else:
            st.info("No hay órdenes nuevas para cargar.")
