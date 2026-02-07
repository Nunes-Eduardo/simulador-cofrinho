import streamlit as st
import pandas as pd
from datetime import date, timedelta

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
    taxa_diaria = (1 + cdi_anual) ** (1 / dias_ano) - 1
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
        return 0.0
    return meta_diaria / taxa_diaria


# =========================
# INTERFACE
# =========================
st.set_page_config(page_title="Simulador de Cofrinho", layout="wide")

st.title("💰 Simulador de Cofrinho – Liquidez Diária")
st.write("Simulação estimativa baseada em CDI e dias úteis.")

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("📌 Parâmetros")

    saldo_inicial = st.number_input(
        "Saldo inicial (R$)",
        value=1550.0,
        step=50.0
    )

    cdi_anual = st.number_input(
        "CDI anual (%)",
        value=10.5
    ) / 100

    percentual_cdi = st.number_input(
        "% do CDI",
        value=102.0
    ) / 100

    data_inicio = st.date_input(
        "Data inicial",
        value=date.today()
    )

    data_fim = st.date_input("Data final")

    st.divider()
    st.subheader("➕ Aporte pontual")

    data_aporte = st.date_input("Data do aporte")
    valor_aporte = st.number_input(
        "Valor do aporte (R$)",
        min_value=0.0,
        step=50.0
    )

    if "aportes" not in st.session_state:
        st.session_state.aportes = {}

    if st.button("Adicionar aporte"):
        st.session_state.aportes[data_aporte] = valor_aporte
        st.success("Aporte adicionado!")


# =========================
# BOTÃO SIMULAR
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

    # Guardar resultados no estado
    st.session_state.simulado = True
    st.session_state.saldo_final = saldo_final
    st.session_state.taxa_diaria = taxa_diaria

    st.success("Simulação realizada com sucesso!")


# =========================
# RESULTADOS
# =========================
if st.session_state.get("simulado", False):

    st.subheader("📊 Resultado da simulação")

    st.write(f"Saldo final estimado: R$ {st.session_state.saldo_final:,.2f}")
    st.write(
        f"Rendimento diário estimado no final: "
        f"R$ {(st.session_state.saldo_final * st.session_state.taxa_diaria):,.2f}"
    )

    st.divider()

    # =========================
    # META DE LIQUIDEZ
    # =========================
    st.subheader("🎯 Meta de liquidez diária")

    if "meta_diaria" not in st.session_state:
        st.session_state.meta_diaria = 1.0

    meta = st.number_input(
        "Quanto você quer ganhar por dia (R$)?",
        min_value=0.5,
        step=0.5,
        key="meta_diaria"
    )

    saldo_necessario = saldo_para_meta(
        meta,
        st.session_state.taxa_diaria
    )

    st.write(
        f"Para ganhar aproximadamente R$ {meta:,.2f} por dia, "
        f"você precisaria ter cerca de R$ {saldo_necessario:,.2f} investidos, "
        f"considerando os parâmetros atuais."
    )
