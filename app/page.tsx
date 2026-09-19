"use client";

import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, CalendarDays, RotateCcw } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";

type Point = { x: number; y: number };
type Metrics = { accelerationTime: number; startImpulse: number; startJerk: number; cruiseVibration: number; brakeJerk: number; peakSpeed: number; dominantFrequency: number; dominantAmplitude: number; estimatedDistance: number; dominantCyclesPerMeter: number; spatialPeriod: number; dominantSpatialAmplitude: number; peakVibrationFloor: number; peakLocalVibration: number };
type Barometer = { sampleCount: number; startPressureHpa: number; endPressureHpa: number; pressureChangeHpa: number; relativeHeightChangeM: number };
type Elevator = { id: string; topFloor: number; bottomFloor: number; profile: Point[]; startProfile?: Point[]; stopProfile?: Point[]; velocity: Point[]; spectrum: Point[]; heightEnergy: Point[]; spatialSpectrum: Point[]; barometerHeight?: Point[]; barometer?: Barometer | null; metrics: Metrics };
type Series = { date: string; label: string; status?: "complete" | "partial"; measuredElevators?: number; totalElevators?: number; missingElevators?: string[]; hasBarometer?: boolean; elevators: Elevator[] };

const COLORS = ["#0b5d80", "#e06b34", "#24805d", "#9446a0", "#d13f5b", "#697386", "#b47716", "#008e8d", "#5865cf", "#825b41", "#28384f"];
const ELEVATOR_IDS = ["10A", "10B", "10C", "10D", "10E", "6A", "4A", "4B", "4C", "4D", "4E"];
const DATA_VERSION = "20260919-2";
const colorFor = (id: string) => COLORS[Math.max(0, ELEVATOR_IDS.indexOf(id)) % COLORS.length];
const metricColumns: { key: keyof Metrics; label: string; digits: number }[] = [
  { key: "accelerationTime", label: "Acc.tid s", digits: 1 },
  { key: "startImpulse", label: "Startimpuls", digits: 2 },
  { key: "startJerk", label: "Startjerk", digits: 2 },
  { key: "cruiseVibration", label: "Färdvibration", digits: 3 },
  { key: "brakeJerk", label: "Bromsjerk", digits: 2 },
];

function interpolate(points: Point[], x: number) {
  if (!points.length || x < points[0].x || x > points[points.length - 1].x) return null;
  let lo = 0;
  let hi = points.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (points[mid].x <= x) lo = mid;
    else hi = mid;
  }
  const left = points[lo];
  const right = points[hi];
  if (right.x === left.x) return left.y;
  return left.y + (right.y - left.y) * ((x - left.x) / (right.x - left.x));
}

function Plot({ title, note, elevators, historical, field, xLabel, yLabel }: { title: string; note: string; elevators: Elevator[]; historical: Elevator[]; field: "profile" | "startProfile" | "stopProfile" | "velocity" | "spectrum" | "heightEnergy" | "spatialSpectrum" | "barometerHeight"; xLabel: string; yLabel: string }) {
  const series = useMemo(() => [
    ...historical.map((elevator, index) => ({ key: `history_${index}`, name: `${elevator.id} historisk`, points: elevator[field] ?? [], elevator, historical: true })),
    ...elevators.map((elevator, index) => ({ key: `current_${index}`, name: elevator.id, points: elevator[field] ?? [], elevator, historical: false })),
  ], [elevators, historical, field]);
  const chartData = useMemo(() => {
    const populated = series.filter((item) => item.points.length);
    if (!populated.length) return [];
    const minX = Math.min(...populated.map((item) => item.points[0].x));
    const maxX = Math.max(...populated.map((item) => item.points[item.points.length - 1].x));
    return Array.from({ length: 321 }, (_, index) => {
      const x = minX + (maxX - minX) * index / 320;
      return Object.fromEntries([["x", x], ...populated.map((item) => [item.key, interpolate(item.points, x)])]);
    });
  }, [series]);
  return <section className="panel min-h-[330px]">
    <div className="mb-3"><h2>{title}</h2><p className="panel-note">{note}</p></div>
    <div className="h-[250px] w-full" aria-label={title}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 6, right: 12, bottom: 18, left: 6 }}>
          <CartesianGrid stroke="#dbe5ea" strokeDasharray="2 4" />
          <XAxis dataKey="x" type="number" domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#52636d" }} label={{ value: xLabel, position: "insideBottom", offset: -11, fontSize: 11 }} />
          <YAxis type="number" domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#52636d" }} width={52} label={{ value: yLabel, angle: -90, position: "insideLeft", fontSize: 11 }} />
          <Tooltip filterNull formatter={(value, name) => [Number(value).toFixed(3), String(name)]} labelFormatter={(value) => `${xLabel}: ${Number(value).toFixed(2)}`} contentStyle={{ borderRadius: 10, borderColor: "#cbd8de", fontSize: 12 }} />
          {series.map((item) => <Line key={`${item.key}-${field}`} dataKey={item.key} name={item.name} stroke={colorFor(item.elevator.id)} strokeWidth={item.historical ? 1.5 : 2} strokeDasharray={item.historical ? "7 5" : undefined} dot={false} activeDot={{ r: 3 }} isAnimationActive={false} opacity={item.historical ? 0.7 : 1} connectNulls={false} />)}
        </LineChart>
      </ResponsiveContainer>
    </div>
  </section>;
}

