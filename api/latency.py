# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
def load_telemetry_data():
    """Load telemetry data from JSON file"""
    try:
        # Get the directory of the current file (api/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to root and load the file
        parent_dir = os.path.dirname(current_dir)
        data_path = os.path.join(parent_dir, 'q-vercel-latency.json')
        
        with open(data_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, Exception) as e:
        print(f"Error loading telemetry data: {e}")
        # Fallback sample data structure
        return {}

TELEMETRY_DATA = load_telemetry_data()


class MetricsRequest(BaseModel):
    regions: List[str] = Field(..., description="List of regions to query")
    threshold_ms: float = Field(180, description="Latency threshold in milliseconds")


class RegionMetrics(BaseModel):
    avg_latency: float
    p95_latency: float
    avg_uptime: float
    breaches: int


def calculate_metrics(data: List[Dict], threshold_ms: float) -> RegionMetrics:
    """Calculate metrics for a region's data."""
    if not data:
        return RegionMetrics(
            avg_latency=0,
            p95_latency=0,
            avg_uptime=0,
            breaches=0
        )
    
    latencies = [record["latency_ms"] for record in data]
    uptimes = [record["uptime"] for record in data]
    
    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    avg_uptime = np.mean(uptimes)
    breaches = sum(1 for lat in latencies if lat > threshold_ms)
    
    return RegionMetrics(
        avg_latency=round(avg_latency, 2),
        p95_latency=round(p95_latency, 2),
        avg_uptime=round(avg_uptime, 2),
        breaches=breaches
    )


@app.post("/api/metrics", response_model=Dict[str, RegionMetrics])
async def get_metrics(request: MetricsRequest):
    """
    Accept POST request with JSON body:
    {
        "regions": ["emea", "apac", ...],
        "threshold_ms": 169
    }
    
    Return per-region metrics.
    """
    results = {}
    
    for region in request.regions:
        if region in TELEMETRY_DATA:
            results[region] = calculate_metrics(
                TELEMETRY_DATA[region], 
                request.threshold_ms
            )
        else:
            # Return zeros if region not found
            results[region] = RegionMetrics(
                avg_latency=0,
                p95_latency=0,
                avg_uptime=0,
                breaches=0
            )
    
    return results


@app.get("/")
async def root():
    return {"message": "eShopCo Metrics API", "available_regions": list(TELEMETRY_DATA.keys())}


# ===================================
# requirements.txt
# ===================================
# fastapi
# numpy
# pydantic

# ===================================
# vercel.json
# ===================================
# {
#   "rewrites": [
#     {
#       "source": "/(.*)",
#       "destination": "/api/index"
#     }
#   ]
# }
