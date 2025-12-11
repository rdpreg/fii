import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

st.set_page_config(
    page_title="Carteiras de FIIs - Convexa",
    layout="wide"
)

st.title("Carteiras de FIIs dos clientes")
st.markdown(
    """
Versão V1 apenas com exemplo de dados,
KPIs principais e tabela por cliente.
"""
)

# ------------------------------------------------------------
# 1. Base de exemplo bem simples
# ------------------------------------------------------------

def criar_exemplo_df():
    dados = [
        {
            "cliente": "João da Silva",
            "assessor": "Pedro",
            "patrimonio_fiis": 185_430.00,
            "rentabilidade_12m": 0.092,
            "dividendos_12m": 12_840.00,
            "ultimo_rebalanceamento": date(2025, 2, 15),
            "proximo_rebalanceamento": date(2025, 8, 15),
        },
        {
            "cliente": "Maria Fernandes",
            "assessor": "Vanessa",
            "patrimonio_fiis": 92_710.00,
            "rentabilidade_12m": 0.047,
            "dividendos_12m": 5_320.00,
            "ultimo_rebalanceamento": date(2024, 1, 10),
            "proximo_rebalanceamento": date(2024, 7, 10),
        },
        {
            "cliente": "Carlos Pereira",
            "assessor": "Luciano",
            "patrimonio_fiis": 302_500.00,
            "rentabilidade_12m": 0.118,
            "dividendos_12m": 24_890.00,
            "ultimo_rebalanceamento": date(2025, 1, 5),
            "proximo_rebalanceamento": date(2025, 7, 5),
        },
        {
            "cliente": "Ana Costa",
            "assessor": "Vanessa",
            "patrimonio_fiis": 154_200.00,
            "rentabilidade_12m": 0.063,
            "dividendos_12m": 10_340.00,
            "ultimo_rebalanceamento": date(2024, 10, 1),
            "proximo_rebalanceamento": date(2025, 4, 1),
        },
    ]
    return pd.DataFrame(dados)

df = criar_exemplo_df()

# ------------------------------------------------------------
# 2. Funções auxiliares
# ------------------------------------------------------------

def calcular_status_rebalanceamento(df, dias_alerta=30):
    hoje = date.today()
    status = []

    for _, row in df.iterrows():
        prox = row["proximo_rebalanceamento"]

        if pd.isna(prox):
            status.append("Sem data")
            continue

        if prox < hoje:
            status.append("Atrasado")
        else:
            delta = (prox - hoje).days
            if delta <= dias_alerta:
                status.append("Próximo")
            else:
                status.append("Em dia")

    df["status_rebalanceamento"] = status
    return df

def formatar_moeda(valor):
    if pd.isna(valor):
        return ""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual(valor):
    if pd.isna(valor):
        return ""
    return f"{valor * 100:.2f} %"


# ------------------------------------------------------------
# 3. Aplica status de rebalanceamento
# ------------------------------------------------------------

df = calcular_status_rebalanceamento(df)

# ------------------------------------------------------------
# 4. KPIs simples
# ------------------------------------------------------------

patrimonio_total = df["patrimonio_fiis"].sum()
dividendos_total_12m = df["dividendos_12m"].sum()

if patrimonio_total > 0:
    rentab_media_pond = (df["rentabilidade_12m"] * df["patrimonio_fiis"]).sum() / patrimonio_total
else:
    rentab_media_pond = np.nan

contagem_status = df["status_rebalanceamento"].value_counts()
em_dia = contagem_status.get("Em dia", 0)
proximo = contagem_status.get("Próximo", 0)
atrasado = contagem_status.get("Atrasado", 0)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown("**Patrimônio total em FIIs**")
    st.markdown(f"<h3>{formatar_moeda(patrimonio_total)}</h3>", unsafe_allow_html=True)

with kpi2:
    st.markdown("**Dividendos nos últimos 12 meses**")
    st.markdown(f"<h3>{formatar_moeda(dividendos_total_12m)}</h3>", unsafe_allow_html=True)

with kpi3:
    st.markdown("**Rentabilidade média 12m ponderada**")
    if pd.notna(rentab_media_pond):
        st.markdown(f"<h3>{formatar_percentual(rentab_media_pond)}</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3>n.d.</h3>", unsafe_allow_html=True)

with kpi4:
    st.markdown("**Status de rebalanceamento**")
    st.markdown(
        f"""
        <ul>
            <li>Em dia: <b>{em_dia}</b></li>
            <li>Próximo: <b>{proximo}</b></li>
            <li>Atrasado: <b>{atrasado}</b></li>
        </ul>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ------------------------------------------------------------
# 5. Tabela principal
# ------------------------------------------------------------

df_exibir = df.copy()

df_exibir["Patrimônio FIIs"] = df_exibir["patrimonio_fiis"].apply(formatar_moeda)
df_exibir["Rentabilidade 12m"] = df_exibir["rentabilidade_12m"].apply(formatar_percentual)
df_exibir["Dividendos 12m"] = df_exibir["dividendos_12m"].apply(formatar_moeda)
df_exibir["Último rebalanceamento"] = df_exibir["ultimo_rebalanceamento"].apply(
    lambda d: d.strftime("%d/%m/%Y") if not pd.isna(d) else ""
)
df_exibir["Próximo rebalanceamento"] = df_exibir["proximo_rebalanceamento"].apply(
    lambda d: d.strftime("%d/%m/%Y") if not pd.isna(d) else ""
)

colunas_ordem = [
    "cliente",
    "assessor",
    "Patrimônio FIIs",
    "Rentabilidade 12m",
    "Dividendos 12m",
    "Último rebalanceamento",
    "Próximo rebalanceamento",
    "status_rebalanceamento",
]

df_exibir = df_exibir[colunas_ordem]
df_exibir = df_exibir.rename(columns={
    "cliente": "Cliente",
    "assessor": "Assessor",
    "status_rebalanceamento": "Status rebalanceamento",
})

st.subheader("Carteiras de FIIs por cliente")
st.dataframe(df_exibir, use_container_width=True)
