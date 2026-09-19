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


def event_profile(ride, phase):
    """Locally zeroed, event-aligned acceleration around start or stop."""
    signal = module.lowpass_zero_phase(ride.vertical, ride.fs, 5.0)
    if phase == "start":
        search_lo = ride.start
        search_hi = min(len(signal), ride.start + int(6.0 * ride.fs))
        before_s, after_s = 1.25, 4.0
    else:
        search_lo = max(ride.start, ride.stop - int(6.0 * ride.fs))
        search_hi = min(len(signal), ride.stop + 1)
        before_s, after_s = 4.0, 1.25
    search = np.abs(signal[search_lo:search_hi])
    peak = search_lo + int(np.argmax(search))
    threshold = max(0.04, 0.12 * float(search.max()))
    event = peak
    while event > search_lo and abs(signal[event - 1]) > threshold:
        event -= 1
    if phase == "start":
        candidates = np.flatnonzero(search > threshold)
        if len(candidates):
            event = search_lo + int(candidates[0])
    lo = max(0, event - int(before_s * ride.fs))
    hi = min(len(signal), event + int(after_s * ride.fs) + 1)
    baseline_hi = max(lo + 1, event - int(0.25 * ride.fs))
    baseline = float(np.median(signal[lo:baseline_hi]))
    seconds = (np.arange(lo, hi) - event) / ride.fs
    values = signal[lo:hi] - baseline
    if len(seconds) > 320:
        seconds, values = map(np.asarray, downsample(seconds, values, 320))
    return [{"x": round(float(x), 3), "y": round(float(y), 5)} for x, y in zip(seconds, values)]


def spatial_diagnostics(ride):
    """Map high-frequency ride vibration to shaft position and spatial frequency."""
    raw = ride.vertical[ride.start : ride.stop + 1]
    _, velocity = module.estimated_velocity(ride)
    velocity = np.maximum(velocity, 0.0)
    distance = np.r_[0.0, np.cumsum((velocity[:-1] + velocity[1:]) / (2 * ride.fs))]
    total_distance = float(distance[-1])
    if total_distance <= 0.5:
        raise ValueError(f"Unusable distance estimate for {ride.name}")

    # Isolate vibration from the low-frequency motion profile using zero-phase filters.
    band = (
        module.lowpass_zero_phase(raw, ride.fs, 25.0)
        - module.lowpass_zero_phase(raw, ride.fs, 2.0)
    )
    local_rms = np.sqrt(np.maximum(0, module.movavg(band * band, 0.8 * ride.fs)))
    floor_position = ride.top + (ride.bottom - ride.top) * distance / total_distance
    moving = velocity >= max(0.25, 0.15 * float(np.max(velocity)))

    # Uniform spatial sampling turns temporal oscillations into cycles per metre,
    # including the acceleration and braking phases where speed is changing.
    keep = np.r_[True, np.diff(distance) > 1e-5]
    spatial_x = np.linspace(0.0, total_distance, max(512, min(2048, len(raw))))
    spatial_vibration = np.interp(spatial_x, distance[keep], band[keep])
    spatial_fs = 1.0 / float(np.median(np.diff(spatial_x)))
    cycles_per_m, spatial_amplitude = module.spec(spatial_vibration, spatial_fs)
    usable = (cycles_per_m >= 0.25) & (cycles_per_m <= min(20.0, 0.45 * spatial_fs))
    peak_index = np.flatnonzero(usable)[np.argmax(spatial_amplitude[usable])]
    peak_energy_index = np.flatnonzero(moving)[np.argmax(local_rms[moving])]
    return {
        "floor_position": floor_position[moving],
        "local_rms": local_rms[moving],
        "cycles_per_m": cycles_per_m[usable],
        "spatial_amplitude": spatial_amplitude[usable],
        "distance_m": total_distance,
        "dominant_cpm": float(cycles_per_m[peak_index]),
        "dominant_spatial_amplitude": float(spatial_amplitude[peak_index]),
        "spatial_period_m": float(1.0 / cycles_per_m[peak_index]),
        "peak_vibration_floor": float(floor_position[peak_energy_index]),
        "peak_local_rms": float(local_rms[peak_energy_index]),
    }


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
    spatial = spatial_diagnostics(ride)
    start_profile = event_profile(ride, "start")
    stop_profile = event_profile(ride, "stop")
    hx, hy = downsample(spatial["floor_position"][::-1], spatial["local_rms"][::-1])
    sx, sy = downsample(spatial["cycles_per_m"], spatial["spatial_amplitude"], 280)
    payload["elevators"].append(
        {
            "id": ride.name,
            "topFloor": ride.top,
            "bottomFloor": ride.bottom,
            "profile": [{"x": round(x, 3), "y": round(y, 5)} for x, y in zip(px, py)],
            "startProfile": start_profile,
            "stopProfile": stop_profile,
            "velocity": [{"x": round(x, 3), "y": round(y, 5)} for x, y in zip(vx, vy)],
            "spectrum": [{"x": round(x, 4), "y": round(y, 6)} for x, y in zip(fx, fy)],
            "heightEnergy": [{"x": round(x, 3), "y": round(y, 6)} for x, y in zip(hx, hy)],
            "spatialSpectrum": [{"x": round(x, 4), "y": round(y, 6)} for x, y in zip(sx, sy)],
            "metrics": {
                "accelerationTime": round(ride.metrics["accel_phase_s"], 2),
                "startImpulse": round(ride.metrics["start_impulse_ms2"], 3),
                "startJerk": round(ride.metrics["start_jerk_rms_ms3"], 3),
                "cruiseVibration": round(ride.metrics["cruise_vibration_rms_ms2"], 4),
                "brakeJerk": round(ride.metrics["brake_jerk_rms_ms3"], 3),
                "peakSpeed": round(ride.metrics["estimated_peak_speed_ms"], 3),
                "dominantFrequency": round(ride.metrics["dominant_hz"], 2),
                "dominantAmplitude": round(ride.metrics["dominant_amp_ms2"], 5),
                "estimatedDistance": round(spatial["distance_m"], 2),
                "dominantCyclesPerMeter": round(spatial["dominant_cpm"], 3),
                "spatialPeriod": round(spatial["spatial_period_m"], 3),
                "dominantSpatialAmplitude": round(spatial["dominant_spatial_amplitude"], 5),
                "peakVibrationFloor": round(spatial["peak_vibration_floor"], 2),
                "peakLocalVibration": round(spatial["peak_local_rms"], 4),
            },
        }
    )

out = Path(__file__).resolve().parents[1] / "public" / "data"
out.mkdir(parents=True, exist_ok=True)
(out / "2026-09-13.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
(out / "index.json").write_text(json.dumps({"series": [{"date": payload["date"], "label": payload["label"]}]}, ensure_ascii=False))
print(out / "2026-09-13.json")
