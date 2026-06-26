# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (g++ for C++ compilation)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Prevent Streamlit from prompting for setup during evaluation
ENV STREAMLIT_SERVER_HEADLESS=true

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Compile the C++ Routing Engine during the image build
RUN if [ -f routing/graph_optimizer.cpp ]; then \
      g++ -O3 -shared -fPIC -o routing/graph_optimizer.so routing/graph_optimizer.cpp; \
    fi

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