function MetricMatrix({ elevators }: { elevators: Elevator[] }) {
  const ranges = useMemo(() => Object.fromEntries(metricColumns.map(({ key }) => {
    const values = elevators.map((e) => e.metrics[key]);
    return [key, [Math.min(...values), Math.max(...values)]];
  })) as Record<keyof Metrics, [number, number]>, [elevators]);
  return <section className="panel overflow-x-auto">
    <h2>Jämförande rörelseegenskaper</h2><p className="panel-note mb-4">Mörkare ton betyder högre värde inom den valda gruppen.</p>
    <table className="metric-table"><thead><tr><th>Hiss</th>{metricColumns.map((m) => <th key={m.key}>{m.label}</th>)}</tr></thead><tbody>
      {elevators.map((elevator) => <tr key={elevator.id}><th>{elevator.id}</th>{metricColumns.map(({ key, digits }) => {
        const [min, max] = ranges[key]; const level = max === min ? 0 : (elevator.metrics[key] - min) / (max - min);
        return <td key={key} style={{ backgroundColor: `color-mix(in srgb, #e85c3f ${14 + level * 66}%, #f5fafb)` }}>{elevator.metrics[key].toFixed(digits)}</td>;
      })}</tr>)}
    </tbody></table>
  </section>;
}

function centeredProfile(points: Point[]) {
  if (!points.length) return points;
  const edge = Math.max(1, Math.floor(points.length * 0.06));
  const baselinePoints = [...points.slice(0, edge), ...points.slice(-edge)];
  const baseline = baselinePoints.reduce((sum, point) => sum + point.y, 0) / baselinePoints.length;
  return points.map((point) => ({ x: point.x, y: point.y - baseline }));
}

function profileDistance(left: Point[], right: Point[]) {
  const a = centeredProfile(left);
  const b = centeredProfile(right);
  if (!a.length || !b.length) return 0;
  const start = Math.max(a[0].x, b[0].x);
  const stop = Math.min(a[a.length - 1].x, b[b.length - 1].x);
  if (stop <= start) return 0;
  const squared = Array.from({ length: 121 }, (_, index) => {
    const x = start + (stop - start) * index / 120;
    const delta = (interpolate(a, x) ?? 0) - (interpolate(b, x) ?? 0);
    return delta * delta;
  });
  return Math.sqrt(squared.reduce((sum, value) => sum + value, 0) / squared.length);
}

function percentChange(current: number, previous: number) {
  return previous ? Math.round(100 * (current - previous) / previous) : 0;
}

