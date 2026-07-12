import math
import random
import numpy as np
from typing import Any, Dict, List, Optional
from simulation.economic_impact_model import predict_economic_fallout

# 1. High-Fidelity Scenario Parameters 
# Each scenario now includes distinct standard deviation (volatility) and contagion multipliers
SCENARIO_BASELINE = {
    "Baseline (No Disruption)": {
        "base_nodes": [1, 2, 3, 8], "disrupted_nodes": [],
        "volatility": 0.05, "contagion_alpha": 0.02
    },
    "Red Sea Shipping Suspension (Houthi Threat)": {
        "base_nodes": [1, 2, 3, 8], "disrupted_nodes": [6],
        "volatility": 0.65, "contagion_alpha": 0.35
    },
    "Strait of Hormuz Partial Closure": {
        "base_nodes": [1, 2, 8], "disrupted_nodes": [3],
        "volatility": 0.85, "contagion_alpha": 0.60
    },
    "OPEC+ Emergency Supply Cut": {
        "base_nodes": [1, 8], "disrupted_nodes": [2, 3],
        "volatility": 0.40, "contagion_alpha": 0.20
    },
}

class MCTSNode:
    """
    Represents a state node within the Monte Carlo look-ahead tree.
    Tracks sequential crisis days and cascading downstream network failures.
    """
    def __init__(self, state_nodes: List[int], disrupted_nodes: List[int], current_day: int, max_depth: int, parent: Optional["MCTSNode"] = None, action_taken: Optional[str] = None):
        self.state_nodes = list(state_nodes)
        self.disrupted_nodes = list(disrupted_nodes)
        self.current_day = current_day
        self.max_depth = max_depth
        self.parent = parent
        self.action_taken = action_taken
        
        self.children: List["MCTSNode"] = []
        self.visits = 0
        self.total_reward = 0.0
        
        self.untried_actions = ["Maintain Baseline", "Secondary Congestion Shock", "Strategic SPR Intervention"] if current_day < max_depth else []

    def get_uct_score(self, exploration_constant: float = 1.414) -> float:
        if self.visits == 0:
            return float("inf")
        return (self.total_reward / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

    def select_child(self) -> "MCTSNode":
        return max(self.children, key=lambda child: child.get_uct_score())

    def expand(self) -> "MCTSNode":
        action = self.untried_actions.pop(random.randrange(len(self.untried_actions)))
        
        next_disrupted = list(self.disrupted_nodes)
        next_base = list(self.state_nodes)
        
        if action == "Secondary Congestion Shock":
            potential_cascades = [n for n in [4, 7, 9, 10] if n not in next_disrupted]
            if potential_cascades:
                next_disrupted.append(random.choice(potential_cascades))
        elif action == "Strategic SPR Intervention" and 9 not in next_disrupted:
            if 9 in next_base:
                next_base.append(9) 

        child_node = MCTSNode(
            state_nodes=next_base,
            disrupted_nodes=next_disrupted,
            current_day=self.current_day + 1,
            max_depth=self.max_depth,
            parent=self,
            action_taken=action
        )
        self.children.append(child_node)
        return child_node

    def rollout(self, base_severity: int, volatility: float, contagion_alpha: float) -> float:
        """PHASE 3: Stochastic Simulation utilizing Gaussian Volatility Shocks"""
        day = self.current_day
        sim_disrupted = list(self.disrupted_nodes)
        
        while day < self.max_depth:
            # 2. Mathematical Monte Carlo injection (Mean=0, StdDev=volatility)
            market_shock = random.gauss(0, volatility)
            
            # If the market shock exceeds the contagion threshold, the disruption cascades
            if (random.random() + market_shock) > (1.0 - contagion_alpha):
                potential_failures = [n for n in [4, 5, 6, 7, 10] if n not in sim_disrupted]
                if potential_failures:
                    sim_disrupted.append(random.choice(potential_failures))
            day += 1
            
        sim_severity = min(10.0, base_severity + len(sim_disrupted) - len(self.disrupted_nodes))
        return float(sim_severity)

    def backpropagate(self, severity_score: float):
        # Convert severity score to a maximization reward (0 to 10 scale)
        reward = max(0.0, 10.0 - severity_score)
        self.visits += 1
        self.total_reward += reward
        if self.parent:
            self.parent.backpropagate(severity_score)

def run_mcts_scenario(disruption_event: str, severity: int, elasticity: float = -0.4, spr_release_cap: float = 1.5, refinery_buffer: int = 7) -> Dict[str, Any]:
    """Runs structural look-ahead MCTS graph iterations to calculate precise system resiliency limits."""
    if disruption_event not in SCENARIO_BASELINE:
        disruption_event = "Baseline (No Disruption)"
        
    scenario_params = SCENARIO_BASELINE[disruption_event]
    
    root = MCTSNode(
        state_nodes=scenario_params["base_nodes"],
        disrupted_nodes=scenario_params["disrupted_nodes"],
        current_day=0,
        max_depth=7 
    )
    
    iterations = 1000
    rollout_severities = []
    
    for _ in range(iterations):
        node = root
        while not node.untried_actions and node.children:
            node = node.select_child()
            
        if node.untried_actions:
            node = node.expand()
            
        # Simulate using scenario-specific volatility distributions
        sim_severity = node.rollout(severity, scenario_params["volatility"], scenario_params["contagion_alpha"])
        rollout_severities.append(sim_severity)
        
        node.backpropagate(sim_severity)
        
    # --- 3. Institutional Monte Carlo Analytics ---
    # Downside Risk (Worst 20% of outcomes)
    downside_severity = np.percentile(rollout_severities, 80) 
    
    # Median Trajectory (50th percentile)
    median_severity = np.percentile(rollout_severities, 50)
    
    # Probability of Success (Supply chain survives without hitting catastrophic severity 8+)
    success_count = sum(1 for s in rollout_severities if s < 8.0)
    prob_success = (success_count / iterations) * 100
    
    # We process the final macroeconomic impact on the MEDIAN expected severity
    economic_forecast = predict_economic_fallout(
        disruption_event, median_severity, elasticity, spr_release_cap, refinery_buffer
    )
    
    total_cascading_visits = sum(child.visits for child in root.children if child.action_taken == "Secondary Congestion Shock")
    contagion_prob = (total_cascading_visits / max(1, root.visits)) * 100
    model_confidence = max(45.0, 98.5 - (severity * 1.5) + (root.visits * 0.0005))
    
    return {
        "base_nodes": scenario_params["base_nodes"],
        "disrupted_nodes": scenario_params["disrupted_nodes"],
        **economic_forecast,
        "calculated_severity": median_severity,
        "downside_risk_severity": downside_severity,
        "probability_of_success": f"{prob_success:.1f}%",
        "contagion_probability": f"{contagion_prob:.1f}%",
        "mcts_confidence": f"{model_confidence:.1f}%"
    }
