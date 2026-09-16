from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "Elevator" / "elevator_monitor.py"
spec = importlib.util.spec_from_file_location("elevator_monitor", ANALYSIS)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def downsample(x, y, points=360):
    target = np.linspace(float(x[0]), float(x[-1]), points)
    return target.tolist(), np.interp(target, x, y).tolist()


rides, _ = module.load_rides(ROOT / "Elevator" / "data260913", ROOT / "Elevator" / "runs.csv")
module.classify(rides)

payload = {"date": "2026-09-13", "label": "Baslinjemätning", "elevators": []}
for ride in rides:
    segment = ride.vertical[ride.start : ride.stop + 1]
    filtered = module.lowpass_zero_phase(segment, ride.fs, 1.0)
    profile_x = np.linspace(0, 100, len(filtered))
    velocity_t, velocity = module.estimated_velocity(ride)
    n = ride.stop - ride.start + 1
    frequency, amplitude = module.spec(
        ride.vertical[ride.start + n // 4 : ride.start + 3 * n // 4], ride.fs
    )
    keep = (frequency >= 0.5) & (frequency <= 25)
    px, py = downsample(profile_x, filtered)
    vx, vy = downsample(velocity_t, velocity)
    fx, fy = downsample(frequency[keep], amplitude[keep], 280)
    payload["elevators"].append(
        {
            "id": ride.name,
            "profile": [{"x": round(x, 3), "y": round(y, 5)} for x, y in zip(px, py)],
            "velocity": [{"x": round(x, 3), "y": round(y, 5)} for x, y in zip(vx, vy)],
            "spectrum": [{"x": round(x, 4), "y": round(y, 6)} for x, y in zip(fx, fy)],
            "metrics": {
                "accelerationTime": round(ride.metrics["accel_phase_s"], 2),
                "startImpulse": round(ride.metrics["start_impulse_ms2"], 3),
                "startJerk": round(ride.metrics["start_jerk_rms_ms3"], 3),
                "cruiseVibration": round(ride.metrics["cruise_vibration_rms_ms2"], 4),
                "brakeJerk": round(ride.metrics["brake_jerk_rms_ms3"], 3),
                "peakSpeed": round(ride.metrics["estimated_peak_speed_ms"], 3),
                "dominantFrequency": round(ride.metrics["dominant_hz"], 2),
                "dominantAmplitude": round(ride.metrics["dominant_amp_ms2"], 5),
            },
        }
    )

out = Path(__file__).resolve().parents[1] / "public" / "data"
out.mkdir(parents=True, exist_ok=True)
(out / "2026-09-13.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
(out / "index.json").write_text(json.dumps({"series": [{"date": payload["date"], "label": payload["label"]}]}, ensure_ascii=False))
print(out / "2026-09-13.json")
