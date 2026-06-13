"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Play, RotateCcw, Trash2, Timer, BarChart3, Brain, FileText,
} from "lucide-react";
import { api } from "@/lib/api";

export default function AgentDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [agent, setAgent] = useState(null);
  const [kline, setKline] = useState([]);
  const [backtestResult, setBacktestResult] = useState(null);
  const [granularity, setGranularity] = useState("daily");
  const [executing, setExecuting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("trades");
  const [realtime, setRealtime] = useState(null);
  const [btStart, setBtStart] = useState("2025-06-01");
  const [btEnd, setBtEnd] = useState("2025-12-31");

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      setLoading(true);
      try {
        const a = await api.getAgent(Number(id));
        setAgent(a);
        const [k, r] = await Promise.all([
          api.getKline(a.stock_code, 120, granularity).catch(() => ({ kline: [] })),
          api.getRealtime(a.stock_code).catch(() => null),
        ]);
        setKline(k?.kline || []);
        setRealtime(r);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    load();
  }, [id, granularity]);

  const handleExecute = async () => {
    if (!agent || executing) return;
    setExecuting(true);
    try {
      await api.executeTrade(agent.id, granularity);
      setAgent(await api.getAgent(agent.id));
    } catch (e) { console.error(e); }
    finally { setExecuting(false); }
  };

  const handleReset = async () => {
    if (!agent) return;
    try {
      await api.resetAgent(agent.id);
      setAgent(await api.getAgent(agent.id));
      setBacktestResult(null);
    } catch (e) { console.error(e); }
  };

  const handleDelete = async () => {
    if (!agent || !confirm("确认删除？")) return;
    try { await api.deleteAgent(agent.id); router.push("/agents"); }
    catch (e) { console.error(e); }
  };

  const handleBacktest = async () => {
    if (!agent) return;
    try {
      const result = await api.runBacktest(agent.id, btStart, btEnd);
      setBacktestResult(result);
      const updated = await api.getAgent(agent.id);
      setAgent(updated);
      setActiveTab("backtest");
    } catch (e) { console.error(e); }
  };

  if (loading || !agent) {
    return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>加载中...</div>;
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={() => router.push("/agents")} className="btn-ghost"><ArrowLeft size={16} /></button>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>{agent.name}</h2>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "2px 0 0" }}>{agent.stock_code} - {agent.strategy}</p>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={handleExecute} disabled={executing} className="btn-primary"><Play size={14} /> ִ��</button>
          <button onClick={handleBacktest} style={{ padding: "8px 14px", background: "var(--bg-secondary)", color: "var(--text-primary)", borderRadius: 8, fontSize: 13, border: "1px solid var(--border)" }}><Timer size={14} /> �ز�</button>
          <button onClick={handleReset} style={{ padding: "8px 14px", background: "var(--danger-10)", color: "#C46A5A", borderRadius: 8 }}><RotateCcw size={14} /></button>
          <button onClick={handleDelete} style={{ padding: "8px 14px", background: "transparent", color: "#C46A5A", borderRadius: 8, border: "1px solid var(--border)" }}><Trash2 size={14} /></button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>周期：</span>
        {["daily", "60分"].map(g => (
          <button key={g} onClick={() => setGranularity(g)} style={{ padding: "6px 14px", borderRadius: 6, fontSize: 12, fontWeight: 600, border: granularity === g ? "1px solid #D4835A" : "1px solid var(--border)", background: granularity === g ? "var(--primary-10)" : "transparent", color: granularity === g ? "#D4835A" : "var(--text-secondary)" }}>{g === "daily" ? "日线" : "60分"}</button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginBottom: 20 }}>
        <MiniCard label="�۸�" value={realtime ? realtime.price.toFixed(2) : "-"} color="var(--text-primary)" />
        <MiniCard label="�ֲ�" value={agent.position + " ��"} color="var(--text-primary)" sub={"�ɱ���" + agent.avg_cost.toFixed(2)} />
        <MiniCard label="�ֽ�" value={agent.available_cash.toFixed(2)} color="var(--text-primary)" />
        <MiniCard label="ӯ��" value={agent.pnl.toFixed(2)} color={agent.pnl >= 0 ? "var(--success)" : "var(--danger)"} sub={agent.return_rate.toFixed(2) + "%"} />
      </div>

      <div className="card" style={{ marginBottom: 20, height: 300, overflow: "hidden" }}>
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>图表 - {agent.stock_code} {agent.stock_name}</div>
        <div style={{ height: "calc(100% - 44px)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-secondary)" }}>
          {kline.length > 0 ? <SimpleKLine data={kline} trades={agent.trades || []} /> : "����ͼ����..."}
        </div>
      </div>

      <div style={{ display: "flex", gap: 4, marginBottom: 16, borderBottom: "1px solid var(--border)" }}>
        {["trades","logs","backtest"].map(k => (
          <button key={k} onClick={() => setActiveTab(k)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 16px", fontSize: 13, fontWeight: 600, color: activeTab === k ? "#D4835A" : "var(--text-secondary)", background: "transparent", border: "none", borderBottom: activeTab === k ? "2px solid #D4835A" : "2px solid transparent", marginBottom: -1 }}>
            {k === "trades" ? <FileText size={14}/> : k === "logs" ? <Brain size={14}/> : <BarChart3 size={14}/>} {k === "trades" ? "交易" : k === "logs" ? "日志" : "回测"}
          </button>
        ))}
      </div>

      <div className="card" style={{ minHeight: 280 }}>
        {activeTab === "trades" && (!agent.trades || agent.trades.length === 0 ? <div style={{ padding: 48, textAlign: "center", color: "var(--text-secondary)" }}>No trades</div> :
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead><tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 11, textAlign: "left" }}>
              <th style={{ padding: "10px 16px" }}>时间</th><th style={{ padding: "10px 16px" }}>类型</th><th style={{ padding: "10px 16px" }}>价格</th><th style={{ padding: "10px 16px" }}>数量</th></tr></thead>
            <tbody>{agent.trades.map(t => (
              <tr key={t.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "10px 16px", color: "var(--text-secondary)", fontSize: 12 }}>{(t.created_at||"").substring(0,19).replace("T"," ")}</td>
                <td style={{ padding: "10px 16px" }}><span style={{color:t.trade_type==="buy"?"var(--success)":"var(--danger)",fontWeight:600}}>{t.trade_type}</span></td>
                <td style={{ padding: "10px 16px", color: "var(--text-primary)" }}>{t.price.toFixed(2)}</td>
                <td style={{ padding: "10px 16px", color: "var(--text-primary)" }}>{t.quantity}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
        {activeTab === "logs" && <LogsPanel agentId={agent.id} />}
        {activeTab === "backtest" && (!backtestResult ?
          <div style={{ padding: 20 }}>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>Select date range for backtest:</p>
            <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
              <div><label style={{ fontSize: 11, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>开始</label><input type="date" value={btStart} onChange={e => setBtStart(e.target.value)} style={{ padding: "6px 10px", borderRadius: 6, fontSize: 13, background: "var(--bg-primary)", border: "1px solid var(--border)", color: "var(--text-primary)" }} /></div>
              <div><label style={{ fontSize: 11, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>结束</label><input type="date" value={btEnd} onChange={e => setBtEnd(e.target.value)} style={{ padding: "6px 10px", borderRadius: 6, fontSize: 13, background: "var(--bg-primary)", border: "1px solid var(--border)", color: "var(--text-primary)" }} /></div>
              <button onClick={handleBacktest} style={{ marginTop: 18, padding: "6px 16px", background: "#D4835A", color: "white", borderRadius: 6, fontSize: 13, fontWeight: 600 }}>运行回测</button>
            </div>
          </div> :
          <div style={{ padding: 20 }}>
            {backtestResult.summary?.initial_capital ? (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 12 }}>
                  {[["��ʼ�ʽ�", backtestResult.summary.initial_capital.toFixed(0)],["���ռ�ֵ",backtestResult.summary.final_value.toFixed(0)],["ӯ��",(backtestResult.summary.total_pnl>=0?"+":"")+backtestResult.summary.total_pnl.toFixed(2)],["������",(backtestResult.summary.total_return_pct>=0?"+":"")+backtestResult.summary.total_return_pct.toFixed(2)+"%"]].map(([l,v]) => (
                    <div key={l} className="card" style={{ padding: 12 }}><div style={{fontSize:11,color:"var(--text-secondary)",marginBottom:4}}>{l}</div><div style={{fontSize:16,fontWeight:700,color:"var(--text-primary)"}}>{v}</div></div>
                  ))}
                  <button onClick={() => setBacktestResult(null)} style={{ gridColumn: "1 / -1", padding: "6px 14px", background: "var(--bg-secondary)", color: "var(--text-primary)", borderRadius: 6, fontSize: 12, border: "1px solid var(--border)" }}>更改日期范围</button>
                </div>
                <div style={{ display: "flex", gap: 20, padding: "8px 0", fontSize: 12, color: "var(--text-secondary)" }}>
                  <span>周期： {btStart} ~ {btEnd}</span>
                  <span>买入持有收益：{backtestResult.summary?.buy_hold_return_pct?.toFixed(2) || "-"}%</span>
                </div>
                <BacktestTradeTable trades={backtestResult.trades} />
              </div>
            ) : (
              <div style={{ padding: 40, textAlign: "center", color: "#C46A5A", fontSize: 14 }}>{backtestResult.message || "��������"}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MiniCard({ label, value, color, sub }) {
  return (
    <div className="card" style={{ padding: "14px 16px" }}>
      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function SimpleKLine({ data, trades }) {
  const maxP = Math.max(...data.map(d => d.high));
  const minP = Math.min(...data.map(d => d.low));
  const range = maxP - minP || 1;
  return (
    <div style={{ width: "100%", height: "100%", padding: "8px 0", position: "relative" }}>
      <svg width="100%" height="100%" viewBox={"0 0 " + (data.length * 4) + " 250"} preserveAspectRatio="none">
        <polyline points={data.map((d, i) => (i * 4 + 2) + "," + (170 - (d.close - minP) / range * 150)).join(" ")} fill="none" stroke="#D4835A" strokeWidth="1" opacity={0.8} />
        {trades.filter(t => t.trade_type === "buy").map((t, i) => {
          const idx = data.findIndex(d => d.date && t.created_at && d.date.startsWith(t.created_at.substring(0, 10)));
          return idx >= 0 ? <circle key={"b" + i} cx={idx * 4 + 2} cy={170 - (t.price - minP) / range * 150} r="4" fill="var(--success)" stroke="var(--bg-secondary)" strokeWidth="1.5" /> : null;
        })}
        {trades.filter(t => t.trade_type === "sell").map((t, i) => {
          const idx = data.findIndex(d => d.date && t.created_at && d.date.startsWith(t.created_at.substring(0, 10)));
          return idx >= 0 ? <circle key={"s" + i} cx={idx * 4 + 2} cy={170 - (t.price - minP) / range * 150} r="4" fill="var(--danger)" stroke="var(--bg-secondary)" strokeWidth="1.5" /> : null;
        })}
      </svg>
    </div>
  );
}

function LogsPanel({ agentId }) {
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);
  useEffect(() => { api.getAgentLogs(agentId).then(r => { setLogs(r || []); setLogsLoading(false); }).catch(() => setLogsLoading(false)); }, [agentId]);
  if (logsLoading) return <div style={{ padding: 48, textAlign: "center", color: "var(--text-secondary)" }}>加载中...</div>;
  if (logs.length === 0) return <div style={{ padding: 48, textAlign: "center", color: "var(--text-secondary)" }}>No logs yet</div>;
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead><tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 11, textAlign: "left" }}>
          <th style={{ padding: "10px 16px" }}>时间</th><th style={{ padding: "10px 16px" }}>决策</th><th style={{ padding: "10px 16px" }}>价格</th><th style={{ padding: "10px 16px" }}>周期</th>
        </tr></thead>
        <tbody>{logs.map(l => (
          <tr key={l.id} style={{ borderBottom: "1px solid var(--border)" }}>
            <td style={{ padding: "10px 16px", color: "var(--text-secondary)", fontSize: 12 }}>{(l.created_at || "").substring(0, 19).replace("T", " ")}</td>
            <td style={{ padding: "10px 16px" }}><span style={{ color: l.decision === "buy" ? "var(--success)" : l.decision === "sell" ? "var(--danger)" : "#D4835A", fontWeight: 600 }}>{l.decision}</span></td>
            <td style={{ padding: "10px 16px", color: "var(--text-primary)" }}>{(l.price || 0).toFixed(2)}</td>
            <td style={{ padding: "10px 16px", color: "var(--text-secondary)" }}>{l.kline_granularity === "daily" ? "日线" : "60分"}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function BacktestTradeTable({ trades }) {
  if (!trades || trades.length === 0) return null;
  return (
    <div style={{ overflowX: "auto" }}>
      <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>回测交易记录 ({trades.length})</div>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-secondary)", fontSize: 11, textAlign: "left" }}>
            <th style={{ padding: "8px 14px" }}>日期</th><th style={{ padding: "8px 14px" }}>类型</th><th style={{ padding: "8px 14px" }}>价格</th><th style={{ padding: "8px 14px" }}>数量</th><th style={{ padding: "8px 14px" }}>金额</th><th style={{ padding: "8px 14px" }}>原因</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, idx) => (
            <tr key={idx} style={{ borderBottom: "1px solid var(--border)" }}>
              <td style={{ padding: "8px 14px", color: "var(--text-secondary)" }}>{t.date || ""}</td>
              <td style={{ padding: "8px 14px" }}><span style={{ color: t.trade_type === "buy" ? "var(--success)" : "var(--danger)", fontWeight: 600 }}>{t.trade_type}</span></td>
              <td style={{ padding: "8px 14px", color: "var(--text-primary)" }}>{t.price?.toFixed(2)}</td>
              <td style={{ padding: "8px 14px", color: "var(--text-primary)" }}>{t.quantity}</td>
              <td style={{ padding: "8px 14px", color: "var(--text-primary)" }}>{t.amount?.toFixed(2)}</td>
              <td style={{ padding: "8px 14px", color: "var(--text-secondary)", fontSize: 11 }}>{t.reason || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
