#!/bin/bash
# Script to start both Operator and User dashboards
# Run this from the project root directory

cd "$(dirname "$0")/.."

echo "Starting SpendSenseAI Frontends..."
echo ""
echo "Operator Dashboard will be available at http://localhost:5173"
echo "User Dashboard will be available at http://localhost:5174"
echo ""
echo "Make sure the API server is running at http://localhost:8000"
echo ""

# Navigate to frontend directory
cd frontend

# Start Operator Dashboard in background
echo "Starting Operator Dashboard on port 5173..."
npm run dev:operator &

# Wait a moment
sleep 2

# Start User Dashboard in background
echo "Starting User Dashboard on port 5174..."
npm run dev:user &

echo ""
echo "Both dashboards are starting..."
echo "Operator Dashboard: http://localhost:5173"
echo "User Dashboard: http://localhost:5174/dashboard/CUST000001"

