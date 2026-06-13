"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Search, Loader2, Database } from "lucide-react";
import { api } from "@/lib/api";



export default function NewAgentPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [searchQ, setSearchQ] = useState("");
  const [results, setResults] = useState<{ code: string; name: string }[]>([]);
  const [selected, setSelected] = useState<{ code: string; name: string } | null>(null);
  const [capital, setCapital] = useState("100000");
  const [strategy, setStrategy] = useState("ai");
  const [submitting, setSubmitting] = useState(false);
  const [searching, setSearching] = useState(false);
  const [stocksLoading, setStocksLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const preload = async () => {
      try { await api.preloadStocks(); }
      catch (e) { console.error(e); }
      setStocksLoading(false);
    };
    preload();
  }, []);

  const handleSearch = async (q: string) => {
    setSearchQ(q);
    if (q.length < 1) { setResults([]); return; }
    setSearching(true);
    try {
      const r = await api.searchStocks(q);
      setResults(r.results || []);
    } catch (e) { console.error(e); setErrorMsg("Search failed: " + (e.message || e)); }
    finally { setSearching(false); }
  };

  const handleSubmit = async () => {
    if (!name || !selected) return;
    setSubmitting(true);
    try {
      const agent = await api.createAgent({
        name, stock_code: selected.code, stock_name: selected.name,
        total_capital: parseFloat(capital), strategy, mode: "live",
      });
      router.push(`/agents/${agent.id}`);
    } catch (e) {
      console.error(e);
      setErrorMsg("Create failed: " + (e.message || e));
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 560, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <button onClick={() => router.back()} className="btn-ghost" style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 0", fontSize: 13 }}>
          <ArrowLeft size={14} /> 返回
        </button>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: "8px 0 4px" }}>新建交易员</h2>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>创建一个AI或规则驱动的模拟交易员</p>
      </div>

      <div className="card" style={{ padding: 24, position: "relative" }}>
        {stocksLoading && <div style={{position:"absolute",inset:0,background:"var(--bg-secondary)",borderRadius:12,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",zIndex:10,opacity:0.95}}><Loader2 size={28} className="animate-spin" style={{color:"var(--primary)",marginBottom:12}} /><div style={{fontSize:13,color:"var(--text-secondary)"}}>\u6b63\u5728\u52a0\u8f7d\u80a1\u7968\u6570\u636e...</div></div>}
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", fontSize: 12, color: "var(--text-secondary)", marginBottom: 6, fontWeight: 600 }}>交易员名称</label>
          <input type="text" value={name} onChange={e => setName(e.target.value)}
            placeholder="例: 猎豹一号" style={{ width: "100%" }} />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", fontSize: 12, color: "var(--text-secondary)", marginBottom: 6, fontWeight: 600 }}>股票</label>
          <div style={{ position: "relative" }}>
            <input type="text" value={searchQ} onChange={e => handleSearch(e.target.value)}
              placeholder="搜索 A股代码或名称 (如 000001, 贵州茅台)"
              style={{ width: "100%", paddingRight: 36 }} />
            <Search size={14} style={{ position: "absolute", right: 12, top: 12, color: "var(--text-secondary)" }} />
          </div>
          {searching && <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 6 }}>搜索中...</div>}
          {results.length > 0 && (
            <div style={{ marginTop: 6, maxHeight: 200, overflow: "auto", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: 8 }}>
              {results.map(r => (
                <div key={r.code} onClick={() => { setSelected(r); setSearchQ(`${r.code} ${r.name}`); setResults([]); }}
                  style={{
                    padding: "8px 12px", cursor: "pointer", fontSize: 13,
                    borderBottom: "1px solid var(--border)", transition: "background 0.15s",
                    background: selected?.code === r.code ? "var(--highlight)" : "transparent",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = "var(--highlight)"}
                  onMouseLeave={e => e.currentTarget.style.background = selected?.code === r.code ? "var(--highlight)" : "transparent"}>
                  <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{r.name}</span>
                  <span style={{ color: "var(--text-secondary)", marginLeft: 8 }}>{r.code}</span>
                </div>
              ))}
            </div>
          )}
          {selected && !searching && (
            <div style={{ marginTop: 8, display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 10px", background: "var(--primary-10)", borderRadius: 6, fontSize: 12, color: "#D4835A" }}>
              已选: {selected.name} ({selected.code})
              <button onClick={() => { setSelected(null); setSearchQ(""); }}
                style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer", fontSize: 12, padding: 0 }}>✕</button>
            </div>
          )}
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", fontSize: 12, color: "var(--text-secondary)", marginBottom: 6, fontWeight: 600 }}>初始资金</label>
          <input type="number" value={capital} onChange={e => setCapital(e.target.value)}
            placeholder="100000" style={{ width: "100%" }} />
        </div>

        <div style={{ marginBottom: 24 }}>
          <label style={{ display: "block", fontSize: 12, color: "var(--text-secondary)", marginBottom: 6, fontWeight: 600 }}>策略类型</label>
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={() => setStrategy("ai")}
              style={{
                flex: 1, padding: "10px 16px", borderRadius: 8, fontSize: 13,
                border: strategy === "ai" ? "1px solid #D4835A" : "1px solid var(--border)",
                background: strategy === "ai" ? "var(--primary-10)" : "var(--bg-secondary)",
                color: strategy === "ai" ? "#D4835A" : "#8B8278",
              }}>
              <div style={{ fontWeight: 600 }}>AI 智能策略</div>
              <div style={{ fontSize: 11, marginTop: 2 }}>LLM 分析技术指标决策</div>
            </button>
            <button onClick={() => setStrategy("rule")}
              style={{
                flex: 1, padding: "10px 16px", borderRadius: 8, fontSize: 13,
                border: strategy === "rule" ? "1px solid #D4835A" : "1px solid var(--border)",
                background: strategy === "rule" ? "var(--primary-10)" : "var(--bg-secondary)",
                color: strategy === "rule" ? "#D4835A" : "#8B8278",
              }}>
              <div style={{ fontWeight: 600 }}>规则策略</div>
              <div style={{ fontSize: 11, marginTop: 2 }}>技术指标规则自动执行</div>
            </button>
          </div>
        </div>

        {errorMsg && <div style={{padding:"8px 12px",marginBottom:12,background:"var(--danger-10)",border:"1px solid #C46A5A",borderRadius:8,fontSize:12,color:"#C46A5A"}}>{errorMsg}</div>}
        <button onClick={handleSubmit} disabled={!name || !selected || submitting} className="btn-primary"
          style={{ width: "100%", padding: "10px 0", fontSize: 14 }}>
          {submitting ? <><Loader2 size={14} style={{ marginRight: 6, animation: "spin 1s linear infinite" }} /> 创建中...</> : "创建交易员"}
        </button>
      </div>
    </div>
  );
}
