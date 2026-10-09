from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import statistics
import math

app = FastAPI()

# CORS: allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "q-vercel-latency.json"

with DATA_FILE.open("r", encoding="utf-8") as f:
    telemetry = json.load(f)

class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile(values, p):
    values = sorted(values)

    if not values:
        return 0

    k = (len(values) - 1) * p
    lower = math.floor(k)
    upper = math.ceil(k)

    if lower == upper:
        return values[lower]

    return values[lower] + (values[upper] - values[lower]) * (k - lower)


@app.post("/latency")
def calculate_latency(request: LatencyRequest):

    results = []

    for region in request.regions:

        records = [
            row for row in telemetry
            if row["region"] == region
        ]

        if not records:
            continue

        latencies = [row["latency_ms"] for row in records]
        uptimes = [row["uptime_pct"] for row in records]

        results.append({
            "region": region,
            "avg_latency": statistics.mean(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(
                1 for x in latencies
                if x > request.threshold_ms
            )
        })

    return results
