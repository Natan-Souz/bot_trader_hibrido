import time
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd

from symbol_manager import SymbolManager
from strategy import MarketAnalyst
from market_scanner import MarketScanner, ScannerConfig

# ================================
# 🔧 CONFIGURAÇÕES DE ENTRADA
# ================================

QTD_FOREX   = 2
QTD_INDICES = 0
QTD_CRYPTO  = 10
QTD_ACOES  = 0
SPREAD_MAX  = 50
INTERVALO_SCANNER = timedelta(hours=1)
INTERVALO_ESTRATEGIA = timedelta(minutes=5)
N_CANDLES_ANALISE = 200
N_CANDLES_CICLO = 100

# ================================
# 📥 OBTENÇÃO DE DADOS
# ================================

def obter_candles(simbolo: str, timeframe: int, n_barras: int) -> pd.DataFrame:
    mt5.initialize()
    rates = mt5.copy_rates_from_pos(simbolo, timeframe, 0, n_barras)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

# ================================
# 🔍 EXECUÇÃO DO MARKET SCANNER
# ================================

def executar_market_scanner():
    print("🔍 Executando market scanner...")
    config = ScannerConfig(
        max_forex=QTD_FOREX,
        max_indices=QTD_INDICES,
        max_crypto=QTD_CRYPTO,
        max_acoes = QTD_ACOES,
        spread_maximo=SPREAD_MAX
    )
    scanner = MarketScanner(config)
    scanner.carregar_dados_mt5()
    scanner.salvar_no_banco()
    print("📊 Market scanner finalizado.")

# ================================
# 🤖 EXECUÇÃO DAS ESTRATÉGIAS
# ================================

def executar_estrategias():
    print("📈 Executando geração de sinais...")

    symbol_manager = SymbolManager()
    symbol_manager.carregar_do_banco()
    ativos_config = list(symbol_manager.simbolos.values())

    for config in ativos_config:
        try:
            simbolo = config.simbolo
            print(f"\n🧠 Processando ativo: {simbolo}")

            df_principal = obter_candles(simbolo, config.timeframe, N_CANDLES_ANALISE)
            df_ciclo = obter_candles(simbolo, config.timeframe_ciclo, N_CANDLES_CICLO)

            if df_principal.empty:
                print(f"⚠️ Sem candles principais para {simbolo}")
                continue

            if df_ciclo.empty:
                print(f"⚠️ Sem candles de ciclo para {simbolo}")
                continue

            analista = MarketAnalyst(df_principal, df_ciclo, simbolo)
            sinal = analista.gerar_sinal_detalhado(config, datetime.now().time())

            if sinal:
                print(f"✅ Sinal gerado para {simbolo}: {sinal['direcao']} @ {sinal['preco_entrada']}")
            else:
                print(f"ℹ️ Sem sinal gerado para {simbolo}")

        except Exception as e:
            print(f"❌ Erro ao processar {config.simbolo}: {e}")

    print("\n🏁 Geração de sinais finalizada.")

# ================================
# 🚀 EXECUÇÃO PRINCIPAL
# ================================

if __name__ == "__main__":

    proxima_execucao_scanner = datetime.now()
    ultima_execucao_estrategia = datetime.now() - INTERVALO_ESTRATEGIA

    try:
        while True:
            agora = datetime.now()

            if agora >= proxima_execucao_scanner:
                executar_market_scanner()
                proxima_execucao_scanner = agora + INTERVALO_SCANNER

            if agora - ultima_execucao_estrategia >= INTERVALO_ESTRATEGIA:
                executar_estrategias()
                ultima_execucao_estrategia = agora

            time.sleep(5)

    finally:
        mt5.shutdown()
        print("🛑 Conexão com MetaTrader 5 encerrada.")
