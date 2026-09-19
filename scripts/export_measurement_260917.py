from __future__ import annotations

import importlib.util
import json
import re
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


def barometer_diagnostics(ride):
    """Return relative barometric height during the detected ride."""
    acc_t0 = None
    pressure_rows = []
    with ride.path.open(encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 5 and parts[1] == "ACC" and acc_t0 is None:
                acc_t0 = float(parts[0])
            elif len(parts) >= 3 and parts[1] == "PRS":
                pressure_rows.append((float(parts[0]), float(parts[2])))
    if acc_t0 is None or len(pressure_rows) < 2:
        return [], None
    start_ms = acc_t0 + 1000.0 * ride.t[ride.start]
    stop_ms = acc_t0 + 1000.0 * ride.t[ride.stop]
    selected = [(stamp, pressure) for stamp, pressure in pressure_rows if start_ms <= stamp <= stop_ms]
    if len(selected) < 2:
        return [], None
    stamps = np.asarray([row[0] for row in selected])
    pressure = np.asarray([row[1] for row in selected])
    p0 = float(pressure[0])
    relative_height = 44330.0 * (1.0 - np.power(pressure / p0, 0.1903))
    seconds = (stamps - start_ms) / 1000.0
    if len(seconds) > 360:
        seconds, relative_height = map(np.asarray, downsample(seconds, relative_height))
    points = [{"x": round(float(x), 3), "y": round(float(y), 4)} for x, y in zip(seconds, relative_height)]
    metadata = {"sampleCount": len(selected), "startPressureHpa": round(p0, 3), "endPressureHpa": round(float(pressure[-1]), 3), "pressureChangeHpa": round(float(pressure[-1] - p0), 3), "relativeHeightChangeM": round(float(relative_height[-1]), 2)}
    return points, metadata


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


data_dir = ROOT / "Elevator" / "data260917"
floors = {"10A": (8, 2), "10B": (6, 1), "10C": (7, 2), "10D": (8, 2), "10E": (6, 1), "6A": (7, 1), "4A": (8, 2), "4B": (6, 1), "4C": (7, 2), "4D": (8, 2), "4E": (6, 1)}
rides = []
for i, path in enumerate(sorted(p for p in data_dir.iterdir() if p.is_file() and not p.name.startswith(".")), 1):
    match = re.search(r"(10[A-E]|6A|4[A-E])$", path.name)
    if not match:
        continue
    name = match.group(1)
    t, acceleration = module.load_log(path)
    vertical, lateral, start, stop, fs = module.detect(t, acceleration)
    top, bottom = floors[name]
    ride = module.Ride(i, path, name, top, bottom, t, vertical, lateral, start, stop, fs, module.metrics(t, vertical, lateral, start, stop, fs))
    ride.metrics.update(module.ride_features(ride))
    rides.append(ride)
module.classify(rides)

payload = {"date": "2026-09-17", "label": "Uppföljningsmätning 17–18 sep", "status": "complete", "measuredElevators": 11, "totalElevators": 11, "missingElevators": [], "hasBarometer": True, "elevators": []}
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
    barometer_height, barometer = barometer_diagnostics(ride)
    hx, hy = downsample(spatial["floor_position"][::-1], spatial["local_rms"][::-1])
    sx, sy = downsample(spatial["cycles_per_m"], spatial["spatial_amplitude"], 280)
    payload["elevators"].append(
        {
            "id": ride.name,
            "recordedAt": f"{ride.path.name[4:8]}-{ride.path.name[8:10]}-{ride.path.name[10:12]}T{ride.path.name[13:15]}:{ride.path.name[15:17]}:{ride.path.name[17:19]}",
            "topFloor": ride.top,
            "bottomFloor": ride.bottom,
            "profile": [{"x": round(x, 3), "y": round(y, 5)} for x, y in zip(px, py)],
            "velocity": [{"x": round(x, 3), "y": round(y, 5)} for x, y in zip(vx, vy)],
            "spectrum": [{"x": round(x, 4), "y": round(y, 6)} for x, y in zip(fx, fy)],
            "heightEnergy": [{"x": round(x, 3), "y": round(y, 6)} for x, y in zip(hx, hy)],
            "spatialSpectrum": [{"x": round(x, 4), "y": round(y, 6)} for x, y in zip(sx, sy)],
            "barometerHeight": barometer_height,
            "barometer": barometer,
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
(out / "2026-09-17.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
(out / "index.json").write_text(json.dumps({"series": [{"date": "2026-09-17", "label": "Uppföljningsmätning 17–18 sep", "status": "complete", "measuredElevators": 11, "totalElevators": 11}, {"date": "2026-09-13", "label": "Baslinjemätning", "status": "complete", "measuredElevators": 11, "totalElevators": 11}]}, ensure_ascii=False))
print(out / "2026-09-17.json")
