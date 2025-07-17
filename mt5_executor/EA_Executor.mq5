#property strict
#include <Trade\Trade.mqh>

input string db_path = "sinais.sqlite";
input bool trailing_ativo = true;

CTrade trade;

int id_sinal = -1;
datetime ultima_barra = 0;

//+------------------------------------------------------------------+
//| Inicialização                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   BuscarEExecutarOrdem();
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Tick - aplica trailing stop                                      |
//+------------------------------------------------------------------+
void OnTick()
{
   if (BarraNova())
   {
      // Só executa na primeira vez de cada vela
      if (!PositionSelect(Symbol()))
         BuscarEExecutarOrdem();
   }

   if (trailing_ativo)
      AplicarTrailingStop();
}

//+------------------------------------------------------------------+
//| Etapa 1: Buscar sinal pendente e marcar como em_execucao         |
//+------------------------------------------------------------------+
bool BuscarEExecutarOrdem()
{
   int db = DatabaseOpen(db_path, DATABASE_OPEN_READWRITE);
   if (db == INVALID_HANDLE)
   {
      Print("❌ Erro ao abrir banco: ", GetLastError());
      return false;
   }

   string simbolo = Symbol();
   string sql = "SELECT id, direcao, preco_entrada, sl, tp, lote FROM sinais "
                "WHERE simbolo = '" + simbolo + "' AND status = 'pendente' "
                "ORDER BY timestamp LIMIT 1";

   int stmt = DatabasePrepare(db, sql);
   if (stmt == INVALID_HANDLE)
   {
      Print("❌ Erro na consulta SQL: ", GetLastError());
      DatabaseClose(db);
      return false;
   }

   if (!DatabaseRead(stmt))
   {
      Print("ℹ️ Nenhum sinal pendente para ", simbolo);
      DatabaseFinalize(stmt);
      DatabaseClose(db);
      return false;
   }

   string direcao;
   double preco, sl, tp, lote;

   DatabaseColumnInteger(stmt, 0, id_sinal);
   DatabaseColumnText(stmt, 1, direcao);
   DatabaseColumnDouble(stmt, 2, preco);
   DatabaseColumnDouble(stmt, 3, sl);
   DatabaseColumnDouble(stmt, 4, tp);
   DatabaseColumnDouble(stmt, 5, lote);

   DatabaseFinalize(stmt);

   // Atualizar status
   string update = "UPDATE sinais SET status = 'em_execucao' WHERE id = " + IntegerToString(id_sinal);
   if (!DatabaseExecute(db, update))
   {
      Print("❌ Falha ao atualizar status: ", GetLastError());
      DatabaseClose(db);
      return false;
   }

   DatabaseClose(db);

   // Verificar se já há posição
   if (PositionSelect(simbolo))
   {
      Print("⚠️ Já existe posição para ", simbolo);
      return false;
   }

   // Executar ordem
   bool resultado = false;
   if (direcao == "buy")
      resultado = trade.Buy(lote, simbolo, preco, sl, tp);
   else if (direcao == "sell")
      resultado = trade.Sell(lote, simbolo, preco, sl, tp);

   if (resultado)
      PrintFormat("✅ Ordem executada para %s | Entrada: %.5f | SL: %.5f | TP: %.5f", simbolo, preco, sl, tp);
   else
      Print("❌ Falha na execução da ordem: ", trade.ResultRetcodeDescription());

   return resultado;
}

//+------------------------------------------------------------------+
//| Etapa 2: Trailing Stop baseado em marcos                         |
//+------------------------------------------------------------------+
void AplicarTrailingStop()
{
   if (!PositionSelect(Symbol()))
      return;

   string simbolo = Symbol();
   double preco_atual = SymbolInfoDouble(simbolo, SYMBOL_BID);
   long tipo = PositionGetInteger(POSITION_TYPE);
   double preco_entrada = PositionGetDouble(POSITION_PRICE_OPEN);
   double preco_tp = PositionGetDouble(POSITION_TP);
   double preco_sl = PositionGetDouble(POSITION_SL);

   double ponto = SymbolInfoDouble(simbolo, SYMBOL_POINT);

   // Distância total até o TP
   double alvo_dist = MathAbs(preco_tp - preco_entrada);
   double progresso = (tipo == POSITION_TYPE_BUY)
      ? preco_atual - preco_entrada
      : preco_entrada - preco_atual;

   if (progresso <= 0 || alvo_dist == 0)
      return;

   double percentual = progresso / alvo_dist;
   double novo_sl = preco_sl;

   if (percentual >= 0.95)
      novo_sl = preco_entrada + (tipo == POSITION_TYPE_BUY ? 0.75 * alvo_dist : -0.75 * alvo_dist);
   else if (percentual >= 0.80)
      novo_sl = preco_entrada + (tipo == POSITION_TYPE_BUY ? 0.50 * alvo_dist : -0.50 * alvo_dist);
   else if (percentual >= 0.75)
      novo_sl = preco_entrada + (tipo == POSITION_TYPE_BUY ? 0.25 * alvo_dist : -0.25 * alvo_dist);
   else if (percentual >= 0.50)
      novo_sl = preco_entrada;

   // Só modifica se for mais favorável
   if ((tipo == POSITION_TYPE_BUY && novo_sl > preco_sl) ||
       (tipo == POSITION_TYPE_SELL && novo_sl < preco_sl))
   {
      bool modificado = trade.PositionModify(simbolo, NormalizeDouble(novo_sl, _Digits), preco_tp);
      if (modificado)
         PrintFormat("🔄 SL ajustado para %.5f (%d%% do alvo)", novo_sl, int(percentual * 100));
      else
         Print("⚠️ Falha ao aplicar trailing stop: ", trade.ResultRetcodeDescription());
   }
}
//+------------------------------------------------------------------+
//| Verifica se formou uma nova vela                                 |
//+------------------------------------------------------------------+
bool BarraNova()
{
   datetime tempo_atual = iTime(Symbol(), PERIOD_CURRENT, 0);

   if (tempo_atual != ultima_barra)
   {
      ultima_barra = tempo_atual;
      return true;
   }
   return false;
}
