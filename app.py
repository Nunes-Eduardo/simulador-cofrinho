import streamlit as st
import pandas as pd
from datetime import date, timedelta
import numpy as np

# =========================
# FUNÇÕES FINANCEIRAS
# =========================
def aliquota_ir_regressiva(dias):
    if dias <= 180:
        return 0.225
    elif dias <= 360:
        return 0.20
    elif dias <= 720:
        return 0.175
    else:
        return 0.15


def simular_cofrinho(
    saldo_inicial,
    cdi_anual,
    percentual_cdi,
    data_inicio,
    data_fim,
    aportes
):
    dias_ano = 252
    taxa_diaria = (1 + cdi_anual)**(1 / dias_ano) - 1
    taxa_diaria *= percentual_cdi

    saldo = saldo_inicial
    total_aportado = saldo_inicial
    data_atual = data_inicio

    registros = []

    while data_atual <= data_fim:
        aporte = aportes.get(data_atual, 0.0)
        saldo += aporte
        total_aportado += aporte

        rendimento = 0.0
        if data_atual.weekday() < 5:  # dia útil
            rendimento = saldo * taxa_diaria
            saldo += rendimento

        registros.append({
            "Data": data_atual,
            "Aporte": aporte,
            "Rendimento do dia": rendimento,
            "Saldo": saldo
        })

        data_atual += timedelta(days=1)

    df = pd.DataFrame(registros)

    dias_corridos = (data_fim - data_inicio).days
    ir = aliquota_ir_regressiva(dias_corridos)
    lucro = saldo - total_aportado
    imposto_estimado = max(lucro, 0) * ir

    return df, saldo, imposto_estimado, taxa_diaria


def saldo_para_meta(meta_diaria, taxa_diaria):
    if taxa_diaria <= 0:
        return 0
    return meta_diaria / taxa_diaria


# =========================
# INTERFACE
# =========================
st.set_page_config(page_title="Simulador de Cofrinho", layout="wide")

st.title("💰 Simulador de Cofrinho – Liquidez Diária")

st.markdown(
    "Este app é uma **estimativa didática** baseada em CDI, dias úteis e capitalização diária."
)

# =========================
# INPUTS
# =========================
with st.sidebar:
    st.header("📌 Parâmetros")

    saldo_inicial = st.number_input("Saldo inicial (R$)", value=1550.0, step=50.0)
    cdi_anual = st.number_input("CDI anual (%)", value=10.5) / 100
    percentual_cdi = st.number_input("% do CDI", value=102.0) / 100

    data_inicio = st.date_input("Data inicial", value=date.today())
    data_fim = st.date_input("Data final")

    st.divider()
    st.subheader("➕ Aporte único")
    data_aporte = st.date_input("Data do aporte", key="aporte_data")
    valor_aporte = st.number_input("Valor do aporte", min_value=0.0, step=50.0)

    if "aportes" not in st.session_state:
        st.session_state.aportes = {}

    if st.button("Adicionar aporte"):
        st.session_state.aportes[data_aporte] = valor_aporte
        st.success("Aporte adicionado")


# =========================
# SIMULAÇÃO
# =========================
if st.button("▶️ Simular"):
    df, saldo_final, ir_estimado, taxa_diaria = simular_cofrinho(
        saldo_inicial,
        cdi_anual,
        percentual_cdi,
        data_inicio,
        data_fim,
        st.session_state.aportes
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Saldo final bruto", f"R$ {saldo_final:,.2f}")
    col2.metric("IR estimado (informativo)", f"R$ {ir_estimado:,.2f}")
    col3.metric(
        "Rendimento diário final",
        f"R$ {(saldo_final * taxa_diaria):,.2f}"
    )

    st.divider()

    # =========================
    # GRÁFICOS
    # =========================
    st.subheader("📈 Evolução do saldo")
    st.line_chart(df.set_index("Data")["Saldo"])

    st.subheader("💸 Rendimento diário")
    st.line_chart(df.set_index("Data")["Rendimento do dia"])

    st.subheader("📊 Aporte × Rendimento")
    df["Rendimento acumulado"] = df["Saldo"] - df["Aporte"].cumsum() - saldo_inicial
    st.area_chart(
        df.set_index("Data")[["Aporte", "Rendimento acumulado"]]
    )

    st.divider()

    # =========================
    # METAS
    # =========================
    st.subheader("🎯 Meta de liquidez diária")

    meta = st.number_input(
        "Quanto você quer ganhar por dia (R$)?",
        min_value=0.5,
        step=0.5
    )

    saldo_necessario = saldo_para_meta(meta, taxa_diaria)

    st.info(
        f"Para ganhar aproximadamente **R$ {meta:.2f} por dia**, "
        f"você precisaria de cerca de **R$ {saldo_necessario:,.2f}** investidos."
    )

    st.divider()
    st.subheader("📋 Últimos dias da simulação")
    st.dataframe(df.tail(10), use_container_width=True)
