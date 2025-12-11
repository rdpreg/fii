import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date

# ------------------------------------------------------------
# Configuração inicial
# ------------------------------------------------------------

st.set_page_config(
    page_title="Dashboard Carteira de FIIs - Convexa",
    layout="wide"
)

st.title("Carteiras de FIIs dos clientes")
st.markdown(
    """
Acompanhe a performance, a geração de renda e o rebalanceamento das carteiras de FIIs dos seus clientes.
"""
)

# ------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------

def carregar_arquivo(uploaded_file):
    """Lê CSV ou Excel e retorna DataFrame."""
    if uploaded_file is None:
        return None

    nome = uploaded_file.name.lower()
    if nome.endswith(".csv"):
        df = pd.read_csv(uploaded_file, sep=";", decimal=",")
    elif nome.endswith(".xlsx") or nome.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Formato de arquivo não suportado. Use CSV, XLSX ou XLS.")
        return None

    return df


def criar_exemplo_df():
    """Cria uma base de exemplo para testar o layout."""
    hoje = date.today()
    dados = [
        {
            "cliente": "João da Silva",
            "assessor": "Pedro",
            "patrimonio_fiis": 185430.00,
            "rentabilidade_12m": 0.092,
            "dividendos_12m": 12840.00,
            "ultimo_rebalanceamento": date(2025, 2, 15),
            "proximo_rebalanceamento": date(2025, 8, 15),
        },
        {
            "cliente": "Maria Fernandes",
            "assessor": "Vanessa",
            "patrimonio_fiis": 92710.00,
            "rentabilidade_12m": 0.047,
            "dividendos_12m": 5320.00,
            "ultimo_rebalanceamento": date(2024, 1, 10),
            "proximo_rebalanceamento": date(2024, 7, 10),
        },
        {
            "cliente": "Carlos Pereira",
            "assessor": "Luciano",
            "patrimonio_fiis": 302500.00,
            "rentabilidade_12m": 0.118,
            "dividendos_12m": 24890.00,
            "ultimo_rebalanceamento": date(2025, 1, 5),
            "proximo_rebalanceamento": date(2025, 7, 5),
        },
        {
            "cliente": "Ana Costa",
            "assessor": "Vanessa",
            "patrimonio_fiis": 154200.00,
            "rentabilidade_12m": 0.063,
            "dividendos_12m": 10340.00,
            "ultimo_rebalanceamento": date(2024, 10, 1),
            "proximo_rebalanceamento": date(2025, 4, 1),
        },
    ]
    df = pd.DataFrame(dados)
    return df


def garantir_colunas_padrao(df):
    """
    Ajusta o DataFrame para garantir colunas esperadas, 
    se os nomes vierem um pouco diferentes.
    """
    col_map = {
        "cliente": ["cliente", "Cliente", "nome_cliente", "Nome"],
        "assessor": ["assessor", "Assessor"],
        "patrimonio_fiis": ["patrimonio_fiis", "Patrimonio_FIIs", "Patrimônio FIIs", "patrimonio_fundo_imobiliario"],
        "rentabilidade_12m": ["rentabilidade_12m", "Rentabilidade_12m", "Rentabilidade 12m", "rentab_12m"],
        "dividendos_12m": ["dividendos_12m", "Dividendos_12m", "Dividendos 12m", "div_12m"],
        "ultimo_rebalanceamento": ["ultimo_rebalanceamento", "Último rebalanceamento", "ultimo_reb"],
        "proximo_rebalanceamento": ["proximo_rebalanceamento", "Próximo rebalanceamento", "proximo_reb"],
    }

    df_cols_lower = {c.lower(): c for c in df.columns}

    nova = {}
    for alvo, alternativas in col_map.items():
        for alt in alternativas:
            alt_lower = alt.lower()
            if alt_lower in df_cols_lower:
                nova[alvo] = df[df_cols_lower[alt_lower]]
                break

    if len(nova) < len(col_map):
        faltando = [k for k in col_map.keys() if k not in nova]
        st.warning(
            "Algumas colunas esperadas não foram encontradas na base enviada: "
            + ", ".join(faltando)
            + ". Será usado o exemplo de dados."
        )
        return criar_exemplo_df()

    df_padrao = pd.DataFrame(nova)

    # Garantir tipos de data
    for col_data in ["ultimo_rebalanceamento", "proximo_rebalanceamento"]:
        df_padrao[col_data] = pd.to_datetime(df_padrao[col_data]).dt.date

    return df_padrao


