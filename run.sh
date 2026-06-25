#!/bin/bash

echo "🚀 Initializing AI-Driven Energy Supply Chain Digital Twin..."

# Step 1: Compile the C++ Routing Engine (if g++ is available)
echo "⚙️ Checking for C++ compiler (g++)..."
if command -v g++ >/dev/null 2>&1; then
    echo "⚙️ Compiling C++ graph optimizer..."
    g++ -shared -fPIC -o routing/graph_optimizer.so routing/graph_optimizer.cpp
    if [ $? -ne 0 ]; then
        echo "❌ C++ Compilation failed. Please ensure g++ is correctly installed."
        exit 1
    fi
    echo "✅ C++ shared library compiled successfully."
else
    echo "⚠️ g++ not found. Skipping C++ compilation. The app may fail without the compiled engine."
fi

# Step 2: Verify Python Dependencies (Optional but recommended)
echo "📦 Checking Python dependencies..."
pip install -r requirements.txt -q

# Step 3: Launch the Streamlit Dashboard
echo "🌐 Launching the Digital Twin Command Center..."
streamlit run app.py
