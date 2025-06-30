#!/bin/bash

# --- Configuration ---
FILES_DIR="files"
GENERATED_DIR="generated"
PROTO_DIR="proto"

MAIN_AI_PORT=50051
DEP_AI_PORT=50052

# --- Setup ---

# Check if GEMINI_API_KEY is set in the environment
if [ -z "$GEMINI_API_KEY" ]; then
  echo "Error: GEMINI_API_KEY environment variable is not set."
  echo "Please set it by running:"
  echo "  export GEMINI_API_KEY=your_key_here"
  echo "or by using a .env file and loading it with:"
  echo "  source .env"
  exit 1
fi

echo "--- Setting up Phoenix Prototype ---"

# Create necessary directories
mkdir -p "$FILES_DIR"
mkdir -p "$GENERATED_DIR"

# Initialize or reset files
echo "def greeting():
    print('Hello from Phoenix!')

if __name__ == '__main__':
    greeting()" > "$FILES_DIR/main.py"
echo "# Initial dependencies" > "$FILES_DIR/requirements.txt"
echo "Initialized main.py and requirements.txt"

# Generate gRPC Python code
echo "Generating gRPC Python code..."
# CHANGE THIS LINE: The -I argument (include path) now correctly points to 'proto'
# and the --python_out and --grpc_python_out directly target 'generated'.
python -m grpc_tools.protoc -I"$PROTO_DIR" --python_out="$GENERATED_DIR" --grpc_python_out="$GENERATED_DIR" \
    "$PROTO_DIR/task_protocol.proto" "$PROTO_DIR/main_ai_service.proto" "$PROTO_DIR/dep_ai_service.proto"
if [ $? -ne 0 ]; then
    echo "Error generating gRPC code. Exiting."
    exit 1
fi
echo "gRPC code generation complete."

# --- FIX GENERATED IMPORTS ---
echo "Adjusting generated gRPC file imports..."
# This sed command finds absolute imports of generated pb2 files and makes them relative.
# It targets files ending in _pb2.py and _pb2_grpc.py within the generated directory.
find "$GENERATED_DIR" -name "*_pb2.py" -o -name "*_pb2_grpc.py" | xargs sed -i 's/^import \([a-zA-Z0-9_]*_pb2\) as/from . import \1 as/'
echo "Generated imports adjusted."

# --- Export PYTHONPATH ---
# Add the current directory (project root) to PYTHONPATH
export PYTHONPATH=$(pwd):$PYTHONPATH
echo "PYTHONPATH set to: $PYTHONPATH"

# --- Start Agents ---
echo "Starting MainAI and DepAI agents..."

# Start DepAI in the background
python agents/dep_ai_agent.py &
DEP_AI_PID=$!
echo "DepAI started with PID: $DEP_AI_PID"
sleep 2 # Give DepAI a moment to start

# Start MainAI in the background
python agents/main_ai_agent.py &
MAIN_AI_PID=$!
echo "MainAI started with PID: $MAIN_AI_PID"
sleep 2 # Give MainAI a moment to start

# --- Start CLI ---
echo "--- Starting Phoenix CLI ---"
python cli/Phoenix_cli.py

# --- Cleanup ---
echo "--- Shutting down agents ---"
# Check if PIDs exist before killing
if ps -p $MAIN_AI_PID > /dev/null; then
  kill $MAIN_AI_PID
fi
if ps -p $DEP_AI_PID > /dev/null; then
  kill $DEP_AI_PID
fi
echo "Agents shut down."
echo "Phoenix prototype finished."
