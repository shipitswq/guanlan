"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Bot, Plus, Play, RotateCcw, Trophy, Pause } from "lucide-react";
import { api, AgentData } from "@/lib/api";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState<number | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      const r = await api.getAgents();
      setAgents(r || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  const sorted = [...agents].sort((a, b) => b.return_rate - a.return_rate);
  const maxRate = Math.max(...sorted.map(a => Math.abs(a.return_rate)), 1);

  const handleExecute = async (id: number) => {
    setExecuting(id);
    try {
      await api.executeTrade(id);
      fetchAgents();
    } catch (e) { console.error(e); }
    finally { setExecuting(null); }
  };

  const handleReset = async (id: number) => {
    try { await api.resetAgent(id); fetchAgents(); } catch (e) { console.error(e); }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>交易员</h2>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>AI智能交易员 · 模拟盘比赛</p>
        </div>
        <Link href="/agents/new" className="btn-primary">
          <Plus size={14} style={{ marginRight: 6 }} />新建交易员
        </Link>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>加载中...</div>
      ) : agents.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)", background: "var(--bg-secondary)", borderRadius: 12, border: "1px solid var(--border)" }}>
          <Bot size={48} style={{ margin: "0 auto 16px", display: "block", opacity: 0.3 }} />
          <p style={{ margin: "0 0 4px", fontSize: 15 }}>还没有交易员</p>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "0 0 16px" }}>创建一个AI交易员，开始模拟交易比赛</p>
          <Link href="/agents/new" style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "8px 20px", background: "#D4835A", color: "white", borderRadius: 8, textDecoration: "none", fontSize: 13 }}>
            <Plus size={14} /> 创建第一个
          </Link>
        </div>
      ) : (
        <div className="card" style={{ overflow: "hidden" }}>
          <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <Trophy size={16} color="#C9A84C" />
            <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>交易员大赛</span>
            <span style={{ fontSize: 12, color: "var(--text-secondary)", marginLeft: "auto" }}>{agents.length} 位参赛</span>
          </div>

          {/* Header */}
          <div style={{
            display: "grid", gridTemplateColumns: "36px 1fr 90px 100px 100px 80px",
            padding: "8px 20px", borderBottom: "1px solid var(--border)",
            fontSize: 11, color: "var(--text-secondary)", fontWeight: 600,
          }}>
            <span>#</span><span>交易员</span><span>收益率</span><span>累计盈亏</span><span>赛马</span><span>操作</span>
          </div>

          {sorted.map((agent, i) => (
            <div key={agent.id} style={{ textDecoration: "none" }}>
              <div style={{
                display: "grid", gridTemplateColumns: "36px 1fr 90px 100px 100px 80px",
                padding: "10px 20px", alignItems: "center",
                borderBottom: i < agents.length - 1 ? "1px solid var(--border)" : "none",
                transition: "background 0.15s",
              }}
              onMouseEnter={e => e.currentTarget.style.background = "var(--highlight)"}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                <span style={{ fontSize: 14 }}>{i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `#${i + 1}`}</span>

                <Link href={`/agents/${agent.id}`} style={{ textDecoration: "none" }}>
                  <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: 13 }}>{agent.name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>{agent.stock_code} · {agent.strategy === "ai" ? "AI" : "规则"}</div>
                </Link>

                <span style={{ fontWeight: 700, fontSize: 14, color: agent.return_rate >= 0 ? "#6B8F6B" : "#C46A5A" }}>
                  {agent.return_rate >= 0 ? "+" : ""}{agent.return_rate.toFixed(1)}%
                </span>

                <div>
                  <span style={{ fontWeight: 600, fontSize: 13, color: agent.pnl >= 0 ? "#6B8F6B" : "#C46A5A" }}>
                    {agent.pnl >= 0 ? "+" : ""}{agent.pnl.toFixed(0)}
                  </span>
                  <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>{agent.available_cash.toFixed(0)} 现金</div>
                </div>

                <div style={{ height: 20, display: "flex", alignItems: "center" }}>
                  <div style={{
                    width: `${Math.max(Math.abs(agent.return_rate) / maxRate * 100, 8)}%`,
                    height: 14, borderRadius: 7,
                    background: agent.return_rate >= 0
                      ? "linear-gradient(90deg, #6B8F6B, #5A7D5A)"
                      : "linear-gradient(90deg, #C46A5A, #A85A4A)",
                    transition: "width 0.5s ease", minWidth: 14,
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    {Math.abs(agent.return_rate) > 3 && <span style={{ fontSize: 8 }}>{agent.return_rate >= 0 ? "🐎" : "🐢"}</span>}
                  </div>
                </div>

                <div style={{ display: "flex", gap: 4 }}>
                  <button onClick={() => handleExecute(agent.id)} disabled={executing === agent.id}
                    title="执行交易" style={{
                      padding: "4px 8px", background: "var(--primary-10)", border: "none",
                      borderRadius: 4, cursor: "pointer", color: "#D4835A", fontSize: 11,
                    }}>
                    <Play size={12} />
                  </button>
                  <button onClick={() => handleReset(agent.id)}
                    title="重置" style={{
                      padding: "4px 8px", background: "var(--danger-10)", border: "none",
                      borderRadius: 4, cursor: "pointer", color: "#C46A5A", fontSize: 11,
                    }}>
                    <RotateCcw size={12} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
