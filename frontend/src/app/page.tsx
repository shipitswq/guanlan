"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Bot, TrendingUp, TrendingDown, Plus, Trophy, DollarSign, Activity } from "lucide-react";
import { api, AgentData } from "@/lib/api";

export default function Dashboard() {
  const [agents, setAgents] = useState<AgentData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAgents()
      .then(r => setAgents(r || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const sorted = [...agents].sort((a, b) => b.return_rate - a.return_rate);
  const activeAgents = agents.filter(a => a.status === "active").length;
  const totalPnl = agents.reduce((s, a) => s + a.pnl, 0);
  const totalCapital = agents.reduce((s, a) => s + a.total_capital, 0);
  const bestReturn = agents.length > 0 ? Math.max(...agents.map(a => a.return_rate)) : 0;
  const maxBar = Math.max(...agents.map(a => Math.abs(a.return_rate)), 1);

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>总览面板</h2>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>模拟盘全局概览</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14, marginBottom: 28 }}>
        <StatCard icon={<Bot size={18} color="#D4835A" />} label="交易员" value={String(agents.length)} sub={`运行中 ${activeAgents}`} />
        <StatCard icon={<DollarSign size={18} color="#6B8F6B" />} label="总盈亏" value={totalPnl >= 0 ? `+${totalPnl.toFixed(0)}` : totalPnl.toFixed(0)} sub={`总资金 ${totalCapital.toFixed(0)}`} isPositive={totalPnl >= 0} />
        <StatCard icon={<TrendingUp size={18} color="#6B8F6B" />} label="最高收益率" value={bestReturn >= 0 ? `+${bestReturn.toFixed(2)}%` : `${bestReturn.toFixed(2)}%`} isPositive={bestReturn >= 0} />
        <StatCard icon={<Activity size={18} color="#C9A84C" />} label="运行中" value={String(activeAgents)} sub={`总计 ${agents.length}`} />
      </div>

      <div className="card" style={{ overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Trophy size={16} color="#C9A84C" />
            <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>交易员排行榜</span>
          </div>
          <Link href="/agents/new" style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "6px 14px", background: "#D4835A", color: "white",
            borderRadius: 6, textDecoration: "none", fontSize: 12, fontWeight: 600,
          }}>
            <Plus size={12} /> 新建
          </Link>
        </div>
        {loading ? (
          <div style={{ padding: 48, textAlign: "center", color: "var(--text-secondary)" }}>加载中...</div>
        ) : agents.length === 0 ? (
          <div style={{ padding: 48, textAlign: "center", color: "var(--text-secondary)" }}>
            <Bot size={36} style={{ opacity: 0.3, margin: "0 auto 12px", display: "block" }} />
            <p style={{ margin: "0 0 4px" }}>还没有交易员</p>
            <p style={{ fontSize: 13, margin: "0 0 16px" }}>创建第一个AI交易员开始模拟交易</p>
            <Link href="/agents/new" style={{ display: "inline-block", padding: "8px 20px", background: "#D4835A", color: "white", borderRadius: 8, textDecoration: "none", fontSize: 13 }}>创建第一个</Link>
          </div>
        ) : (
          sorted.map((agent, i) => (
            <Link key={agent.id} href={"/agents/" + agent.id} style={{ textDecoration: "none" }}>
              <div style={{
                display: "flex", alignItems: "center", padding: "10px 20px",
                borderBottom: i < agents.length - 1 ? "1px solid var(--border)" : "none",
                cursor: "pointer", transition: "background 0.15s",
              }}
              onMouseEnter={e => e.currentTarget.style.background = "var(--highlight)"}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                <span style={{ minWidth: 32, fontSize: 16 }}>{i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `#${i + 1}`}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: 14 }}>{agent.name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>{agent.stock_code} · {agent.stock_name} · {agent.strategy === "ai" ? "AI策略" : "规则策略"}</div>
                </div>
                <div style={{ width: 100, height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden", marginRight: 14 }}>
                  <div style={{
                    width: `${Math.max(Math.abs(agent.return_rate) / maxBar * 100, 5)}%`,
                    height: "100%", borderRadius: 3,
                    background: agent.return_rate >= 0 ? "#6B8F6B" : "#C46A5A",
                    minWidth: 10, transition: "width 0.5s ease"
                  }} />
                </div>
                <span style={{ fontWeight: 700, fontSize: 14, minWidth: 80, textAlign: "right", color: agent.return_rate >= 0 ? "#6B8F6B" : "#C46A5A" }}>
                  {agent.return_rate >= 0 ? "+" : ""}{agent.return_rate.toFixed(2)}%
                </span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, sub, isPositive }: { icon: React.ReactNode; label: string; value: string; sub?: string; isPositive?: boolean }) {
  return (
    <div className="card" style={{ padding: 18 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        {icon}
        <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{label}</span>
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: isPositive !== undefined ? (isPositive ? "#6B8F6B" : "#C46A5A") : "var(--text-primary)" }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}
