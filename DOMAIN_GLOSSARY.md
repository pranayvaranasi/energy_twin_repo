# 📖 Energy Digital Twin: Ubiquitous Language Glossary

This glossary establishes the **Ubiquitous Language** (a core Domain-Driven Design principle) used across the codebase, UI, and business logic to ensure developers and domain experts share an exact mental model.

## Artificial Intelligence & Operations Research
* **MCTS (Monte Carlo Tree Search):** A heuristic search algorithm used in `mcts_engine.py` to evaluate the systemic downside risk (Value-at-Risk) of cascading supply chain failures.
* **LSTM-AE (Long Short-Term Memory Autoencoder):** A neural network architecture simulated in `pdm_agent.py` to detect time-series reconstruction errors indicating physical machinery fatigue.
* **CoT (Chain-of-Thought):** The prompting strategy used in `watcher_agent.py` requiring the LLM to output its step-by-step geopolitical reasoning before assigning a threat score.

## Industrial Logistics & Supply Chain
* **SPR (Strategic Petroleum Reserve):** The underground cavern infrastructure (modeled in `spr_agent.py`) holding emergency supply. Hard limit: 39 Million Barrels.
* **DOH (Days of Inventory on Hand):** A metric calculated by `inventory_agent.py` indicating exactly how long a specific refinery can operate without incoming vessel deliveries before total starvation.
* **VaR (Value at Risk):** A financial metric used to quantify the downside exposure of an investment or portfolio. In our model, it represents the 95th percentile worst-case severity.
* **BIA (Business Impact Analysis):** The enterprise framework used in `economic_impact_model.py` to calculate exact SLA penalties, lost revenue, and expediting costs in dollars.
* **CGE (Computable General Equilibrium):** An economic modeling approach used to estimate the effect of supply shocks on macro metrics like Brent Crude pricing and GDP.
