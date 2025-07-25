import sqlite3
from datetime import datetime
import MetaTrader5 as mt5

from config import DB_PATH

class SymbolConfig:
    def __init__(self, simbolo, lote, adx_min, horario_inicio, horario_fim, tipo, volume_ajustado, ponto, engolfo_pct_max=2.5):
        self.simbolo = simbolo
        self.lote = lote
        self.adx_min = adx_min
        self.horario_inicio = horario_inicio
        self.horario_fim = horario_fim
        self.tipo = tipo
        self.volume_ajustado = volume_ajustado
        self.ponto = ponto
        self.engolfo_pct_max = engolfo_pct_max
        self.timeframe = mt5.TIMEFRAME_M5         # Timeframe principal de operação
        self.timeframe_ciclo = mt5.TIMEFRAME_M30  # Timeframe para identificar o ciclo


class SymbolManager:
    def __init__(self):
        self.simbolos = {}

    def adicionar_simbolo(self, config: SymbolConfig):
        self.simbolos[config.simbolo] = config

    def obter_configuracao(self, simbolo: str) -> SymbolConfig:
        return self.simbolos.get(simbolo, None)

    def carregar_do_banco(self, caminho_banco=DB_PATH):
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT simbolo, tipo, descricao, path, spread, volume_ajustado FROM ativos WHERE observando = 1")

            for row in cursor.fetchall():
                simbolo, tipo, descricao, path, spread, volume = row

                ponto = 0.0001
                if "JPY" in simbolo:
                    ponto = 0.01

                config = SymbolConfig(
                    simbolo=simbolo,
                    lote=0.01,
                    adx_min=20,
                    horario_inicio=datetime.strptime("00:00", "%H:%M").time(),
                    horario_fim=datetime.strptime("23:59", "%H:%M").time(),
                    tipo=tipo,
                    volume_ajustado=float(volume),
                    ponto=ponto,
                    engolfo_pct_max=2.5
                )
                self.adicionar_simbolo(config)

        except Exception as e:
            print(f"Erro ao carregar configurações do banco: {e}")

        finally:
            conn.close()
