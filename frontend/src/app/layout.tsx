"use client";
import "./globals.css";
import Link from "next/link";
import { BarChart3, Bot, Search, TrendingUp } from "lucide-react";


export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body style={{ display: "flex", minHeight: "100vh" }}>
        {/* Sidebar */}
        <nav style={{
          width: 220, background: "var(--bg-secondary)", borderRight: "1px solid var(--border)",
          padding: "20px 0", display: "flex", flexDirection: "column", flexShrink: 0,
        }}>
          <div style={{ padding: "0 20px", marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <BarChart3 size={22} color="#D4835A" />
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text-primary)" }}>模拟盘</div>
                <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>A股智能交易员</div>
              </div>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 2, padding: "0 8px" }}>
            <NavItem href="/" icon={<TrendingUp size={16} />} label="总览面板" />
            <NavItem href="/agents" icon={<Bot size={16} />} label="交易员" />
            <NavItem href="/agents/new" icon={<Search size={16} />} label="创建交易员" />
          </div>
        </nav>

        {/* Main */}
        <main style={{ flex: 1, padding: 28, overflow: "auto", minHeight: "100vh" }}>
          {children}
        </main>
      </body>
    </html>
  );
}

function NavItem({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link href={href} style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "10px 12px", borderRadius: 8, fontSize: 13, fontWeight: 500,
      color: "var(--text-secondary)", textDecoration: "none", transition: "all 0.15s",
    }}
    onMouseEnter={e => { e.currentTarget.style.background = "var(--highlight)"; e.currentTarget.style.color = "var(--text-primary)"; }}
    onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#8B8278"; }}>
      {icon}
      <span>{label}</span>
    </Link>
  );
}
