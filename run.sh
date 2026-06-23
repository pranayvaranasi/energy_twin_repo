#!/usr/bin/env bash
set -euo pipefail

# Build the C++ shared library for the routing backend.
g++ -shared -fPIC routing/graph_optimizer.cpp -o routing/graph_optimizer.so

# Launch the Streamlit dashboard.
streamlit run app.py
