import json
from pathlib import Path
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# GeeksForGeeks Principle: Optimize "Data Storage and Access" via RAM Caching
# lru_cache ensures this function only reads from the disk ONCE during the application's lifecycle.
@lru_cache(maxsize=1)
def get_cached_graph_data() -> dict:
    """
    Centralized, memory-cached graph loader.
    Eliminates repetitive Disk I/O bottlenecks across multiple agent executions.
    """
    logger.info("RAM CACHE MISS: Loading supply_nodes.json from disk into memory...")
    data_path = Path(__file__).resolve().parent.parent / "data" / "supply_nodes.json"
    
    try:
        with open(data_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Critical System Failure: Could not locate graph data at {data_path}")
        return {"nodes": [], "edges": []}