def calcular_status_rebalanceamento(df, dias_alerta=30):
    """
    Define o status de rebalanceamento com base na data de hoje e na próxima data.
    - Atrasado: próxima data já passou
    - Próximo: falta menos ou igual a dias_alerta dias
    - Em dia: caso contrário
    """
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
# Upload de arquivo
# ------------------------------------------------------------

st.sidebar.header("Base de dados")
uploaded_file = st.sidebar.file_uploader(
    "Envie a base de Carteiras de FIIs (CSV ou Excel)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    df_raw = carregar_arquivo(uploaded_file)
    if df_raw is not None:
        df = garantir_colunas_padrao(df_raw)
    else:
        df = criar_exemplo_df()
else:
    st.info("Nenhum arquivo enviado. Usando base de exemplo para demonstração.")
    df = criar_exemplo_df()

df = calcular_status_rebalanceamento(df)

# ------------------------------------------------------------
# Filtros principais (topo)
# ------------------------------------------------------------

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    busca_cliente = st.text_input("Buscar cliente (nome ou parte do nome):")

with col2:
    assessores = sorted(df["assessor"].dropna().unique().tolist())
    assessor_sel = st.multiselect("Filtrar por assessor", options=assessores, default=assessores)

with col3:
    status_opcoes = ["Em dia", "Próximo", "Atrasado", "Sem data"]
    status_sel = st.multiselect("Status de rebalanceamento", options=status_opcoes, default=status_opcoes)

# Filtro por busca de cliente
df_filtrado = df.copy()

if busca_cliente:
    filtro = df_filtrado["cliente"].str.contains(busca_cliente, case=False, na=False)
    df_filtrado = df_filtrado[filtro]

# Filtro por assessor
df_filtrado = df_filtrado[df_filtrado["assessor"].isin(assessor_sel)]

# Filtro por status
df_filtrado = df_filtrado[df_filtrado["status_rebalanceamento"].isin(status_sel)]

# ------------------------------------------------------------
# KPIs gerais
# ------------------------------------------------------------

patrimonio_total = df_filtrado["patrimonio_fiis"].sum()
dividendos_total_12m = df_filtrado["dividendos_12m"].sum()

# Média ponderada de rentabilidade: ponderar pelo patrimonio_fiis
if patrimonio_total > 0:
    rentab_media_pond = (df_filtrado["rentabilidade_12m"] * df_filtrado["patrimonio_fiis"]).sum() / patrimonio_total
else:
    rentab_media_pond = np.nan

# Contagem por status
contagem_status = df_filtrado["status_rebalanceamento"].value_counts()
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
    st.markdown("**Rentabilidade média 12m (ponderada)**")
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
# Preparar tabela para exibição
# ------------------------------------------------------------

df_exibir = df_filtrado.copy()

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

st.dataframe(
    df_exibir,
    use_container_width=True
)

# ------------------------------------------------------------
# Detalhe simples ao clicar (opcional: via selectbox)
# ------------------------------------------------------------

st.markdown("---")
st.subheader("Detalhe de cliente (visual simples)")

clientes_lista = df_filtrado["cliente"].unique().tolist()
if clientes_lista:
    cliente_detalhe = st.selectbox("Selecione um cliente para ver o resumo:", options=clientes_lista)

    df_cli = df_filtrado[df_filtrado["cliente"] == cliente_detalhe].iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Cliente**")
        st.write(df_cli["cliente"])
        st.markdown("**Assessor**")
        st.write(df_cli["assessor"])

    with c2:
        st.markdown("**Patrimônio em FIIs**")
        st.write(formatar_moeda(df_cli["patrimonio_fiis"]))
        st.markdown("**Rentabilidade 12m**")
        st.write(formatar_percentual(df_cli["rentabilidade_12m"]))

    with c3:
        st.markdown("**Último rebalanceamento**")
        st.write(
            df_cli["ultimo_rebalanceamento"].strftime("%d/%m/%Y")
            if not pd.isna(df_cli["ultimo_rebalanceamento"])
            else "n.d."
        )
        st.markdown("**Próximo rebalanceamento**")
        st.write(
            df_cli["proximo_rebalanceamento"].strftime("%d/%m/%Y")
            if not pd.isna(df_cli["proximo_rebalanceamento"])
            else "n.d."
        )
        st.markdown("**Status de rebalanceamento**")
        st.write(df_cli["status_rebalanceamento"])
else:
    st.info("Nenhum cliente após os filtros aplicados.")
