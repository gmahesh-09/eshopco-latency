# api/latency.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, "..", "q-vercel-latency.json")

with open(data_path) as f:
    telemetry = json.load(f)

# ✅ Define request body model
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float = 180

@app.post("/api/latency")
async def latency(req: LatencyRequest):
    regions = req.regions
    threshold = req.threshold_ms
    response = {}

    for region in regions:
        records = [r for r in telemetry if r["region"] == region]
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        if not records:
            continue

        breaches = sum(1 for l in latencies if l > threshold)
        response[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": breaches,
        }

    return response
