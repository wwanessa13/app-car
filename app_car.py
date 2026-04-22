import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Previsão de preços de carros",
    page_icon="🚗",
    layout="wide"
)

def format_brl(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R\\$ {texto}"

# Carregar modelo
@st.cache_resource
def load_model():
    try:
        return joblib.load("model.pkl")
    except FileNotFoundError:
        return None

# Conversões
def lakh_to_brl(valor_lakh, taxa=0.06):
    return valor_lakh * 100000 * taxa

def brl_to_lakh(valor_brl, taxa=0.06):
    return valor_brl / (100000 * taxa)

# Título
st.markdown(
    "<h3 style='text-align: center;'>Sistema de Previsão de Preços de Carros Usados</h3>",
    unsafe_allow_html=True
)

model = load_model()

if model is None:
    st.error("Modelo não encontrado. Verifique se o arquivo 'model_car.pkl' está na mesma pasta do aplicativo.")
    st.stop()

# Sidebar
st.sidebar.title("Detalhes do carro")

st.sidebar.subheader("Informações básicas")
ano = st.sidebar.slider("Ano de fabricação", 2000, datetime.now().year, 2015)
preco_fabrica_brl = st.sidebar.number_input(
    "Preço atual de fábrica (R$)",
    min_value=0.0,
    max_value=500000.0,
    value=50000.0,
    step=1000.0
)
kms_driven = st.sidebar.number_input("Quilômetros rodados", 0, 500000, 50000, 1000)

st.sidebar.subheader("Especificações do carro")
fuel_type = st.sidebar.selectbox("Tipo de combustível", ["Gasolina", "Diesel", "Gás Natural"])
seller_type = st.sidebar.selectbox("Tipo de vendedor", ["Concessionária", "Particular"])
transmission = st.sidebar.selectbox("Transmissão", ["Manual", "Automático"])
owner = st.sidebar.selectbox("Número de proprietários anteriores", [0, 1, 2, 3, 4, 5])

st.sidebar.markdown("---")
predict_btn = st.sidebar.button("Obtenha uma estimativa de preço", type="primary", use_container_width=True)

# Idade do carro
car_age = datetime.now().year - ano

if predict_btn:
    fuel_encoded = {"Gasolina": 0, "Diesel": 1, "Gás Natural": 2}[fuel_type]
    seller_encoded = {"Concessionária": 0, "Particular": 1}[seller_type]
    transmission_encoded = {"Manual": 0, "Automático": 1}[transmission]

    # Converter preço em R$ para lakh antes de enviar ao modelo
    present_price_lakh = brl_to_lakh(preco_fabrica_brl)

    # Entrada do modelo
    input_data = pd.DataFrame({
        "Year": [ano],
        "Present_Price": [present_price_lakh],
        "Kms_Driven": [kms_driven],
        "Fuel_Type": [fuel_encoded],
        "Seller_Type": [seller_encoded],
        "Transmission": [transmission_encoded],
        "Owner": [owner]
    })

    # Predição em lakh
    predicted_price_lakh = model.predict(input_data)[0]

    # Evitar preço negativo
    predicted_price_lakh = max(predicted_price_lakh, 0)

    # Conversão para R$
    predicted_price_brl = lakh_to_brl(predicted_price_lakh)
    present_price_brl = preco_fabrica_brl
    depreciation_brl = present_price_brl - predicted_price_brl
    depreciation_percent = (depreciation_brl / present_price_brl) * 100 if present_price_brl > 0 else 0

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Preço estimado de venda",
            f"R$ {predicted_price_brl:,.2f}"
        )

    with col2:
        st.metric(
            "Preço atual de fábrica",
            f"R$ {present_price_brl:,.2f}"
        )

    with col3:
        st.metric(
            "Depreciação total",
            f"R$ {depreciation_brl:,.2f}",
            delta=f"-{depreciation_percent:.1f}%"
        )

    st.markdown("---")
    st.subheader("Análise de preço")

    col1, col2 = st.columns([2, 1])

    with col1:
        lower_estimate_brl = lakh_to_brl(predicted_price_lakh * 0.9)
        upper_estimate_brl = lakh_to_brl(predicted_price_lakh * 1.1)

        st.success(f"""
        **Faixa de preço esperada:** {format_brl(lower_estimate_brl)} - {format_brl(upper_estimate_brl)}
        """)

        st.write("**Fatores que influenciam o preço:**")

        factors = []

        if car_age <= 2:
            factors.append("Carro muito novo - depreciação mínima")
        elif car_age <= 5:
            factors.append("Relativamente novo - bom valor de revenda")
        elif car_age <= 10:
            factors.append("Idade moderada - valor médio de mercado")
        else:
            factors.append("Carro mais antigo - maior depreciação")

        if kms_driven < 30000:
            factors.append("Baixa quilometragem - agrega valor")
        elif kms_driven < 80000:
            factors.append("Quilometragem média")
        else:
            factors.append("Alta quilometragem - reduz o valor")

        if transmission == "Automático":
            factors.append("Transmissão automática - pode elevar o valor")

        if fuel_type == "Diesel":
            factors.append("Diesel - preferido para uso intenso")
        elif fuel_type == "Gasolina":
            factors.append("Gasolina - opção padrão")
        elif fuel_type == "Gás Natural":
            factors.append("Gás Natural - alternativa mais econômica")

        if seller_type == "Concessionária":
            factors.append("Concessionária - pode oferecer maior confiabilidade")

        for factor in factors:
            st.markdown(f"- {factor}")

    with col2:
        max_price_brl = max(present_price_brl * 1.2, predicted_price_brl * 1.2, 1000)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=predicted_price_brl,
            title={"text": "Preço estimado"},
            number={"prefix": "R$ "},
            gauge={
                "axis": {"range": [None, max_price_brl]},
                "bar": {"color": "#e74c3c"},
                "steps": [
                    {"range": [0, present_price_brl * 0.3], "color": "lightgray"},
                    {"range": [present_price_brl * 0.3, present_price_brl * 0.7], "color": "lightyellow"},
                    {"range": [present_price_brl * 0.7, max_price_brl], "color": "lightgreen"}
                ],
                "threshold": {
                    "line": {"color": "blue", "width": 4},
                    "thickness": 0.75,
                    "value": present_price_brl
                }
            }
        ))

        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
