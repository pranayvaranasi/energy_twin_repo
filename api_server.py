"""
FastAPI Microservice Layer
Provides a scalable, horizontally-distributable REST API for the Digital Twin compute engines.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import concurrent.futures

from simulation.mcts_engine import run_mcts_scenario
from routing.wrapper import get_optimized_corridors
from simulation.inventory_agent import calculate_stranded_inventory

app = FastAPI(
    title="Energy Supply Chain Twin API",
    description="Horizontally scalable microservice for Geopolitical Risk & Routing Optimization",
    version="1.0.0"
)

# Request Payload Schema
class SimulationRequest(BaseModel):
    disruption_event: str
    severity: int
    elasticity: float = -0.4
    spr_release_cap: float = 1.5
    refinery_buffer: int = 7

@app.post("/api/v1/simulate")
async def execute_digital_twin(req: SimulationRequest):
    """
    Decoupled execution endpoint. Allows UI to remain lightweight while 
    heavy C++ and PyTorch compute scales horizontally on backend Kubernetes pods.
    """
    try:
        # 1. Run Stochastic MCTS
        impact_data = run_mcts_scenario(
            req.disruption_event, req.severity, req.elasticity, req.spr_release_cap, req.refinery_buffer
        )
        
        # 2. Parallel Graph Execution (Concurrency & Parallelism principle)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_routes = executor.submit(get_optimized_corridors, impact_data)
            future_inventory = executor.submit(
                calculate_stranded_inventory, 
                impact_data.get("disrupted_nodes", []), req.severity, 80.0
            )
            
            routes_result = future_routes.result()
            inventory_result = future_inventory.result()

        return {
            "status": "success",
            "impact_data": impact_data,
            "routing": routes_result,
            "inventory": inventory_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compute Node Failure: {str(e)}")

# Run via: uvicorn api_server:app --host 0.0.0.0 --port 8000
