import pandas as pd 
import numpy

class IndicatorCalculator:

    @staticmethod
    def calcular_vwap(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("O DataFrame precisa ter um índice ou coluna datetime.")

        df = df.sort_index()

        df['tp'] = (df['high'] + df['low'] + df['close']) / 3
        df['data'] = df.index.date
        df['semana'] = df.index.to_series().dt.to_period('W').apply(lambda p: p.start_time.date())

        df['vwap_diaria'] = np.nan
        df['vwap_semanal'] = np.nan

        soma_tpv_dia = 0
        soma_vol_dia = 0
        dia_atual = None

        soma_tpv_semana = 0
        soma_vol_semana = 0
        semana_atual = None

        for i, row in df.iterrows():
            vol = row['tick_volume'] if row['tick_volume'] > 0 else row.get('volume', 0)

            if dia_atual != row['data']:
                soma_tpv_dia = 0
                soma_vol_dia = 0
                dia_atual = row['data']

            if semana_atual != row['semana']:
                soma_tpv_semana = 0
                soma_vol_semana = 0
                semana_atual = row['semana']

            tpv = row['tp'] * vol
            soma_tpv_dia += tpv
            soma_vol_dia += vol
            df.at[i, 'vwap_diaria'] = soma_tpv_dia / soma_vol_dia if soma_vol_dia > 0 else np.nan

            soma_tpv_semana += tpv
            soma_vol_semana += vol
            df.at[i, 'vwap_semanal'] = soma_tpv_semana / soma_vol_semana if soma_vol_semana > 0 else np.nan

        return df[['vwap_diaria', 'vwap_semanal']]