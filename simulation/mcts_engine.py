import math
import random
from typing import Any, Dict, List, Optional
from simulation.economic_impact_model import predict_economic_fallout

SCENARIO_BASELINE = {
    "Baseline (No Disruption)": {
        "base_nodes": [1, 2, 3, 8],
        "disrupted_nodes": [],
    },
    "Red Sea Shipping Suspension (Houthi Threat)": {
        "base_nodes": [1, 2, 3, 8],
        "disrupted_nodes": [6],
    },
    "Strait of Hormuz Partial Closure": {
        "base_nodes": [1, 2, 8],
        "disrupted_nodes": [3],
    },
    "OPEC+ Emergency Supply Cut": {
        "base_nodes": [1, 8],
        "disrupted_nodes": [2, 3],
    },
}


class MCTSNode:
    """
    Represents a state node within the Monte Carlo look-ahead tree.
    """

    def __init__(
        self,
        state_nodes: List[int],
        disrupted_nodes: List[int],
        current_day: int,
        max_depth: int,
        parent: Optional["MCTSNode"] = None,
        action_taken: Optional[str] = None,
    ):
        self.state_nodes = list(state_nodes)
        self.disrupted_nodes = list(disrupted_nodes)
        self.current_day = current_day
        self.max_depth = max_depth
        self.parent = parent
        self.action_taken = action_taken

        self.children: List["MCTSNode"] = []
        self.visits = 0
        self.total_reward = 0.0
        self.untried_actions = (
            [
                "Maintain Baseline",
                "Secondary Congestion Shock",
                "Strategic SPR Intervention",
            ]
            if current_day < max_depth
            else []
        )

    def get_uct_score(self, exploration_constant: float = 1.414) -> float:
        if self.visits == 0:
            return float("inf")
        return (
            (self.total_reward / self.visits)
            + exploration_constant
            * math.sqrt(math.log(self.parent.visits) / self.visits)
        )

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
            action_taken=action,
        )
        self.children.append(child_node)
        return child_node

    def rollout(self, disruption_event: str, base_severity: int) -> float:
        day = self.current_day
        sim_disrupted = list(self.disrupted_nodes)

        while day < self.max_depth:
            if random.random() > 0.75:
                potential_failures = [n for n in [4, 5, 6, 7] if n not in sim_disrupted]
                if potential_failures:
                    sim_disrupted.append(random.choice(potential_failures))
            day += 1

        sim_severity = min(10, base_severity + len(sim_disrupted) - len(self.disrupted_nodes))
        macro_metrics = predict_economic_fallout(disruption_event, sim_severity)

        gdp_val = float(macro_metrics.get("gdp_impact", "-0.5%").replace("%", ""))
        reward = max(0.0, 10.0 + gdp_val)
        return reward

    def backpropagate(self, reward: float):
        self.visits += 1
        self.total_reward += reward
        if self.parent:
            self.parent.backpropagate(reward)


def run_mcts_scenario(
    disruption_event: str,
    severity: int,
    elasticity: float = -0.4,
    spr_release_cap: float = 1.5,
    refinery_buffer: int = 7,
) -> Dict[str, Any]:
    if disruption_event not in SCENARIO_BASELINE:
        disruption_event = "Baseline (No Disruption)"

    scenario_nodes = SCENARIO_BASELINE[disruption_event].copy()

    root = MCTSNode(
        state_nodes=scenario_nodes["base_nodes"],
        disrupted_nodes=scenario_nodes["disrupted_nodes"],
        current_day=0,
        max_depth=7,
    )

    iterations = 1000
    for _ in range(iterations):
        node = root
        while not node.untried_actions and node.children:
            node = node.select_child()
        if node.untried_actions:
            node = node.expand()
        reward = node.rollout(disruption_event, severity)
        node.backpropagate(reward)

    total_cascading_visits = sum(
        child.visits
        for child in root.children
        if child.action_taken == "Secondary Congestion Shock"
    )
    contagion_prob = (total_cascading_visits / max(1, root.visits)) * 100
    model_confidence = max(45.0, 98.5 - (severity * 1.5) + (root.visits * 0.0005))

    economic_forecast = predict_economic_fallout(
        disruption_event, severity, elasticity, spr_release_cap, refinery_buffer
    )

    return {
        **scenario_nodes,
        **economic_forecast,
        "calculated_severity": severity,
        "contagion_probability": f"{contagion_prob:.1f}%",
        "mcts_confidence": f"{model_confidence:.1f}%",
    }
