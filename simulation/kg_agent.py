import networkx as nx
import json
import logging
from typing import List, Dict, Any
from simulation.data_loader import get_cached_graph_data

logger = logging.getLogger(__name__)

class SupplyChainKnowledgeGraph:
    """
    Semantic Knowledge Graph Engine.
    Maps non-spatial, relational ontologies (Triples) between Suppliers, Grades, Routes, Risks, and Refineries.
    """
    def __init__(self):
        # MultiDiGraph allows multiple different relationships (edges) between the same entities
        self.kg = nx.MultiDiGraph()
        self.triples = []

    def _add_triple(self, subject: str, predicate: str, object_node: str, **kwargs):
        """Standardizes insertion of Subject -> Predicate -> Object triples."""
        self.kg.add_node(subject, label="Entity")
        self.kg.add_node(object_node, label="Entity")
        self.kg.add_edge(subject, object_node, relation=predicate, **kwargs)
        self.triples.append({"Subject": subject, "Predicate": predicate, "Object": object_node})

    def build_live_ontology(self, impact_data: Dict[str, Any], procurement_matrix: List[Dict[str, Any]]):
        """
        Dynamically constructs the Knowledge Graph based on real-time simulation states.
        Satisfies the 'supplier-route-risk-refinery relationships' requirement.
        """
        self.kg.clear()
        self.triples = []
        
        disrupted_ids = impact_data.get("disrupted_nodes", [])
        trigger_event = impact_data.get("trigger_event", "Baseline")
        severity = impact_data.get("calculated_severity", 1)

        # 1. Map Geopolitical Risks to Physical Corridors
        if 6 in disrupted_ids:
            self._add_triple("Red Sea / Suez", "IS_EXPOSED_TO", "Houthi Maritime Threat", risk_level=severity)
            self._add_triple("Houthi Maritime Threat", "CAUSES_EVENT", trigger_event)
        if 3 in disrupted_ids:
            self._add_triple("Strait of Hormuz", "IS_EXPOSED_TO", "Iranian Blockade Risk", risk_level=severity)
            self._add_triple("Iranian Blockade Risk", "CAUSES_EVENT", trigger_event)

        # 2. Map Suppliers to Grades, Routes, and Compliance Risks
        for option in procurement_matrix:
            supplier = option["supplier"]
            grade = option["crude_grade"]
            corridor = option["logistics_corridor"]
            
            # Supplier -> Grade (e.g., Saudi Aramco PRODUCES Arab Light)
            self._add_triple(supplier, "PRODUCES_GRADE", grade)
            
            # Sanctions Ontology mapping
            if "Sanction" in supplier:
                self._add_triple(supplier, "HAS_COMPLIANCE_RISK", "OFAC Sanctions Registry")
                self._add_triple("OFAC Sanctions Registry", "RESTRICTS_FINANCING_FOR", grade)

            # Grade -> Route (e.g., Arab Light TRANSITS_THROUGH Strait of Hormuz)
            self._add_triple(grade, "TRANSITS_THROUGH", corridor)

        # 3. Map Routes to Refineries & Assay Compatibilities
        graph_data = get_cached_graph_data()
        refineries = [n["name"] for n in graph_data["nodes"] if n["type"] == "refinery"]
        
        for option in procurement_matrix:
            grade = option["crude_grade"]
            corridor = option["logistics_corridor"]
            assay_score = option["assay_fit_score"]
            
            for refinery in refineries:
                if assay_score > 70:
                    self._add_triple(grade, "METALLURGICALLY_COMPATIBLE_WITH", refinery, score=assay_score)
                else:
                    self._add_triple(grade, "CAUSES_DAMAGE_TO", refinery, score=assay_score)
                
                # Close the loop: Route -> Refinery
                self._add_triple(corridor, "FEEDS_INTO", refinery)

        return self.triples

    def execute_graphrag_query(self, query_type: str) -> List[Dict[str, str]]:
        """Traverses the ontology to answer complex, multi-hop relationship questions."""
        results = []
        if query_type == "risk_contagion":
            # Find all Refineries affected by a specific Sanction or Blockade
            for u, v, data in self.kg.edges(data=True):
                if data["relation"] == "IS_EXPOSED_TO":
                    corridor = u
                    risk = v
                    # Find downstream refineries
                    for target, _, rel_data in self.kg.out_edges(corridor, data=True):
                        if rel_data["relation"] == "FEEDS_INTO":
                            results.append({
                                "Risk Origin": risk,
                                "Compromised Corridor": corridor,
                                "Downstream Impact": target
                            })
        return results

# Singleton instantiation for the app
kg_engine = SupplyChainKnowledgeGraph()
