from datetime import datetime, timedelta
import os
import MetaTrader5 as mt5

from symbol_manager import SymbolManager
from strategy import MarketAnalyst
from signal_generator import obter_candles, obter_ativos_observados
from market_scanner import MarketScanner, ScannerConfig


CAMINHO_ULTIMA_CHECAGEM = "data/ultima_checagem.txt"


def deve_executar_market_scanner():
    if not os.path.exists(CAMINHO_ULTIMA_CHECAGEM):
        return True

    with open(CAMINHO_ULTIMA_CHECAGEM, "r") as f:
        conteudo = f.read().strip()
        try:
            ultima = datetime.fromisoformat(conteudo)
            return datetime.now() - ultima > timedelta(minutes=30)
        except Exception:
            return True


def atualizar_ultima_checagem():
    with open(CAMINHO_ULTIMA_CHECAGEM, "w") as f:
        f.write(datetime.now().isoformat())


def executar_fluxo():
    print("🚀 Iniciando geração de sinais...")

    if not mt5.initialize():
        print("❌ Falha ao iniciar o MetaTrader 5")
        return

    # Etapa 1: Scanner de mercado (a cada 30 min)
    if deve_executar_market_scanner():
        print("🔍 Executando market scanner...")
        scanner = MarketScanner(ScannerConfig())
        scanner.carregar_dados_mt5()
        scanner.salvar_no_banco()
        atualizar_ultima_checagem()
        print("📊 Market scanner finalizado.")

    # Etapa 2: Geração de sinais
    symbol_manager = SymbolManager()
    symbol_manager.carregar_do_banco()

    ativos = obter_ativos_observados()

    for simbolo in ativos:
        config = symbol_manager.obter_configuracao(simbolo)
        if not config:
            print(f"⚠️ Configuração ausente para {simbolo}")
            continue

        df = obter_candles(simbolo, config.timeframe, barras=500)
        df_ciclo = obter_candles(simbolo, config.timeframe_ciclo, barras=1000)

        if df.empty or df_ciclo.empty:
            print(f"⚠️ Dados insuficientes para {simbolo}")
            continue

        analista = MarketAnalyst(df, df_ciclo, simbolo)
        sinal = analista.gerar_sinal_detalhado(config, datetime.now().time())

        if sinal:
            print(f"✅ Sinal gerado para {simbolo}")
        else:
            print(f"🕵️ Nenhum sinal para {simbolo}")

    mt5.shutdown()
    print("🏁 Geração de sinais finalizada.")


if __name__ == "__main__":
    executar_fluxo()
