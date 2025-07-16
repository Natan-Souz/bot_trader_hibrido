import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()
symbol = "NAS100"  # ou outro do log
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 10)
df = pd.DataFrame(rates)
print(df)
mt5.shutdown()