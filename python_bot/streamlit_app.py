import streamlit as st
import sqlite3
import pandas as pd
from config import DB_PATH
import plotly.graph_objects as go
import MetaTrader5 as mt5

# ========================
# 🎛️ CONFIGURAÇÃO INICIAL
# ========================
st.set_page_config(page_title="Painel do Robô Trader", layout="wide")
st.title("🤖 Painel do Robô Trader Híbrido")

# ========================
# 📌 NAVEGAÇÃO LATERAL
# ========================
st.sidebar.title("🔧 Navegação")
aba = st.sidebar.selectbox("Escolha a seção:", [
    "📋 Sinais Gerados",
    "📈 Gráfico do Sinal",
    "📊 Ativos Observáveis",
    "🧠 Diagnóstico",
    "⚙️ Configurações do Robô"
])

# ========================
# 📋 ABA 1: SINAIS GERADOS
# ========================
if aba == "📋 Sinais Gerados":
    st.subheader("📋 Lista de Sinais Gerados")

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM sinais ORDER BY timestamp DESC LIMIT 500", conn)

    # Filtros
    col1, col2, col3 = st.columns(3)
    simbolos = ["Todos"] + sorted(df['simbolo'].unique())
    status_options = ["Todos"] + sorted(df['status'].unique())
    datas = pd.to_datetime(df['timestamp'])

    with col1:
        simbolo_sel = st.selectbox("Filtrar por símbolo", simbolos)
    with col2:
        status_sel = st.selectbox("Filtrar por status", status_options)
    with col3:
        data_min = st.date_input("A partir de:", datas.min().date())

    # Aplicar filtros
    if simbolo_sel != "Todos":
        df = df[df['simbolo'] == simbolo_sel]
    if status_sel != "Todos":
        df = df[df['status'] == status_sel]
    df = df[pd.to_datetime(df['timestamp']).dt.date >= data_min]

    st.dataframe(df, use_container_width=True)

# ========================
# 📈 ABA 2: GRÁFICO DO SINAL
# ========================
elif aba == "📈 Gráfico do Sinal":
    st.subheader("📈 Visualização do Sinal Selecionado")

    with sqlite3.connect(DB_PATH) as conn:
        sinais_df = pd.read_sql_query("SELECT * FROM sinais ORDER BY timestamp DESC LIMIT 100", conn)

    if sinais_df.empty:
        st.warning("Nenhum sinal disponível para exibição.")
    else:
        sinal_id = st.selectbox("Selecione um sinal:", sinais_df.index,
            format_func=lambda idx: f"{sinais_df.loc[idx, 'simbolo']} - {sinais_df.loc[idx, 'direcao']} @ {sinais_df.loc[idx, 'timestamp'][:16]}"
        )

        sinal = sinais_df.loc[sinal_id]
        simbolo = sinal['simbolo']
        preco_entrada = sinal['preco_entrada']
        sl = sinal['sl']
        tp = sinal['tp']

        # Obtém candles do ativo
        mt5.initialize()
        rates = mt5.copy_rates_from_pos(simbolo, mt5.TIMEFRAME_M5, 0, 100)
        mt5.shutdown()

        if rates is None or len(rates) == 0:
            st.error("Não foi possível obter dados do ativo no MetaTrader.")
        else:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            entrada_candle = df.iloc[(df['close'] - preco_entrada).abs().argsort()[:1]]
            entrada_time = entrada_candle.index[0]
            entrada_preco = preco_entrada

            # Gráfico
            fig = go.Figure(data=[
                go.Candlestick(
                    x=df.index,
                    open=df['open'], high=df['high'],
                    low=df['low'], close=df['close'],
                    name='Candles'
                ),
                go.Scatter(x=df.index, y=[preco_entrada]*len(df), mode='lines', name='Entrada',
                           line=dict(color='blue', dash='dash')),
                go.Scatter(x=df.index, y=[sl]*len(df), mode='lines', name='Stop Loss',
                           line=dict(color='red', dash='dot')),
                go.Scatter(x=df.index, y=[tp]*len(df), mode='lines', name='Take Profit',
                           line=dict(color='green', dash='dot')),
                go.Scatter(x=[entrada_time], y=[entrada_preco], mode='markers', name='📍 Entrada',marker=dict(size=12, color='blue', symbol='triangle-up')
),
            ])

            fig.update_layout(
                title=f"{simbolo} - {sinal['direcao'].upper()}",
                xaxis_title="Tempo",
                yaxis_title="Preço",
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

# ========================
# 📊 ABA 3: ATIVOS OBSERVADOS
# ========================
elif aba == "📊 Ativos Observáveis":
    st.subheader("📊 Lista de Ativos Observados")

    with sqlite3.connect(DB_PATH) as conn:
        ativos_df = pd.read_sql_query("SELECT * FROM ativos WHERE observando = 1", conn)

    if ativos_df.empty:
        st.info("Nenhum ativo está sendo observado no momento.")
    else:
        st.dataframe(ativos_df, use_container_width=True)

# ========================
# 🧠 ABA 4: DIAGNÓSTICO (em breve)
# ========================
elif aba == "🧠 Diagnóstico":
    st.subheader("🧠 Diagnóstico dos ativos")
    st.info("Esta funcionalidade será implementada nas próximas etapas.")

# ========================
# ⚙️ ABA 5: CONFIGURAÇÕES (em breve)
# ========================
elif aba == "⚙️ Configurações do Robô":
    st.subheader("⚙️ Parâmetros da Estratégia")
    st.info("Em breve você poderá ajustar os parâmetros do robô aqui.")