function median(values: number[]) {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return 0;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function ElevatorAssessments({ current, history, elevators }: { current: Series; history: Series | null; elevators: Elevator[] }) {
  const assessments = useMemo(() => {
    const previous = new Map(history?.elevators.map((elevator) => [elevator.id, elevator]) ?? []);
    const medians = {
      startImpulse: median(current.elevators.map((elevator) => elevator.metrics.startImpulse)),
      startJerk: median(current.elevators.map((elevator) => elevator.metrics.startJerk)),
      brakeJerk: median(current.elevators.map((elevator) => elevator.metrics.brakeJerk)),
      vibration: median(current.elevators.map((elevator) => elevator.metrics.cruiseVibration)),
    };
    return elevators.map((elevator) => {
      const old = previous.get(elevator.id);
      const peers = current.elevators.filter((item) => item.id[0] === elevator.id[0] && item.id !== elevator.id);
      const oldPeers = history?.elevators.filter((item) => item.id[0] === elevator.id[0] && item.id !== elevator.id) ?? [];
      const peerDistance = peers.length ? peers.reduce((sum, peer) => sum + profileDistance(elevator.profile, peer.profile), 0) / peers.length : 0;
      const oldPeerDistance = old && oldPeers.length ? oldPeers.reduce((sum, peer) => sum + profileDistance(old.profile, peer.profile), 0) / oldPeers.length : 0;
      const issues: string[] = [];
      if (elevator.metrics.startImpulse > Math.max(0.65, medians.startImpulse * 1.35)) issues.push("hög startimpuls");
      if (elevator.metrics.startJerk > Math.max(0.55, medians.startJerk * 1.45)) issues.push("hög startjerk");
      if (elevator.metrics.brakeJerk > Math.max(0.4, medians.brakeJerk * 1.45)) issues.push("hög bromsjerk");
      if (elevator.metrics.cruiseVibration > Math.max(0.06, medians.vibration * 1.5)) issues.push("hög färdvibration");
      const profileChange = old ? profileDistance(elevator.profile, old.profile) : 0;
      const changed = profileChange > 0.045;
      const status = issues.length ? "Följ upp" : changed ? "Förändrad profil" : "Liknar gruppen";
      const now = issues.length ? `Nu avviker ${issues.join(", ")}.` : "Nu ligger start, stopp och färdvibration nära gruppens centrala nivåer.";
      const relative = peers.length ? (peerDistance < 0.055 ? "Styrprofilen ligger nära hissarna i samma portgrupp." : "Styrprofilen skiljer sig från flera hissar i samma portgrupp.") : "Gruppjämförelsen är begränsad.";
      let change = "Ingen historisk jämförelse är vald.";
      if (old) {
        const changes: string[] = [];
        if (changed) changes.push("styrprofilen har förändrats tydligt");
        else if (profileChange < 0.02) changes.push("styrprofilen är väl reproducerad");
        else changes.push("styrprofilen har förändrats måttligt");
        if (oldPeerDistance > 0 && peerDistance < oldPeerDistance * 0.8) changes.push("den ansluter nu bättre till portgruppen");
        const startChange = percentChange(elevator.metrics.startImpulse, old.metrics.startImpulse);
        const stopChange = percentChange(elevator.metrics.brakeJerk, old.metrics.brakeJerk);
        if (Math.abs(startChange) >= 25) changes.push(`startimpulsen är ${Math.abs(startChange)} % ${startChange > 0 ? "högre" : "lägre"}`);
        if (Math.abs(stopChange) >= 30) changes.push(`bromsjerken är ${Math.abs(stopChange)} % ${stopChange > 0 ? "högre" : "lägre"}`);
        change = `Sedan ${history?.date}: ${changes.join("; ")}.`;
      }
      return { id: elevator.id, status, now, relative, change };
    });
  }, [current, history, elevators]);

  return <section className="panel">
    <h2>Bedömning per hiss</h2>
    <p className="panel-note mb-4">Automatisk relativ screening. Välj färre hissar ovan för en kortare lista.</p>
    <div className="divide-y divide-slate-200">
      {assessments.map((item) => <article key={item.id} className="py-3 first:pt-0 last:pb-0">
        <div className="mb-1 flex flex-wrap items-center gap-2"><h3 className="font-bold text-slate-900">{item.id}</h3><span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">{item.status}</span></div>
        <p className="text-sm leading-6 text-slate-700">{item.now} {item.relative} {item.change}</p>
      </article>)}
    </div>
  </section>;
}

export default function Home() {
  const [current, setCurrent] = useState<Series | null>(null);
  const [history, setHistory] = useState<Series | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [currentDate, setCurrentDate] = useState("2026-09-17");
  const [comparisonDate, setComparisonDate] = useState("2026-09-13");
  const [dateMessage, setDateMessage] = useState("");

  useEffect(() => { fetch(`/data/${currentDate}.json?v=${DATA_VERSION}`).then((r) => { if (!r.ok) throw new Error("Mätserien saknas"); return r.json(); }).then((data: Series) => { setCurrent(data); setDateMessage(""); setSelected((old) => old.length ? old : data.elevators.map((e) => e.id)); }).catch(() => setDateMessage(`Ingen mätserie finns för ${currentDate}. Senaste giltiga serie visas.`)); }, [currentDate]);
  useEffect(() => {
    if (!comparisonDate) {
      Promise.resolve().then(() => setHistory(null));
      return;
    }
    fetch(`/data/${comparisonDate}.json?v=${DATA_VERSION}`).then((r) => r.ok ? r.json() : Promise.reject()).then((data) => { setHistory(data); setDateMessage(""); }).catch(() => { setHistory(null); setDateMessage(`Ingen historisk mätserie finns för ${comparisonDate}.`); });
  }, [comparisonDate]);

  const visible = current?.elevators.filter((e) => selected.includes(e.id)) ?? [];
  const historical = history?.elevators.filter((e) => selected.includes(e.id)) ?? [];
  const byId = current?.elevators ?? [];
  const strongest = [...byId].sort((a, b) => b.metrics.dominantAmplitude - a.metrics.dominantAmplitude).slice(0, 4);
  const shortest = [...byId].sort((a, b) => a.metrics.accelerationTime - b.metrics.accelerationTime)[0];
  const longest = [...byId].sort((a, b) => b.metrics.accelerationTime - a.metrics.accelerationTime)[0];
  if (!current) return <main className="grid min-h-screen place-items-center bg-slate-50">Laddar mätningen…</main>;

  const toggle = (id: string) => setSelected((value) => value.includes(id) ? value.filter((x) => x !== id) : [...value, id]);
  const solo = (id: string) => setSelected((value) => value.length === 1 && value[0] === id ? byId.map((e) => e.id) : [id]);

  return <main className="min-h-screen bg-[#eef4f6] text-slate-950">
    <header className="border-b border-[#c8d7dd] bg-[#0c3444] text-white"><div className="mx-auto flex max-w-[1600px] flex-col gap-5 px-5 py-5 lg:flex-row lg:items-end lg:justify-between lg:px-8">
      <div><div className="mb-2 flex items-center gap-2 text-sm text-cyan-100"><Activity size={17} /> BRF hissanalys</div><h1>Hissövervakning</h1><p className="mt-1 max-w-2xl text-sm text-slate-200">Jämför styrprofil och mekaniska vibrationssignaturer mellan hissar och mättillfällen.</p></div>
      <div className="date-controls"><label><span>Aktuell mätning</span><input type="date" value={currentDate} onChange={(e) => setCurrentDate(e.target.value)} /></label><div className="line-key"><span className="solid-line" /> Heldragen</div><label><span>Historisk jämförelse</span><input type="date" value={comparisonDate} onChange={(e) => setComparisonDate(e.target.value)} /></label><div className="line-key"><span className="dashed-line" /> Streckad</div></div>
    </div></header>

    <div className="mx-auto max-w-[1600px] px-5 py-5 lg:px-8">
      <section className="selector-bar" aria-label="Välj hissar"><div className="flex flex-wrap items-center gap-2"><span className="mr-2 text-sm font-semibold text-slate-700">Visa hissar</span>
        {byId.map((elevator) => <div key={elevator.id} className={`elevator-toggle ${selected.includes(elevator.id) ? "selected" : ""}`}><Checkbox checked={selected.includes(elevator.id)} onCheckedChange={() => toggle(elevator.id)} aria-label={`Visa ${elevator.id}`} style={{ backgroundColor: selected.includes(elevator.id) ? colorFor(elevator.id) : undefined, borderColor: colorFor(elevator.id) }} /><button onClick={() => solo(elevator.id)} title={`Visa endast ${elevator.id}`}>{elevator.id}</button></div>)}
      </div><div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => setSelected(byId.map((e) => e.id))}>Alla</Button><Button variant="outline" size="sm" onClick={() => setSelected([])}>Ingen</Button><Button variant="ghost" size="sm" onClick={() => { setComparisonDate(""); setSelected(byId.map((e) => e.id)); }}><RotateCcw /> Återställ</Button></div></section>
      <div className="history-hint"><CalendarDays size={16} /><span>{current.status === "partial" && <>Partiell mätning: {current.measuredElevators || current.elevators.length} av {current.totalElevators || ELEVATOR_IDS.length} hissar. Saknas: {(current.missingElevators || []).join(", ")}. </>}{history ? history.date + " visas streckad som jämförelse." : dateMessage || "Ingen historisk jämförelse vald."}</span></div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Plot title="Tidsnormaliserad acceleration" note="Profilernas form visar skillnader i acceleration och jerk. Heldragen kurva är aktuell mätning; streckad är baslinjen." elevators={visible} historical={historical} field="profile" xLabel="andel av färd %" yLabel="m/s²" />
        <Plot title="Skattad driftkorrigerad hastighet" note={`${shortest?.id} har kortast accelerationsfas (${shortest?.metrics.accelerationTime.toFixed(1)} s); ${longest?.id} har längst (${longest?.metrics.accelerationTime.toFixed(1)} s).`} elevators={visible} historical={historical} field="velocity" xLabel="sekunder" yLabel="m/s" />
        <Plot title="Startförlopp" note="Acceleration lågpassfiltrerad vid 5 Hz, lokalt nollställd och justerad så att detekterad start ligger vid 0 s. Korta toppar kan motsvara ett upplevt tillhopp." elevators={visible} historical={historical} field="startProfile" xLabel="sekunder från start" yLabel="m/s²" />
        <Plot title="Stoppförlopp" note="Detekterad inbromsning ligger vid 0 s. En mjuk, sammanhängande kurva är jämnare än flera snabba riktningsbyten eller en kort topp." elevators={visible} historical={historical} field="stopProfile" xLabel="sekunder från inbromsning" yLabel="m/s²" />
        <Plot title="Glättat vibrationsspektrum" note={`Starkast periodiska signaturer: ${strongest.map((e) => `${e.id} ${e.metrics.dominantFrequency.toFixed(1)} Hz`).join(", ")}.`} elevators={visible} historical={historical} field="spectrum" xLabel="Hz" yLabel="amplitud m/s²" />
        <Plot title="Rumsligt vibrationsspektrum" note="Flera hissar grupperar sig kring 5,6 cykler/m, vilket kan vara en gemensam mekanisk signatur. 10A avviker kring 8,1 cykler/m och har ett planerat hjulbyte." elevators={visible} historical={historical} field="spatialSpectrum" xLabel="cykler/m" yLabel="amplitud m/s²" />
        <Plot title="Vibrationsenergi mot våningsläge" note="En lokal topp blir diagnostisk först om den återkommer vid samma läge i flera resor." elevators={visible} historical={historical} field="heightEnergy" xLabel="skattat våningsläge" yLabel="RMS m/s²" />
        <Plot title="Barometrisk höjdförändring" note="Ny försökskanal i mätningen 17 september. Relativ höjd är nollställd vid resans början; negativ riktning motsvarar färd nedåt." elevators={visible} historical={historical} field="barometerHeight" xLabel="sekunder" yLabel="relativ höjd m" />
      </div>

      <section className="mt-5 grid items-start gap-5 xl:grid-cols-2">
        {visible.length ? <MetricMatrix elevators={visible} /> : <section className="panel empty-selection"><p>Välj minst en hiss för att visa nyckeltal och bedömningar.</p></section>}
        {visible.length ? <ElevatorAssessments current={current} history={history} elevators={visible} /> : null}
      </section>
    </div>
  </main>;
}
