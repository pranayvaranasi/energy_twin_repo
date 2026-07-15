from simulation.kg_agent import SupplyChainKnowledgeGraph

def test_cypher_generation_and_label_inference():
    kg = SupplyChainKnowledgeGraph()
    # Mocking triples manually to check label inference and query generation
    kg._add_triple("Saudi Aramco", "PRODUCES_GRADE", "Arab Light")
    kg._add_triple("Arab Light", "TRANSITS_THROUGH", "Strait of Hormuz")
    kg._add_triple("Strait of Hormuz", "FEEDS_INTO", "Jamnagar Refinery")
    kg._add_triple("Strait of Hormuz", "IS_EXPOSED_TO", "Iranian Blockade Risk", risk_level=8)
    kg._add_triple("Iranian Blockade Risk", "CAUSES_EVENT", "Blockade Event")
    kg._add_triple("Saudi Aramco", "HAS_COMPLIANCE_RISK", "OFAC Sanctions Registry")
    kg._add_triple("OFAC Sanctions Registry", "RESTRICTS_FINANCING_FOR", "Arab Light")
    kg._add_triple("Arab Light", "METALLURGICALLY_COMPATIBLE_WITH", "Jamnagar Refinery", score=92.5)

    # 1. Test Label Inference
    labels = kg.infer_node_labels()
    assert labels["Saudi Aramco"] == "Supplier"
    assert labels["Arab Light"] == "CrudeGrade"
    assert labels["Strait of Hormuz"] == "Corridor"
    assert labels["Jamnagar Refinery"] == "Refinery"
    assert labels["Iranian Blockade Risk"] == "Risk"
    assert labels["OFAC Sanctions Registry"] == "SanctionsRegistry"
    assert labels["Blockade Event"] == "Event"

    # 2. Test Cypher Queries Generation
    cypher_script = kg.generate_cypher_queries(impact_data={"calculated_severity": 8})
    
    # Assert Constraints are created
    assert "CREATE CONSTRAINT IF NOT EXISTS FOR (cru:CrudeGrade) REQUIRE cru.name IS UNIQUE;" in cypher_script
    assert "CREATE CONSTRAINT IF NOT EXISTS FOR (ref:Refinery) REQUIRE ref.name IS UNIQUE;" in cypher_script
    
    # Assert Merges exist
    assert 'MERGE (saudiaramco:Supplier {name: "Saudi Aramco"})' in cypher_script
    assert 'MERGE (arablight:CrudeGrade {name: "Arab Light", api: 33.0, sulfur: 2.0, base_price: 84.5})' in cypher_script
    # Note: Strait of Hormuz might match "Middle East (Hormuz)" or Strait of Hormuz. In data/supply_nodes.json, we have "Middle East (Hormuz)" as ID 3.
    # Our code matches "Middle East (Hormuz)" if we do key similarity checks. Let's make sure it handles both.
    assert 'MERGE (straitofhormuz:Corridor' in cypher_script
    assert 'MERGE (jamnagarrefinery:Refinery' in cypher_script
    assert 'MERGE (iranianblockaderisk:Risk' in cypher_script
    
    # Assert Relationships are mapped
    assert "MERGE (saudiaramco)-[:PRODUCES_GRADE]->(arablight)" in cypher_script
    assert "MERGE (arablight)-[:TRANSITS_THROUGH]->(straitofhormuz)" in cypher_script
    assert "MERGE (straitofhormuz)-[:FEEDS_INTO]->(jamnagarrefinery)" in cypher_script
    assert "MERGE (straitofhormuz)-[:IS_EXPOSED_TO {risk_level: 8}]->(iranianblockaderisk)" in cypher_script
    assert "MERGE (arablight)-[:METALLURGICALLY_COMPATIBLE_WITH {score: 92.5}]->(jamnagarrefinery)" in cypher_script
