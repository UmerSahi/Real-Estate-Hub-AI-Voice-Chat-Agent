@echo off
title RealEstate Hub - Cloudflare Live Launcher
echo ======================================================================
echo Launching RealEstate Hub Live via Cloudflare Tunnel
echo ======================================================================

echo [1/3] Starting FastAPI Backend on port 8000...
start /b python day5-langgraph-agent\vapi_server.py

echo [2/3] Starting Vite Frontend on port 3000...
cd frontend
start /b npm run dev
cd ..

echo [3/3] Launching Cloudflare Tunnel...
.\cloudflared.exe tunnel --url http://localhost:3000

pause
