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

    def infer_node_labels(self) -> Dict[str, str]:
        """
        Infers label/type (e.g. Supplier, CrudeGrade, Corridor, Refinery, Risk, SanctionsRegistry, Event)
        for each node in the Knowledge Graph by analyzing the predicate patterns in the triples.
        """
        labels = {}
        for triple in self.triples:
            sub = triple["Subject"]
            pred = triple["Predicate"]
            obj = triple["Object"]
            
            if pred == "PRODUCES_GRADE":
                labels[sub] = "Supplier"
                labels[obj] = "CrudeGrade"
            elif pred == "HAS_COMPLIANCE_RISK":
                labels[sub] = "Supplier"
                labels[obj] = "SanctionsRegistry"
            elif pred == "RESTRICTS_FINANCING_FOR":
                labels[sub] = "SanctionsRegistry"
                labels[obj] = "CrudeGrade"
            elif pred == "TRANSITS_THROUGH":
                labels[sub] = "CrudeGrade"
                labels[obj] = "Corridor"
            elif pred == "IS_EXPOSED_TO":
                labels[sub] = "Corridor"
                labels[obj] = "Risk"
            elif pred == "CAUSES_EVENT":
                labels[sub] = "Risk"
                labels[obj] = "Event"
            elif pred in ("METALLURGICALLY_COMPATIBLE_WITH", "CAUSES_DAMAGE_TO"):
                labels[sub] = "CrudeGrade"
                labels[obj] = "Refinery"
            elif pred == "FEEDS_INTO":
                labels[sub] = "Corridor"
                labels[obj] = "Refinery"

        # Fallback default for any remaining nodes in kg
        for node in self.kg.nodes:
            if node not in labels:
                labels[node] = "Entity"
        return labels

    def generate_cypher_queries(self, impact_data: Dict[str, Any] = None) -> str:
        """
        Generates production-grade Cypher queries (Constraints, Nodes, and Edges)
        representing the current live ontology state.
        """
        labels = self.infer_node_labels()
        
        # Import lookups dynamically to avoid circular imports or assumptions
        from simulation.procurement_agent import CRUDE_MARKET_TICKER, REFINERY_PROFILES, CORRIDOR_LOGISTICS_FEED
        from simulation.data_loader import get_cached_graph_data

        node_properties = {}
        supply_nodes = {}
        try:
            graph_data = get_cached_graph_data()
            for n in graph_data.get("nodes", []):
                supply_nodes[n["name"]] = n
        except Exception:
            pass

        severity = 1
        if impact_data:
            severity = impact_data.get("calculated_severity", 1)

        def get_best_match(query: str, choices: dict) -> Any:
            query_lower = query.lower()
            if query in choices:
                return choices[query]
            for k, v in choices.items():
                if k.lower() == query_lower:
                    return v
            for k, v in choices.items():
                k_lower = k.lower()
                if k_lower in query_lower or query_lower in k_lower:
                    return v
            query_words = set(w for w in query_lower.split() if w not in {"refinery", "bypass", "canal", "strait", "direct", "transit", "port", "hub", "of", "and"})
            for k, v in choices.items():
                k_words = set(w for w in k.lower().split() if w not in {"refinery", "bypass", "canal", "strait", "direct", "transit", "port", "hub", "of", "and"})
                if query_words & k_words:
                    return v
            return None

        for node in self.kg.nodes:
            label = labels.get(node, "Entity")
            props = {"name": node}
            
            # Enrich based on label type
            if label == "CrudeGrade":
                match = get_best_match(node, CRUDE_MARKET_TICKER)
                if match:
                    props["api"] = match["api"]
                    props["sulfur"] = match["sulfur"]
                    props["base_price"] = match["base_price"]
            elif label == "Refinery":
                match = get_best_match(node, REFINERY_PROFILES)
                if match:
                    props["max_sulfur_tolerance"] = match["max_sulfur"]
                    props["target_api"] = match["target_api"]
                    props["complexity_index"] = match["complexity_index"]
                
                node_match = get_best_match(node, supply_nodes)
                if node_match:
                    props["capacity_mmbpd"] = node_match.get("capacity_mmbpd", 0.0)
            elif label == "Corridor":
                feed_match = get_best_match(node, CORRIDOR_LOGISTICS_FEED)
                if feed_match:
                    props["freight_vlcc"] = feed_match["freight_vlcc"]
                    props["transit_days"] = feed_match["transit_days"]
                    props["mode"] = feed_match["mode"]
                
                node_match = get_best_match(node, supply_nodes)
                if node_match:
                    if "type" not in props:
                        props["type"] = node_match.get("type", "maritime_corridor")
                    props["capacity_mmbpd"] = node_match.get("capacity_mmbpd", 0.0)
            elif label == "Risk":
                props["severity"] = severity
                
            node_properties[node] = props

        def safe_var(name: str) -> str:
            cleaned = "".join(c for c in name if c.isalnum() or c == "_")
            if not cleaned:
                return "node"
            if cleaned[0].isdigit():
                cleaned = "_" + cleaned
            return cleaned.lower()

        def format_properties(props: dict) -> str:
            items = []
            for k, v in props.items():
                if isinstance(v, str):
                    val_str = f'"{v.replace(chr(34), chr(92) + chr(34))}"'
                elif isinstance(v, bool):
                    val_str = "true" if v else "false"
                elif v is None:
                    continue
                else:
                    val_str = str(v)
                items.append(f"{k}: {val_str}")
            return "{" + ", ".join(items) + "}"

        lines = []
        lines.append("// 1. Define Constraints (Best practice for optimizing query speeds and preventing duplicates)")
        unique_labels = sorted(list(set(labels.values())))
        for label in unique_labels:
            if label != "Entity":
                var_name = label.lower()[:3]
                lines.append(f"CREATE CONSTRAINT IF NOT EXISTS FOR ({var_name}:{label}) REQUIRE {var_name}.name IS UNIQUE;")
        lines.append("")

        lines.append("// 2. Ingest the Entities (Nodes)")
        var_map = {}
        for node in sorted(self.kg.nodes):
            label = labels.get(node, "Entity")
            v_name = safe_var(node)
            base_v_name = v_name
            counter = 1
            while v_name in var_map.values() and var_map.get(node) != v_name:
                v_name = f"{base_v_name}_{counter}"
                counter += 1
            var_map[node] = v_name
            
            props = node_properties.get(node, {"name": node})
            props_str = format_properties(props)
            lines.append(f"MERGE ({v_name}:{label} {props_str})")
        lines.append("")

        lines.append("// 3. Define Semantic Relationships (The Ontology Triples)")
        seen_edges = set()
        for u, v, data in self.kg.edges(data=True):
            pred = data.get("relation", "RELATED_TO")
            var_u = var_map.get(u, safe_var(u))
            var_v = var_map.get(v, safe_var(v))
            
            edge_props = {k: v_ for k, v_ in data.items() if k != "relation"}
            edge_props_str = ""
            if edge_props:
                edge_props_str = " " + format_properties(edge_props)
                
            edge_key = (var_u, pred, edge_props_str, var_v)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                lines.append(f"MERGE ({var_u})-[:{pred}{edge_props_str}]->({var_v})")

        return "\n".join(lines)

# Singleton instantiation for the app
kg_engine = SupplyChainKnowledgeGraph()
