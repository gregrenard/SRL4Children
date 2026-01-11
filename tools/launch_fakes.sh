#!/bin/bash
# Launch all fake servers for local testing
# Usage: ./tools/launch_fakes.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting fake servers..."
echo "  Endpoint:  http://localhost:18080/chat"
echo "  Judge:     http://localhost:18081/v1"
echo "  Generator: http://localhost:18082/v1"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Start servers in background
uv run python "$SCRIPT_DIR/fake_endpoint.py" &
PID1=$!
uv run python "$SCRIPT_DIR/fake_judge.py" &
PID2=$!
uv run python "$SCRIPT_DIR/fake_generator.py" &
PID3=$!

# Cleanup on exit
trap "kill $PID1 $PID2 $PID3 2>/dev/null; echo ''; echo 'All servers stopped.'" EXIT

# Wait for any to exit
wait
