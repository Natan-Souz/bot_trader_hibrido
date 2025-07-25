import sqlite3
from datetime import datetime, timedelta
import pandas as pd

from indicators import IndicatorCalculator
from logger import Logger
from config import DB_PATH

Logger.configurar()

class MarketCycle:
    BULL = 'bull'
    BEAR = 'bear'
    NEUTRO = 'neutro'


class MarketAnalyst:
    def __init__(self, df: pd.DataFrame, df_ciclo: pd.DataFrame, simbolo: str):
        self.simbolo = simbolo
        self.df = df
        self.df_ciclo = df_ciclo
        self.db_path = DB_PATH

        self.adx_data = IndicatorCalculator.calcular_adx(df)
        self.vwap_df = IndicatorCalculator.calcular_vwap(df)
        self.vwap_diaria = self.vwap_df['vwap_diaria']
        self.topos, self.fundos = IndicatorCalculator.detectar_pivos(df_ciclo, janela=500, grupo_candles=3, distancia_minima=0.0005)

    def identificar_ciclo(self) -> str:
        if len(self.topos) < 3 or len(self.fundos) < 3:
            Logger.info("⏳ Dados insuficientes para identificar ciclo.")
            return MarketCycle.NEUTRO

        _, topo1 = self.topos[-3]
        _, topo2 = self.topos[-2]
        _, topo3 = self.topos[-1]

        _, fundo1 = self.fundos[-3]
        _, fundo2 = self.fundos[-2]
        _, fundo3 = self.fundos[-1]

        if topo1 < topo2 < topo3:
            if fundo1 < fundo2 < fundo3:
                Logger.info("📈 Ciclo de alta confirmado (3 topos e 3 fundos ascendentes)")
                return MarketCycle.BULL
            elif fundo2 < topo3:
                Logger.info("📈 Estrutura de alta em formação (topos ascendentes e fundo2 < topo3)")
                return MarketCycle.BULL

        if topo1 > topo2 > topo3 and fundo1 > fundo2 > fundo3:
            Logger.info("📉 Ciclo de baixa confirmado (3 topos e 3 fundos descendentes)")
            return MarketCycle.BEAR

        Logger.info("🔄 Movimento lateral ou indefinido")
        return MarketCycle.NEUTRO

    def _sinal_repetido(self, direcao: str, horas: int = 1) -> bool:
        limite_tempo = datetime.now() - timedelta(hours=horas)
        limite_str = limite_tempo.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM sinais
                WHERE simbolo = ? AND direcao = ?
                  AND status IN ('pendente', 'em_execucao')
                  AND timestamp >= ?
                LIMIT 1
            """, (self.simbolo, direcao, limite_str))
            return cursor.fetchone() is not None

    def verificar_sl(self, direcao: str, preco_atual: float, distancia_minima: float = 0.0005):
        if direcao == 'buy':
            candidatos = sorted(
                [(t, p) for t, p in self.fundos if p < preco_atual],
                key=lambda x: x[0], reverse=True
            )
            for _, fundo in candidatos:
                distancia = preco_atual - fundo
                if distancia >= distancia_minima:
                    return {
                        'sl': round(fundo, 5),
                        'tp': round(preco_atual + 2 * distancia, 5)
                    }

        elif direcao == 'sell':
            candidatos = sorted(
                [(t, p) for t, p in self.topos if p > preco_atual],
                key=lambda x: x[0], reverse=True
            )
            for _, topo in candidatos:
                distancia = topo - preco_atual
                if distancia >= distancia_minima:
                    return {
                        'sl': round(topo, 5),
                        'tp': round(preco_atual - 2 * distancia, 5)
                    }

        return None

    def gerar_sinal_detalhado(self, config, horario_atual: datetime.time) -> dict:
        ciclo = self.identificar_ciclo()
        adx = round(self.adx_data['ADX'].iloc[-1], 2)

        # Filtro de horário
        if not (config.horario_inicio <= horario_atual <= config.horario_fim):
            Logger.aviso("Fora de horario de operação")
            return {}

        # Filtro de ADX
        if 20 < adx < config.adx_min:
            Logger.aviso("ADX sem força | ADX: {adx}")
            return {}

        # Filtro de corpo
        candle_atual = self.df.iloc[-1]
        corpo_pct = abs(candle_atual['close'] - candle_atual['open']) / candle_atual['open'] * 100
        if corpo_pct > config.engolfo_pct_max:
            Logger.aviso("Anomalia no mercado (engolfo forte)")

            return {}

        # Filtro de distância VWAP
        preco = candle_atual['close']
        vwap = self.vwap_diaria.iloc[-1]
        if abs(preco - vwap) / vwap > 0.005:
            Logger.aviso("Preço distante da VWAP | Preço: {preco} | VWAP: {vwap}")
            return {}

        # Direção baseada no ciclo
        if ciclo == MarketCycle.BULL:
            direcao = 'buy'
        elif ciclo == MarketCycle.BEAR:
            direcao = 'sell'
        else:
            return {}

        # Verificar duplicidade
        if self._sinal_repetido(direcao):
            return {}

        # SL/TP
        sl_tp = self.verificar_sl(direcao, preco, distancia_minima=0.0003)
        if sl_tp is None:
            return {}

        timestamp = datetime.now().isoformat()
        sinal = {
            'simbolo': self.simbolo,
            'direcao': direcao,
            'preco_entrada': preco,
            'sl': sl_tp['sl'],
            'tp': sl_tp['tp'],
            'lote': 0.01,
            'ciclo': ciclo,
            'adx': adx,
            'corpo_pct': round(corpo_pct, 2),
            'status': 'pendente',
            'timestamp': timestamp,
        }

        self.salvar_sinal(sinal)
        return sinal

    def salvar_sinal(self, sinal: dict):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sinais (simbolo, direcao, preco_entrada, sl, tp, status, ciclo, adx, corpo_pct, lote, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sinal['simbolo'], sinal['direcao'], sinal['preco_entrada'],
                sinal['sl'], sinal['tp'], sinal['status'], sinal['ciclo'],
                sinal['adx'], sinal['corpo_pct'], sinal['lote'], sinal['timestamp']
            ))
            conn.commit()
