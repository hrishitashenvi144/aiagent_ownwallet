#!/usr/bin/env bash
set -e

echo "=== Launching AuditAgent Local Development Stack ==="

# Check if anvil is installed
if command -v anvil >/dev/null 2>&1; then
    echo "--> Starting Anvil node on 127.0.0.1:8545..."
    anvil --port 8545 &
    ANVIL_PID=$!
else
    echo "--> Notice: 'anvil' not detected in PATH. Running services with mock web3 / testnet mode."
fi

echo "--> Launching FastAPI Agent Core on port 8000..."
uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload &
AGENT_PID=$!

echo "--> Launching Next.js Dashboard on port 3000..."
cd dashboard && npm run dev &
DASH_PID=$!
cd ..

echo "=== Services Running! ==="
echo "Dashboard: http://localhost:3000"
echo "Agent API: http://localhost:8000/docs"
echo "Press Ctrl+C to stop all processes."

trap "kill $AGENT_PID $DASH_PID ${ANVIL_PID:-} 2>/dev/null" EXIT
wait
