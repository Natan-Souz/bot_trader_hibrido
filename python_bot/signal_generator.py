import pandas as pd
from datetime import datetime
import sqlite3
import MetaTrader5 as mt5

from strategy import MarketAnalyst
from symbol_manager import SymbolManager

def obter_ativos_observados(banco_path: str = "C:\\Users\\walte\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075\\MQL5\\Files\\sinais.sqlite") -> list:
    conn = sqlite3.connect(banco_path)
    cursor = conn.cursor()
    cursor.execute("SELECT simbolo FROM ativos WHERE observando = 1")
    ativos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ativos


def obter_candles(symbol: str, timeframe: int, barras: int = 1000) -> pd.DataFrame:
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, barras)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


def executar_geracao_sinais():
    if not mt5.initialize():
        return

    symbol_manager = SymbolManager()
    ativos = obter_ativos_observados()

    for simbolo in ativos:
        config = symbol_manager.obter_configuracao(simbolo)
        if not config:
            continue

        df = obter_candles(simbolo, config.timeframe, barras=200)
        df_ciclo = obter_candles(simbolo, config.timeframe_ciclo, barras=200)

        if df.empty or df_ciclo.empty:
            continue

        analista = MarketAnalyst(df, df_ciclo, simbolo)
        sinal = analista.gerar_sinal_detalhado(config, datetime.now().time())

        if sinal:
            print.info(f"{simbolo}: sinal gerado com sucesso")
        else:
            print.info(f"{simbolo}: nenhum sinal gerado")

    mt5.shutdown()


if __name__ == "__main__":
    executar_geracao_sinais()
