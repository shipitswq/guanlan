"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Search, Plus, TrendingUp, TrendingDown } from "lucide-react";
import { api, KlineItem } from "@/lib/api";

export default function StockDetailPage() {
  const { code } = useParams();
  const router = useRouter();
  const [kline, setKline] = useState<KlineItem[]>([]);
  const [info, setInfo] = useState<{ code: string; name: string } | null>(null);
  const [realtime, setRealtime] = useState<any>(null);
  const [tech, setTech] = useState<any>(null);

  useEffect(() => {
    if (!code) return;
    Promise.all([
      api.getStockInfo(code as string).catch(() => null),
      api.getKline(code as string, 120, "daily").catch(() => ({ kline: [] })),
      api.getRealtime(code as string).catch(() => null),
      api.getTechIndicators(code as string).catch(() => null),
    ]).then(([i, k, r, t]) => {
      if (i) setInfo(i);
      if (k) setKline(k.kline);
      if (r) setRealtime(r);
      if (t) setTech(t.indicators);
    });
  }, [code]);

  if (!code) return null;
  const maxPrice = kline.length > 0 ? Math.max(...kline.map(d => d.high)) : 0;
  const minPrice = kline.length > 0 ? Math.min(...kline.map(d => d.low)) : 0;
  const range = maxPrice - minPrice || 1;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={() => router.back()} className="btn-ghost" style={{ padding: "6px 0" }}>
            <ArrowLeft size={16} />
          </button>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              {info?.name || code} ({code})
            </h2>
            {realtime && (
              <p style={{ fontSize: 13, margin: "2px 0 0", color: realtime.change_pct >= 0 ? "#6B8F6B" : "#C46A5A" }}>
                最新价: {realtime.price.toFixed(2)} · {realtime.change_pct >= 0 ? "+" : ""}{realtime.change_pct.toFixed(2)}%
              </p>
            )}
          </div>
        </div>
        <Link href={`/agents/new?stock=${code}`} className="btn-primary" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Plus size={14} /> 创建交易员
        </Link>
      </div>

      <div className="card" style={{ height: 400, marginBottom: 24, position: "relative" }}>
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
          K线图 ({kline.length} 天)
        </div>
        <div style={{ height: "calc(100% - 44px)", padding: 8 }}>
          {kline.length > 0 ? (
            <svg width="100%" height="100%" viewBox={`0 0 ${kline.length * 4} 300`} preserveAspectRatio="none">
              <polyline
                points={kline.map((d, i) => `${i * 4 + 2},${200 - (d.close - minPrice) / range * 180}`).join(" ")}
                fill="none" stroke="#D4835A" strokeWidth="1" opacity={0.8}
              />
            </svg>
          ) : <div style={{ textAlign: "center", paddingTop: 100, color: "var(--text-secondary)" }}>加载中...</div>}
        </div>
      </div>

      {tech && (
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", margin: "0 0 16px" }}>技术指标</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
            <TechBadge label="RSI" value={String(tech.rsi ?? "-")} color={tech.rsi > 70 ? "#C46A5A" : tech.rsi < 30 ? "#6B8F6B" : "var(--text-primary)"} />
            <TechBadge label="MA5" value={String(tech.ma5 ?? "-")} color="var(--text-primary)" />
            <TechBadge label="MA20" value={String(tech.ma20 ?? "-")} color="var(--text-primary)" />
            <TechBadge label="MACD" value={tech.macd?.histogram?.toFixed(4) ?? "-"} color={tech.macd?.histogram >= 0 ? "#6B8F6B" : "#C46A5A"} />
            <TechBadge label="KDJ-K" value={tech.kdj?.k?.toFixed(1) ?? "-"} color="#D4835A" />
            <TechBadge label="KDJ-D" value={tech.kdj?.d?.toFixed(1) ?? "-"} color="#D4835A" />
            <TechBadge label="KDJ-J" value={tech.kdj?.j?.toFixed(1) ?? "-"} color="#D4835A" />
            <TechBadge label="布林位置" value={tech.bollinger?.position === "above_upper" ? "上轨上" : tech.bollinger?.position === "below_lower" ? "下轨下" : "中轨区"} color="var(--text-primary)" />
          </div>
        </div>
      )}
    </div>
  );
}

function TechBadge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ padding: "10px 12px", background: "var(--bg-primary)", borderRadius: 8, border: "1px solid var(--border)" }}>
      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}