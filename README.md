# 🌍 Energy Supply Chain Resilience Twin (Enterprise Control Tower)

An enterprise-grade Digital Twin for simulating, optimizing, and predicting global energy supply chain resilience in the face of geopolitical disruptions. The platform integrates real-time risk classification, Monte Carlo Tree Search (MCTS) look-ahead modeling, a high-performance C++ multi-source Dijkstra routing optimizer, and a Breadth-First Search (BFS) downstream inventory starvation engine.

---

## 🚀 Key Architectural Upgrades

### 1. Palantir-Style Parallel Execution Graph
To minimize end-to-end response times from threat detection to routing recommendations, we decoupled our downstream simulation engines. The Dijkstra Routing Optimizer (compiled C++) and the BFS downstream inventory starvation agent are executed **in parallel** on separate CPU threads using a thread pool executor:
- **Asynchronous Execution:** Dijkstra routing & BFS inventory traversal run concurrently.
- **Latency Reduction:** Slashes simulation sync latency by up to 50%, bringing total control tower orchestration times to under a quarter of a second.
- **Real-time Metrics:** Displays precise microsecond-level telemetry of the execution graph directly in the Streamlit control tower status bar.

### 2. Space-Time AIS Tracking (Temporal ETA Logic)
Incorporates a dynamic vessel navigation simulation along active supply corridors:
- **Haversine Geodistances:** Calculates precise earth-curvature distances (in km) between supply chain nodes.
- **Temporal Interpolation:** Dynamically tracks convoy positions at key fractional points (25%, 50%, 75%) along maritime routes.
- **Live ETA Calculations:** Computes realistic UTC Estimated Time of Arrival (ETA) stamps based on average tanker voyage speeds (25 km/h / ~13.5 knots), displaying them in live interactive hover states.

### 3. Concentric Contagion Radii (Spatial Econometrics)
Implements spatial econometric risk-mapping inspired by Geospatial Impact Evaluation (GIE) methodologies:
- **Primary Epicenter:** A solid, highlighted circle illustrating the immediate operational blackout zone around disrupted nodes.
- **Secondary Contagion Zone:** A wide, semi-transparent outer ring representing the ripple effects and economic spillover risks to adjacent trade paths.
- **Dynamic Severity Scaling:** The physical radius of both rings dynamically rescales on the map based on the assessed disruption severity index ($1 \text{ to } 10$) computed by the AI threat-intelligence agent.

## ⚖️ Enterprise Scalability & Architecture
Designed to bypass standard monolithic bottlenecks, this architecture is engineered for cloud-native scalability:

* **Microservice Decoupling:** Compute engines (C++ Dijkstra, PyTorch MCTS) are decoupled from the Streamlit UI via a **FastAPI REST layer (`api_server.py`)**. This allows the heavy routing engines to be containerized and horizontally autoscaled on Kubernetes independent of frontend traffic.
* **In-Memory Graph Caching:** Utilizing `functools.lru_cache`, the global supply chain graph is loaded directly into RAM upon initialization (`simulation/data_loader.py`). This eliminates catastrophic Disk I/O bottlenecks during concurrent simulation requests.
* **Concurrent Execution:** Utilizing Python `ThreadPoolExecutors`, downstream deterministic agents (Routing & Inventory Traversal) execute asynchronously in parallel, minimizing end-to-end payload latency to sub-300ms.

---

## ⚙️ Deployment & Execution

This application is fully containerized to ensure cross-platform compatibility and zero-dependency friction.

### One-Click Launch (Recommended)

Ensure Docker is running, then execute:

```bash
docker-compose up --build
```

The digital twin will be available at [http://localhost:8501](http://localhost:8501).

---

### Notes for Developers

- The `Dockerfile` compiles the C++ routing engine ([graph_optimizer.cpp](file:///c:/Users/pranay/energy_twin_repo-1/routing/graph_optimizer.cpp)) during the image build process. If you want live-editing of the C++ code during development, remove the `volumes` entry in `docker-compose.yml` or recompile inside the running container.
- For local development without Docker, [run.sh](file:///c:/Users/pranay/energy_twin_repo-1/run.sh) will attempt to compile the C++ engine if `g++` is present; otherwise, it will warn and skip compilation.
