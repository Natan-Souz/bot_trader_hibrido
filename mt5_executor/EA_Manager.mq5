//+------------------------------------------------------------------+
//| EA_Manager.mq5 - Abre gráficos automaticamente com EA aplicado  |
//+------------------------------------------------------------------+
#property strict

input string db_path = "sinais.sqlite";     // Caminho do banco SQLite
input string template_nome = "grafico-basico-robo.tpl"; // Template com EA_Executor
input int intervalo_checagem = 60;           // Intervalo em segundos

string ativos[];

//+------------------------------------------------------------------+
//| Inicialização                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   CarregarAtivosDoBanco();
   AbrirGraficosNecessarios();
   EventSetTimer(intervalo_checagem);
   Print("✅ EA_Manager iniciado. Ativos carregados: ", ArraySize(ativos));
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Finalização                                                      |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("🛑 EA_Manager finalizado.");
}

//+------------------------------------------------------------------+
//| Timer executado periodicamente                                  |
//+------------------------------------------------------------------+
void OnTimer()
{
   CarregarAtivosDoBanco();
   AbrirGraficosNecessarios();
}

//+------------------------------------------------------------------+
//| Consulta ativos com observando=1 diretamente no SQLite          |
//+------------------------------------------------------------------+
void CarregarAtivosDoBanco()
{
   int db = DatabaseOpen(db_path, 1); // 1 = leitura
   if (db == INVALID_HANDLE)
   {
      Print("❌ Erro ao abrir banco: ", GetLastError());
      return;
   }

   string sql = "SELECT simbolo FROM ativos WHERE observando = 1";
   int res = DatabasePrepare(db, sql);
   if (res == INVALID_HANDLE)
   {
      Print("❌ Erro na consulta SQL: ", GetLastError());
      DatabaseClose(db);
      return;
   }

   ArrayFree(ativos);
   while (DatabaseRead(res))
   {
      string simbolo;
      DatabaseColumnText(res, 0, simbolo);
      ArrayResize(ativos, ArraySize(ativos) + 1);
      ativos[ArraySize(ativos) - 1] = simbolo;
   }

   DatabaseFinalize(res);
   DatabaseClose(db);
}

//+------------------------------------------------------------------+
//| Abre gráficos e aplica template                                  |
//+------------------------------------------------------------------+
void AbrirGraficosNecessarios()
{
   for (int i = 0; i < ArraySize(ativos); i++)
   {
      string simbolo = ativos[i];
      bool aberto = false;

      long chart_id = ChartFirst();
      while (chart_id >= 0)
      {
         if (ChartSymbol(chart_id) == simbolo)
         {
            aberto = true;
            break;
         }
         chart_id = ChartNext(chart_id);
      }

      if (!aberto)
      {
         long novo_chart = ChartOpen(simbolo, PERIOD_M5);
         if (novo_chart > 0)
         {
            ChartApplyTemplate(novo_chart, template_nome);
            Print("📈 Gráfico aberto e template aplicado: ", simbolo);
         }
         else
         {
            Print("⚠️ Falha ao abrir gráfico para: ", simbolo);
         }
      }
   }
}
   