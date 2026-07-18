import { useEffect, useState, useCallback } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Activity, ShieldAlert, Zap, LayoutDashboard, History,
  Crosshair, BarChart3, RefreshCw, AlertTriangle,
  CheckCircle, XCircle, Clock, TrendingUp, Cpu,
} from "lucide-react"
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip,
  BarChart, Bar, PieChart, Pie, Cell,
} from "recharts"

const API = "http://localhost:8000"

// ─── Types ─────────────────────────────────────────────────────────────────

interface Run {
  id: number; agent_name: string; task: string; model_name: string;
  status: string; success: boolean | null; started_at: string | null;
  finished_at: string | null; duration_ms: number | null; ari_score: number | null;
}
interface Failure {
  id: number; run_id: number; type: string;
  root_cause: string; recommendation: string | null; created_at: string;
}
interface SecurityEvent {
  id: number; run_id: number; direction: string; detector: string;
  risk_type: string; owasp_category: string | null; severity: number;
  details: Record<string, string> | null; created_at: string;
}
interface Metrics {
  total_runs: number; successful_runs: number; failed_runs: number;
  success_rate: number; average_ari: number | null; average_latency_ms: number | null;
  total_failures: number; total_security_events: number;
  ari_distribution: { excellent: number; good: number; fair: number; poor: number };
}
interface ArenaData {
  matches: { id: number; task: string; winner: string; details: Record<string, Record<string, unknown>>; created_at: string }[];
  leaderboard: { model: string; wins: number; matches: number; avg_ari?: number }[];
}
interface ReplayStep {
  step: number; type: string; node: string | null; content: unknown; timestamp: string;
}
interface RunDetail extends Run {
  traces: ReplayStep[]; tool_calls: unknown[]; scores: { metric_name: string; value: number }[];
  failures: Failure[]; security_events: SecurityEvent[];
}
interface OllamaModel { name: string; size?: number; modified_at?: string; }

// ─── Helpers ───────────────────────────────────────────────────────────────

function ariBucket(score: number | null): string {
  if (score === null) return "—"
  if (score >= 85) return "Excellent"
  if (score >= 70) return "Good"
  if (score >= 50) return "Fair"
  return "Poor"
}
function ariColor(score: number | null): string {
  if (score === null) return "text-muted-foreground"
  if (score >= 85) return "text-emerald-400"
  if (score >= 70) return "text-blue-400"
  if (score >= 50) return "text-amber-400"
  return "text-rose-400"
}
function statusIcon(status: string) {
  if (status === "success") return <CheckCircle className="w-4 h-4 text-emerald-400" />
  if (status === "failure") return <XCircle className="w-4 h-4 text-rose-400" />
  return <Clock className="w-4 h-4 text-amber-400 animate-spin" />
}
function fmtMs(ms: number | null) { return ms ? `${(ms / 1000).toFixed(1)}s` : "—" }
function fmtDate(iso: string | null) {
  if (!iso) return "—"
  return new Date(iso).toLocaleString([], { dateStyle: "short", timeStyle: "short" })
}

const PIE_COLORS = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#f43f5e", "#ec4899"]

// ─── Shared loading/error ───────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex items-center justify-center h-40 text-muted-foreground gap-2">
      <RefreshCw className="w-5 h-5 animate-spin" /> Loading…
    </div>
  )
}
function ErrState({ msg }: { msg: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-40 text-muted-foreground gap-2">
      <AlertTriangle className="w-8 h-8 text-amber-400" />
      <p className="text-sm">{msg}</p>
    </div>
  )
}

// ─── StatCard ──────────────────────────────────────────────────────────────

