import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AutoSMC Ultimate - São Miguel dos Campos", layout="wide", page_icon="🏎️")

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .main-card { background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
    .price-badge { background-color: #2ecc71; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    .alagoas-badge { background-color: #e74c3c; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DE DADOS (API FIPE) ---
BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros/marcas"

@st.cache_data(ttl=3600)
def get_api_data(endpoint):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", timeout=10)
        return r.json()
    except:
        return None

def get_car_details(m_id, mod_id, a_id):
    return get_api_data(f"{m_id}/modelos/{mod_id}/anos/{a_id}")

# --- FUNÇÕES DE CÁLCULO ---
def calcular_custos_alagoas(valor_fipe):
    ipva = valor_fipe * 0.03  # Alíquota AL
    seguro_est = valor_fipe * 0.05
    licenciamento = 180.00
    return ipva, seguro_est, licenciamento

# --- BARRA LATERAL (PAINEL DE CONTROLE) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3202/3202926.png", width=80)
    st.title("AutoSMC Ultimate")
    mode = st.radio("Modo do App", ["Análise Detalhada", "Comparador x2"])
    
    st.divider()
    st.subheader("Configurações Regionais")
    cidade = st.text_input("Cidade Base", "São Miguel dos Campos - AL")
    taxa_juros = st.slider("Taxa de Juros Mensal (%)", 1.0, 5.0, 1.95)

# --- LÓGICA DE SELEÇÃO DE VEÍCULOS ---
def selector_veiculo(key_prefix):
    marcas = get_api_data("")
    m_list = {m['nome']: m['codigo'] for m in marcas}
    marca = st.selectbox(f"Marca", list(m_list.keys()), key=f"m_{key_prefix}")
    
    modelos = get_api_data(f"{m_list[marca]}/modelos")
    mod_list = {mo['nome']: mo['codigo'] for mo in modelos['modelos']}
    modelo = st.selectbox(f"Modelo", list(mod_list.keys()), key=f"mod_{key_prefix}")
    
    anos = get_api_data(f"{m_list[marca]}/modelos/{mod_list[modelo]}/anos")
    a_list = {a['nome']: a['codigo'] for a in anos}
    ano = st.selectbox(f"Ano/Versão", list(a_list.keys()), key=f"a_{key_prefix}")
    
    return get_car_details(m_list[marca], mod_list[modelo], a_list[ano])

# --- CONTEÚDO PRINCIPAL ---
if mode == "Análise Detalhada":
    st.header("🔍 Relatório Detalhado de Mercado")
    with st.expander("Clique para selecionar o veículo", expanded=True):
        veiculo = selector_veiculo("single")

    if veiculo:
        v_fipe = float(veiculo['Valor'].replace('R$ ', '').replace('.', '').replace(',', '.'))
        ipva, seguro, licen = calcular_custos_alagoas(v_fipe)
        
        # Dashboard Principal
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tabela FIPE", veiculo['Valor'])
        col2.metric("IPVA AL (3%)", f"R$ {ipva:,.2f}")
        col3.metric("Média São Miguel", f"R$ {v_fipe*1.02:,.2f}")
        col4.metric("Desvalorização Est.", "-4.2%")

        st.markdown("---")
        
        c_left, c_right = st.columns([1.5, 1])
        
        with c_left:
            st.subheader("🖼️ Galeria & Projeção")
            st.image(f"https://source.unsplash.com/800x450/?car,{veiculo['Marca']}", use_container_width=True)
            
            # Gráfico Complexo de Manutenção
            itens = ['Peças de Motor', 'Suspensão', 'Funilaria', 'Revenda local']
            scores = [85, 70, 60, 90] # Scores fictícios baseados em popularidade
            fig = go.Figure(data=[go.Bar(x=itens, y=scores, marker_color='#3498db')])
            fig.update_layout(title="Facilidade de Manutenção em Alagoas (0-100)")
            st.plotly_chart(fig, use_container_width=True)

        with c_right:
            st.subheader("📋 Ficha e Custos")
            st.write(f"**Referência:** {veiculo['MesReferencia']}")
            st.write(f"**Código FIPE:** {veiculo['CodigoFipe']}")
            
            # Tabela de Manutenção
            df_custos = pd.DataFrame({
                'Serviço': ['Troca de Óleo (Estimada)', 'Seguro Anual Médio', 'Licenciamento', 'IPVA 2026'],
                'Valor (R$)': [350.00, seguro, licen, ipva]
            })
            st.table(df_custos)
            
            # Exportação
            csv = df_custos.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Relatório (CSV)", csv, "relatorio_autosmc.csv", "text/csv")

else:
    st.header("⚖️ Comparador de Mercado (Lado a Lado)")
    comp1, comp2 = st.columns(2)
    
    with comp1:
        st.subheader("Veículo A")
        v1 = selector_veiculo("v1")
    with comp2:
        st.subheader("Veículo B")
        v2 = selector_veiculo("v2")

    if v1 and v2:
        val1 = float(v1['Valor'].replace('R$ ', '').replace('.', '').replace(',', '.'))
        val2 = float(v2['Valor'].replace('R$ ', '').replace('.', '').replace(',', '.'))
        
        st.markdown("### Comparativo de Parcelas (Financiamento)")
        parc = st.select_slider("Número de Parcelas", options=[12, 24, 36, 48, 60], value=48)
        
        def calc_parc(valor, juros, n):
            return (valor * (juros/100)) / (1 - (1 + (juros/100))**-n)

        p1 = calc_parc(val1, taxa_juros, parc)
        p2 = calc_parc(val2, taxa_juros, parc)

        col_a, col_b = st.columns(2)
        col_a.info(f"**{v1['Modelo']}**: {parc}x de R$ {p1:,.2f}")
        col_b.success(f"**{v2['Modelo']}**: {parc}x de R$ {p2:,.2f}")
        
        # Gráfico Comparativo
        fig_comp = go.Figure(data=[
            go.Bar(name=v1['Modelo'], x=['Preço Total', 'Custo Anual Mant.'], y=[val1, val1*0.1]),
            go.Bar(name=v2['Modelo'], x=['Preço Total', 'Custo Anual Mant.'], y=[val2, val2*0.1])
        ])
        st.plotly_chart(fig_comp, use_container_width=True)

# --- RODAPÉ ---
st.markdown("---")
st.markdown(f"📍 **Hub de Inteligência Automotiva - São Miguel dos Campos** | {datetime.now().year}")