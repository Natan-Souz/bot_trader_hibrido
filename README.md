# 🤖 Bot Trader Híbrido (Python + MetaTrader 5)

Este projeto implementa um robô trader híbrido que combina análise técnica em **Python** com execução de ordens via **MetaTrader 5 (MQL5)**.  
A comunicação ocorre por meio de um banco de dados **SQLite**, permitindo controle centralizado e rastreável das decisões.

---

## ⚙️ Arquitetura do Projeto

```
bot_trader_hibrido/
├── python_bot/           # Lógica de análise de mercado e geração de sinais
│   ├── indicators.py
│   ├── strategy.py
│   ├── mt5_utils.py
│   ├── market_scanner.py
│   ├── logger.py
│   └── signal_generator.py
│
├── mt5_executor/         # Expert Advisors em MQL5 que executam ordens no MT5
│   ├── EA_Manager.mq5
│   ├── EA_Executor.mq5
│   └── Ordem_Fetcher.mq5
│
├── data/                 # Banco de dados central e arquivos auxiliares
│   ├── sinais.sqlite
│   └── ativos_observados.json
│
├── scripts/              # Scripts utilitários (ex: abrir gráficos com template)
│   └── abrir_graficos.mq5
│
├── logs/                 # Logs de operação (não versionados)
├── .gitignore
└── README.md
```

---

## 🎯 Objetivo

Desenvolver um robô autônomo que:

- Monitora ativos relevantes em tempo real;
- Gera sinais de entrada baseados em indicadores técnicos;
- Executa ordens com controle de risco dinâmico;
- Utiliza um banco de dados como ponto central de decisão;
- Permite expansão com IA, backtests e dashboards.

---

## 🧩 Módulos e Responsabilidades

| Módulo                 | Responsabilidade                                           |
|------------------------|------------------------------------------------------------|
| `market_scanner.py`    | Coleta e classifica ativos disponíveis                     |
| `strategy.py`          | Define regras de entrada (Price Action, VWAP, ADX, etc.)   |
| `mt5_utils.py`         | Interface com o MetaTrader 5 via Python                    |
| `EA_Manager.mq5`       | Mantém os gráficos dos ativos abertos com os EAs anexados  |
| `EA_Executor.mq5`      | Executa ordens com trailing stop e controle de lote        |
| `EA_Query.mq5`         | Busca os ativos mais volateis para entrar em observação    |
| `Ordem_Fetcher.mq5`    | Busca sinais no banco e atualiza o status da execução      |
---

## 🗃️ Banco de Dados (SQLite)

As informações operacionais são centralizadas no banco `sinais.sqlite`, com tabelas como:

- `ativos`: ativos sob observação.
- `sinais`: sinais gerados pelo Python.
- `resultados`: desempenho das ordens (TP, SL, lucro/prejuízo).
- `configuracoes`: parâmetros por ativo (risco, horário, etc.).

---

## 🖥️ Como Usar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/bot_trader_hibrido.git
cd bot_trader_hibrido
```

### 2. Crie o ambiente virtual (recomendado)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate.bat       # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute os módulos Python

- `main.py` → Executa o fluxo total do projeto.

### 5. Configure o MetaTrader 5

- Instale os arquivos `.mq5` em:
  ```
  C:\Users\SeuUsuario\AppData\Roaming\MetaQuotes\Terminal\...\MQL5\Experts\
  ```
- Compile via MetaEditor.
- Salve o template do grafico com o `EA_Executor.mq5``sobre o gráfico.
- Execute `EA_Manager.mq5` para abrir os gráficos automaticamente.
- Execute `EA_Query.mq5` para scanear os ativos.
- Certifique-se de que "AutoTrading" está ativado.

---

## 📌 Observações

- Os logs são gravados na pasta `/logs`, fora do banco.
- O projeto segue arquitetura modular com divisão clara entre análise, execução e monitoramento.
- Todas as decisões operacionais (inclusive sinais e configurações) ficam no banco SQLite.

---

## 📅 Planejamento e Etapas

Cada etapa do projeto possui objetivo próprio e pode ser rastreada via [issues](https://github.com/seu-usuario/bot_trader_hibrido/issues) ou no planejamento compartilhado:

1. Estruturação do projeto
2. Scanner e classificação de ativos
3. Geração de sinais
4. Execução via EA
5. Registro de performance
6. Expansão com IA e análise de métricas

---

## 📄 Licença

Este projeto é de uso pessoal e acadêmico.  
Para uso comercial, entre em contato com o autor.

---