function StatCard({ title, value, sub, icon, color = "" }: {
  title: string; value: string | number; sub?: string; icon: React.ReactNode; color?: string
}) {
  return (
    <Card className="border-border/40 glass hover:glow-purple transition-all duration-200">
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-extrabold ${color}`}>{value}</div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  )
}

// ─── Overview ──────────────────────────────────────────────────────────────

function OverviewTab({ runs }: { runs: Run[] }) {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/metrics`).then(r => r.json()).then(setMetrics).catch(console.error).finally(() => setLoading(false))
  }, [])

  const chartData = runs.slice(0, 20).reverse().map((r) => ({
    name: `#${r.id}`,
    ari: r.ari_score ?? 0,
  }))

  const distData = metrics ? [
    { name: "Excellent", value: metrics.ari_distribution.excellent, color: "#10b981" },
    { name: "Good", value: metrics.ari_distribution.good, color: "#3b82f6" },
    { name: "Fair", value: metrics.ari_distribution.fair, color: "#f59e0b" },
    { name: "Poor", value: metrics.ari_distribution.poor, color: "#f43f5e" },
  ] : []

  if (loading) return <Spinner />

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Runs" value={metrics?.total_runs ?? 0} sub="all time" icon={<History className="w-4 h-4 text-muted-foreground" />} />
        <StatCard title="Average ARI" value={metrics?.average_ari != null ? metrics.average_ari.toFixed(1) : "—"}
          sub={metrics?.average_ari != null ? ariBucket(metrics.average_ari) : "no data"}
          icon={<Activity className="w-4 h-4 text-muted-foreground" />}
          color={ariColor(metrics?.average_ari ?? null)} />
        <StatCard title="Success Rate" value={`${metrics?.success_rate ?? 0}%`}
          sub={`${metrics?.successful_runs ?? 0} of ${metrics?.total_runs ?? 0} runs`}
          icon={<TrendingUp className="w-4 h-4 text-muted-foreground" />}
          color={(metrics?.success_rate ?? 0) >= 80 ? "text-emerald-400" : "text-amber-400"} />
        <StatCard title="Security Alerts" value={metrics?.total_security_events ?? 0}
          sub={`${metrics?.total_failures ?? 0} failures detected`}
          icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
          color={(metrics?.total_security_events ?? 0) > 0 ? "text-rose-400" : "text-emerald-400"} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-border/40 glass">
          <CardHeader>
            <CardTitle className="text-sm">ARI Over Recent Runs</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length === 0 ? (
              <ErrState msg="No run data yet — trace an agent to populate this chart." />
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "hsl(var(--background))", border: "1px solid hsl(var(--border))" }} />
                  <Line type="monotone" dataKey="ari" stroke="hsl(258,90%,66%)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/40 glass">
          <CardHeader><CardTitle className="text-sm">ARI Distribution</CardTitle></CardHeader>
          <CardContent>
            {distData.every(d => d.value === 0) ? (
              <ErrState msg="No ARI data yet." />
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={distData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                    {distData.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// ─── Runs ──────────────────────────────────────────────────────────────────

function RunsTab({ runs, loading }: { runs: Run[]; loading: boolean }) {
  const [selected, setSelected] = useState<RunDetail | null>(null)
  const [, setDetailLoading] = useState(false)

  const openDetail = async (id: number) => {
    setDetailLoading(true)
    try {
      const r = await fetch(`${API}/runs/${id}`).then(r => r.json())
      setSelected(r)
    } finally {
      setDetailLoading(false)
    }
  }

  if (loading) return <Spinner />

  if (selected) {
    return (
      <div className="animate-fade-in space-y-4">
        <button onClick={() => setSelected(null)} className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1">
          ← Back to runs
        </button>
        <Card className="border-border/40 glass">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                {statusIcon(selected.status)} Run #{selected.id} — {selected.agent_name}
              </CardTitle>
              <Badge variant={selected.success ? "default" : "destructive"}>{selected.status}</Badge>
            </div>
            <CardDescription>{selected.task}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div><span className="text-muted-foreground">Model</span><div className="font-medium mono">{selected.model_name}</div></div>
              <div><span className="text-muted-foreground">Duration</span><div className="font-medium">{fmtMs(selected.duration_ms)}</div></div>
              <div><span className="text-muted-foreground">ARI</span><div className={`text-2xl font-bold ${ariColor(selected.ari_score)}`}>{selected.ari_score?.toFixed(1) ?? "—"}</div></div>
            </div>
            {selected.scores.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">ARI Components</p>
                <div className="grid grid-cols-2 gap-2">
                  {selected.scores.map(s => (
                    <div key={s.metric_name} className="bg-muted/30 rounded p-2 text-sm">
                      <span className="text-muted-foreground capitalize">{s.metric_name.replace(/_/g, " ")}</span>
                      <div className="font-bold">{s.value.toFixed(1)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {selected.traces.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Trace Steps ({selected.traces.length})</p>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {selected.traces.map(t => (
                    <div key={t.step} className="flex gap-2 text-xs bg-muted/20 rounded px-2 py-1">
                      <span className="text-muted-foreground w-6">{t.step}</span>
                      <Badge variant="outline" className="text-xs">{t.type}</Badge>
                      <span className="text-muted-foreground">{t.node ?? "—"}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <Card className="border-border/40 glass">
        <CardHeader>
          <CardTitle>Agent Runs</CardTitle>
          <CardDescription>Click a row to view full details, traces, and scores.</CardDescription>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <ErrState msg="No runs yet — run `orbit trace` to create your first run." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/40 text-muted-foreground">
                    <th className="text-left py-2 px-3">ID</th>
                    <th className="text-left py-2 px-3">Agent</th>
                    <th className="text-left py-2 px-3">Model</th>
                    <th className="text-left py-2 px-3">Status</th>
                    <th className="text-right py-2 px-3">ARI</th>
                    <th className="text-right py-2 px-3">Duration</th>
                    <th className="text-left py-2 px-3">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map(r => (
                    <tr key={r.id} onClick={() => openDetail(r.id)}
                      className="border-b border-border/20 hover:bg-muted/20 cursor-pointer transition-colors">
                      <td className="py-2 px-3 font-mono text-muted-foreground">#{r.id}</td>
                      <td className="py-2 px-3 font-medium">{r.agent_name}</td>
                      <td className="py-2 px-3 mono text-xs text-muted-foreground">{r.model_name}</td>
                      <td className="py-2 px-3"><div className="flex items-center gap-1">{statusIcon(r.status)} {r.status}</div></td>
                      <td className={`py-2 px-3 text-right font-bold ${ariColor(r.ari_score)}`}>{r.ari_score?.toFixed(1) ?? "—"}</td>
                      <td className="py-2 px-3 text-right text-muted-foreground">{fmtMs(r.duration_ms)}</td>
                      <td className="py-2 px-3 text-muted-foreground text-xs">{fmtDate(r.started_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Failures ──────────────────────────────────────────────────────────────

function FailuresTab() {
  const [failures, setFailures] = useState<Failure[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/failures`).then(r => r.json()).then(setFailures).catch(console.error).finally(() => setLoading(false))
  }, [])

  const grouped = failures.reduce<Record<string, Failure[]>>((acc, f) => {
    acc[f.type] = acc[f.type] ? [...acc[f.type], f] : [f]
    return acc
  }, {})

  if (loading) return <Spinner />

  return (
    <div className="animate-fade-in space-y-4">
      {Object.keys(grouped).length === 0 ? (
        <Card className="border-border/40 glass">
          <CardContent className="pt-10 pb-10 text-center">
            <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <p className="text-muted-foreground">No failures detected yet.</p>
          </CardContent>
        </Card>
      ) : (
        Object.entries(grouped).map(([type, items]) => (
          <Card key={type} className="border-border/40 glass">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <CardTitle className="text-sm capitalize">{type.replace(/_/g, " ")} ({items.length})</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {items.map(f => (
                  <div key={f.id} className="bg-muted/20 rounded p-3 text-sm space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">Run #{f.run_id}</Badge>
                      <span className="text-xs text-muted-foreground">{fmtDate(f.created_at)}</span>
                    </div>
                    <p>{f.root_cause}</p>
                    {f.recommendation && <p className="text-muted-foreground text-xs">→ {f.recommendation}</p>}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}

// ─── Arena ─────────────────────────────────────────────────────────────────

function ArenaTab() {
  const [arena, setArena] = useState<ArenaData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/arena`).then(r => r.json()).then(setArena).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const leaderboard = arena?.leaderboard ?? []
  const matches = arena?.matches ?? []

  return (
    <div className="animate-fade-in space-y-4">
      <Card className="border-border/40 glass">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-purple-400" />
            <CardTitle>Model Leaderboard</CardTitle>
          </div>
          <CardDescription>Ranked by Arena wins. Run `orbit battle` to populate.</CardDescription>
        </CardHeader>
        <CardContent>
          {leaderboard.length === 0 ? (
            <ErrState msg="No arena matches yet — run `orbit battle --task '...' --models llama3.1 qwen2.5`" />
          ) : (
            <div className="space-y-3">
              {leaderboard.map((m, i) => (
                <div key={m.model} className="flex items-center gap-3 bg-muted/20 rounded p-3">
                  <span className={`text-2xl font-extrabold w-8 ${i === 0 ? "text-amber-400" : "text-muted-foreground"}`}>#{i + 1}</span>
                  <div className="flex-1">
                    <div className="font-semibold mono">{m.model}</div>
                    <div className="text-xs text-muted-foreground">{m.wins} wins / {m.matches} matches</div>
                  </div>
                  {m.avg_ari !== undefined && (
                    <div className={`text-xl font-bold ${ariColor(m.avg_ari)}`}>{m.avg_ari.toFixed(1)}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-border/40 glass">
        <CardHeader><CardTitle>Match History</CardTitle></CardHeader>
        <CardContent>
          {matches.length === 0 ? (
            <ErrState msg="No match history." />
          ) : (
            <div className="space-y-2">
              {matches.map(m => (
                <div key={m.id} className="bg-muted/20 rounded p-3 text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{m.task}</span>
                    <span className="text-xs text-muted-foreground">{fmtDate(m.created_at)}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">Winner: <span className="text-emerald-400 font-semibold">{m.winner}</span></div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Replay ────────────────────────────────────────────────────────────────

function ReplayTab({ runs }: { runs: Run[] }) {
  const [runId, setRunId] = useState<string>("")
  const [replay, setReplay] = useState<{ steps: ReplayStep[]; run_id: number; agent_name: string; status: string; duration_ms: number | null } | null>(null)
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0)

  const load = async () => {
    if (!runId) return
    setLoading(true)
    try {
      const r = await fetch(`${API}/runs/${runId}/replay`).then(r => r.json())
      setReplay(r)
      setStep(0)
    } finally { setLoading(false) }
  }

  return (
    <div className="animate-fade-in space-y-4">
      <Card className="border-border/40 glass">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" />
            <CardTitle>Failure Replay</CardTitle>
          </div>
          <CardDescription>Select a run to step through its execution timeline.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <select value={runId} onChange={e => setRunId(e.target.value)}
              className="flex-1 bg-muted/30 border border-border/40 rounded px-3 py-2 text-sm">
              <option value="">Select a run…</option>
              {runs.map(r => (
                <option key={r.id} value={r.id}>
                  #{r.id} — {r.agent_name} ({r.status}) {r.ari_score != null ? `ARI:${r.ari_score.toFixed(0)}` : ""}
                </option>
              ))}
            </select>
            <button onClick={load} disabled={!runId || loading}
              className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-4 py-2 rounded text-sm transition-colors">
              {loading ? "Loading…" : "Load Replay"}
            </button>
          </div>

          {replay && replay.steps.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>Step {step + 1} of {replay.steps.length}</span>
                <span>—</span>
                <span>{replay.agent_name}</span>
                <Badge variant={replay.status === "success" ? "default" : "destructive"}>{replay.status}</Badge>
              </div>

              <input type="range" min={0} max={replay.steps.length - 1} value={step}
                onChange={e => setStep(Number(e.target.value))}
                className="w-full accent-purple-500" />

              <div className="space-y-1 max-h-64 overflow-y-auto">
                {replay.steps.slice(0, step + 1).map((s, i) => {
                  const isCurrent = i === step
                  return (
                    <div key={i} className={`flex gap-3 rounded px-3 py-2 text-xs transition-colors ${isCurrent ? "bg-purple-500/20 border border-purple-500/30" : "bg-muted/15"}`}>
                      <span className="text-muted-foreground w-6 text-right">{s.step}</span>
                      <Badge variant="outline" className="text-xs shrink-0">{s.type}</Badge>
                      <span className="text-muted-foreground shrink-0">{s.node ?? "—"}</span>
                      <span className="text-muted-foreground truncate">{s.timestamp.slice(11, 19)}</span>
                    </div>
                  )
                })}
              </div>

              {/* Current step detail */}
              {replay.steps[step] && (
                <div className="bg-muted/20 rounded p-3 text-xs">
                  <div className="font-semibold mb-1">Step {step + 1} — {replay.steps[step].type}</div>
                  <pre className="whitespace-pre-wrap text-muted-foreground overflow-x-auto">
                    {JSON.stringify(replay.steps[step].content, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          {replay && replay.steps.length === 0 && (
            <ErrState msg="No trace steps found for this run. Ensure the agent emits trace events." />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Models ────────────────────────────────────────────────────────────────

function ModelsTab() {
  const [data, setData] = useState<{ db_models: unknown[]; ollama_models: OllamaModel[] } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/models`).then(r => r.json()).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div className="animate-fade-in space-y-4">
      <Card className="border-border/40 glass">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-400" />
            <CardTitle>Ollama Models (Live)</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {(data?.ollama_models ?? []).length === 0 ? (
            <ErrState msg="No Ollama models found. Is Ollama running? Try `ollama pull llama3.1`." />
          ) : (
            <div className="grid gap-2 sm:grid-cols-2">
              {data!.ollama_models.map(m => (
                <div key={m.name} className="flex items-center gap-3 bg-muted/20 rounded p-3">
                  <Zap className="w-4 h-4 text-purple-400 shrink-0" />
                  <div>
                    <div className="font-semibold mono text-sm">{m.name}</div>
                    {m.size && <div className="text-xs text-muted-foreground">{(m.size / 1e9).toFixed(1)} GB</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Security ──────────────────────────────────────────────────────────────

function SecurityTab() {
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [summary, setSummary] = useState<{
    total_events: number; affected_runs: number;
    by_owasp_category: Record<string, number>; by_risk_type: Record<string, number>
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/security/events`).then(r => r.json()),
      fetch(`${API}/security/summary`).then(r => r.json()),
    ]).then(([e, s]) => { setEvents(e); setSummary(s) }).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const owaspData = summary
    ? Object.entries(summary.by_owasp_category).map(([name, value]) => ({ name, value }))
    : []

  return (
    <div className="animate-fade-in space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard title="Total Events" value={summary?.total_events ?? 0}
          icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
          color={(summary?.total_events ?? 0) > 0 ? "text-rose-400" : "text-emerald-400"} />
        <StatCard title="Affected Runs" value={summary?.affected_runs ?? 0}
          icon={<AlertTriangle className="w-4 h-4 text-amber-400" />} />
        <StatCard title="Unique Risk Types" value={Object.keys(summary?.by_risk_type ?? {}).length}
          icon={<Activity className="w-4 h-4 text-muted-foreground" />} />
      </div>

      {owaspData.length > 0 && (
        <Card className="border-border/40 glass">
          <CardHeader><CardTitle className="text-sm">Events by OWASP Category</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={owaspData}>
                <XAxis dataKey="name" tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "hsl(var(--background))", border: "1px solid hsl(var(--border))" }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {owaspData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <Card className="border-border/40 glass">
        <CardHeader><CardTitle className="text-sm">Security Event Log</CardTitle></CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
              <p className="text-muted-foreground text-sm">No security events recorded yet.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border/40 text-muted-foreground">
                    <th className="text-left py-2 px-2">Run</th>
                    <th className="text-left py-2 px-2">Direction</th>
                    <th className="text-left py-2 px-2">Detector</th>
                    <th className="text-left py-2 px-2">Risk</th>
                    <th className="text-left py-2 px-2">OWASP</th>
                    <th className="text-right py-2 px-2">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map(e => (
                    <tr key={e.id} className="border-b border-border/20 hover:bg-muted/10">
                      <td className="py-1.5 px-2 mono">#{e.run_id}</td>
                      <td className="py-1.5 px-2"><Badge variant="outline" className="text-xs">{e.direction}</Badge></td>
                      <td className="py-1.5 px-2 text-muted-foreground">{e.detector}</td>
                      <td className="py-1.5 px-2 text-rose-400">{e.risk_type}</td>
                      <td className="py-1.5 px-2 text-muted-foreground">{e.owasp_category ?? "—"}</td>
                      <td className="py-1.5 px-2 text-right font-bold">{e.severity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Analytics ─────────────────────────────────────────────────────────────

function AnalyticsTab({ runs }: { runs: Run[] }) {
  const latencyData = runs
    .filter(r => r.duration_ms != null)
    .slice(0, 30)
    .reverse()
    .map(r => ({ name: `#${r.id}`, latency: Math.round((r.duration_ms ?? 0) / 1000) }))

  const modelCounts = runs.reduce<Record<string, number>>((acc, r) => {
    acc[r.model_name] = (acc[r.model_name] ?? 0) + 1
    return acc
  }, {})
  const modelData = Object.entries(modelCounts).map(([name, value]) => ({ name, value }))

  return (
    <div className="animate-fade-in space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-border/40 glass">
          <CardHeader><CardTitle className="text-sm">Latency Over Runs (seconds)</CardTitle></CardHeader>
          <CardContent>
            {latencyData.length === 0 ? <ErrState msg="No latency data yet." /> : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={latencyData}>
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "hsl(var(--background))", border: "1px solid hsl(var(--border))" }} />
                  <Bar dataKey="latency" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/40 glass">
          <CardHeader><CardTitle className="text-sm">Runs per Model</CardTitle></CardHeader>
          <CardContent>
            {modelData.length === 0 ? <ErrState msg="No model data yet." /> : (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={modelData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                    {modelData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// ─── Root App ──────────────────────────────────────────────────────────────

function App() {
  const [runs, setRuns] = useState<Run[]>([])
  const [runsLoading, setRunsLoading] = useState(true)
  const [ollamaOk, setOllamaOk] = useState<boolean | null>(null)

  const refresh = useCallback(() => {
    setRunsLoading(true)
    Promise.all([
      fetch(`${API}/runs`).then(r => r.json()),
      fetch(`${API}/health`).then(r => r.json()),
    ]).then(([r, h]) => {
      setRuns(r)
      setOllamaOk(h.ollama)
    }).catch(console.error).finally(() => setRunsLoading(false))
  }, [])

  useEffect(() => { refresh() }, [refresh])

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border/40 glass px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🪐</span>
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-gradient">ORBIT</h1>
            <p className="text-xs text-muted-foreground -mt-0.5">Agent Observability Platform</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs">
            <span className={`relative flex h-2 w-2`}>
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${ollamaOk ? "bg-emerald-400" : "bg-rose-400"}`} />
              <span className={`relative inline-flex rounded-full h-2 w-2 ${ollamaOk ? "bg-emerald-500" : "bg-rose-500"}`} />
            </span>
            <span className="text-muted-foreground">Ollama {ollamaOk === null ? "…" : ollamaOk ? "connected" : "offline"}</span>
          </div>
          <button onClick={refresh} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
          <Badge variant="outline" className="text-xs mono">{runs.length} runs</Badge>
        </div>
      </header>

      {/* Main */}
      <main className="px-6 py-6 max-w-7xl mx-auto">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-8 h-auto p-1 bg-muted/30 rounded-xl glass">
            {[
              { value: "overview", label: "Overview", icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
              { value: "runs", label: "Runs", icon: <History className="w-3.5 h-3.5" /> },
              { value: "failures", label: "Failures", icon: <AlertTriangle className="w-3.5 h-3.5" /> },
              { value: "arena", label: "Arena", icon: <Crosshair className="w-3.5 h-3.5" /> },
              { value: "replay", label: "Replay", icon: <Activity className="w-3.5 h-3.5" /> },
              { value: "models", label: "Models", icon: <Cpu className="w-3.5 h-3.5" /> },
              { value: "analytics", label: "Analytics", icon: <BarChart3 className="w-3.5 h-3.5" /> },
              { value: "security", label: "Security", icon: <ShieldAlert className="w-3.5 h-3.5" /> },
            ].map(t => (
              <TabsTrigger key={t.value} value={t.value}
                className="rounded-lg py-2 px-2 text-xs flex items-center gap-1 data-[state=active]:bg-background data-[state=active]:shadow-sm data-[state=active]:text-foreground">
                {t.icon} <span className="hidden sm:inline">{t.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="overview"><OverviewTab runs={runs} /></TabsContent>
          <TabsContent value="runs"><RunsTab runs={runs} loading={runsLoading} /></TabsContent>
          <TabsContent value="failures"><FailuresTab /></TabsContent>
          <TabsContent value="arena"><ArenaTab /></TabsContent>
          <TabsContent value="replay"><ReplayTab runs={runs} /></TabsContent>
          <TabsContent value="models"><ModelsTab /></TabsContent>
          <TabsContent value="analytics"><AnalyticsTab runs={runs} /></TabsContent>
          <TabsContent value="security"><SecurityTab /></TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App
