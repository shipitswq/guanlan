const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export interface AgentData {
  id: number; name: string; stock_code: string; stock_name: string;
  total_capital: number; available_cash: number; position: number;
  avg_cost: number; strategy: string; mode: string; status: string;
  pnl: number; return_rate: number;
  trades: TradeRecord[]; logs: AgentLog[];
  created_at: string;
}

export interface TradeRecord {
  id: number; trade_type: string; price: number; quantity: number;
  amount: number; reason?: string; created_at: string;
}

export interface AgentLog {
  id: number; decision: string; price: number;
  kline_granularity: string; indicators_json?: any;
  ai_reasoning?: string; created_at: string;
}

export interface BacktestResult {
  trades: TradeRecord[];
  equity_curve: { date: string; value: number }[];
  summary: {
    initial_capital: number; final_value: number; total_pnl: number;
    total_return_pct: number; trade_count: number;
    max_drawdown_pct: number; win_rate: number;
  };
  message: string;
}

export interface KlineItem {
  date: string; open: number; close: number;
  high: number; low: number; volume: number;
}

export const api = {
  getAgents: () => request<AgentData[]>("/agents"),
  getAgent: (id: number) => request<AgentData>(`/agents/${id}`),
  createAgent: (data: { name: string; stock_code: string; stock_name: string; total_capital: number; strategy: string; mode: string }) =>
    request<AgentData>("/agents", { method: "POST", body: JSON.stringify(data) }),
  updateAgent: (id: number, data: any) =>
    request<AgentData>(`/agents/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteAgent: (id: number) => request<any>(`/agents/${id}`, { method: "DELETE" }),
  executeTrade: (id: number, granularity: string = "daily") =>
    request<any>(`/agents/${id}/execute?granularity=${granularity}`, { method: "POST" }),
  runBacktest: (id: number, start: string, end: string) =>
    request<BacktestResult>(`/agents/${id}/backtest`, { method: "POST", body: JSON.stringify({ start_date: start, end_date: end }) }),
  resetAgent: (id: number) => request<any>(`/agents/${id}/reset`, { method: "POST" }),
  pauseAgent: (id: number) => request<any>(`/agents/${id}/pause`, { method: "POST" }),
  resumeAgent: (id: number) => request<any>(`/agents/${id}/resume`, { method: "POST" }),
  getAgentLogs: (id: number, limit: number = 50) =>
    request<AgentLog[]>(`/agents/${id}/logs?limit=${limit}`),

  preloadStocks: () => request<{ status: string; count: number }>("/stocks/preload"),
  searchStocks: (q: string) => request<{ results: { code: string; name: string }[] }>(`/stocks/search?q=${encodeURIComponent(q)}`),
  getStockInfo: (code: string) => request<{ code: string; name: string }>(`/stocks/${code}`),
  getKline: (code: string, range: number = 120, type: string = "daily") =>
    request<{ code: string; kline: KlineItem[]; type: string }>(`/stocks/${code}/kline?range=${range}&type=${type}`),
  getRealtime: (code: string) => request<{ code: string; name: string; price: number; change_pct: number; volume: number; amount: number }>(`/stocks/${code}/realtime`),
  getTechIndicators: (code: string, type: string = "daily") =>
    request<{ code: string; indicators: any }>(`/stocks/${code}/tech?type=${type}`),
};
