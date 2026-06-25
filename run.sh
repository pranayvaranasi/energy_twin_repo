#!/bin/bash

echo "🚀 Initializing AI-Driven Energy Supply Chain Digital Twin..."

# Step 1: Compile the C++ Routing Engine
echo "⚙️ Compiling C++ graph optimizer..."
g++ -shared -fPIC -o routing/graph_optimizer.so routing/graph_optimizer.cpp
if [ $? -ne 0 ]; then
    echo "❌ C++ Compilation failed. Please ensure g++ is installed."
    exit 1
fi
echo "✅ C++ shared library compiled successfully."

# Step 2: Verify Python Dependencies (Optional but recommended)
echo "📦 Checking Python dependencies..."
pip install -r requirements.txt -q

# Step 3: Launch the Streamlit Dashboard
echo "🌐 Launching the Digital Twin Command Center..."
streamlit run app.py
