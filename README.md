# energy_twin_repo

## ⚙️ Deployment & Execution

This application is fully containerized to ensure cross-platform compatibility and zero-dependency friction.

### One-Click Launch (Recommended)

Ensure Docker is running, then execute:

```bash
docker-compose up --build
```

The digital twin will be available at http://localhost:8501.

---

### Notes

- The `Dockerfile` compiles the C++ routing engine (`routing/graph_optimizer.cpp`) during image build. If you want live-editing of the C++ code during development, remove the `volumes` entry in `docker-compose.yml` or recompile inside the running container.
- For local development without Docker, `run.sh` will attempt to compile the C++ engine if `g++` is present; otherwise it will warn and skip compilation.
