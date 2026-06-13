"""Core trading agent engine - orchestrates data fetch, analysis, and trade execution."""
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.agent import Agent, TradeRecord, AgentLog
from app.services.data_fetcher import DataFetcher
from app.services.technical_service import get_technical_analysis
from app.services.rule_engine import decide as rule_decide
from app.services.ai_analysis import agent_decide_trade

fetcher = DataFetcher()

async def execute_live(agent_id: int, db: Session, granularity: str = "daily") -> dict:
    """Execute a single trading decision for an agent (live mode).
    
    Args:
        agent_id: Agent ID
        db: DB session
        granularity: "daily" or "60min"
    """
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        return {"message": "Agent does not exist", "decision": "hold", "trade": None}
    if agent.status == "paused":
        return {"message": "Agent paused", "decision": "hold", "trade": None}

    result = await _make_decision(agent, granularity)
    decision = result["decision"]
    qty = result["quantity"]
    reason = result["reason"]
    price = result["price"]
    indicators = result["indicators"]

    trade_record = None
    if decision == "buy" and qty > 0:
        trade_record = _execute_buy(agent, price, qty, reason, db)
    elif decision == "sell" and qty > 0:
        # T+1 check: shares bought today cannot be sold
        today_bought = _get_today_bought_qty(agent.id, db)
        qty = _apply_t1_restriction(agent, qty, today_bought)
        if qty >= 100:
            trade_record = _execute_sell(agent, price, qty, reason, db)
        else:
            decision = "hold"
            qty = 0

    # Save decision log
    log = AgentLog(
        agent_id=agent.id,
        decision=decision,
        price=price,
        kline_granularity=granularity,
        indicators_json=indicators,
        ai_reasoning=result.get("ai_reasoning"),
    )
    db.add(log)
    db.commit()

    msg = f"决策: {decision}"
    if trade_record:
        msg += f", {trade_record.trade_type} {trade_record.quantity}股 @ {trade_record.price:.2f}"
    else:
        msg += f", {reason}"

    return {
        "message": msg,
        "decision": decision,
        "trade": {
            "id": trade_record.id,
            "trade_type": trade_record.trade_type,
            "price": trade_record.price,
            "quantity": trade_record.quantity,
            "amount": trade_record.amount,
            "reason": trade_record.reason,
            "created_at": trade_record.created_at.isoformat(),
        } if trade_record else None,
    }

async def run_backtest(agent_id: int, start: str, end: str, db: Session) -> dict:
    """Run a historical backtest for an agent."""
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        return {"trades": [], "summary": {}, "message": "Agent does not exist"}

    # Reset agent for backtest
    original_capital = agent.total_capital
    sim_cash = agent.total_capital
    sim_position = 0
    sim_avg_cost = 0.0

    df = await fetcher.get_stock_hist(agent.stock_code, start, end, "daily")
    if df.empty or len(df) < 7:
        return {"trades": [], "summary": {}, "message": "历史数据不足，至少需要30个交易日"}

    trades = []
    equity_curve = []

    for i in range(5, len(df)):  # Start from index 20 to have enough MA data
        window = df.iloc[:i+1].copy()
        tech = await get_technical_analysis(window)
        price = float(df.iloc[i]["close"])

        # Create a mock agent for the rule engine
        class MockAgent:
            pass
        mock = MockAgent()
        mock.available_cash = sim_cash
        mock.position = sim_position

        dec = rule_decide(mock, tech)
        if dec["decision"] == "buy" and dec["quantity"] > 0:
            qty = dec["quantity"]
            cost = price * qty
            if cost <= sim_cash:
                sim_cash -= cost
                sim_avg_cost = (sim_avg_cost * sim_position + cost) / (sim_position + qty) if (sim_position + qty) > 0 else price
                sim_position += qty
                trades.append({"trade_type": "buy", "price": round(price, 2), "quantity": qty,
                               "amount": round(cost, 2), "reason": dec["reason"],
                               "date": df.iloc[i]["date"]})
        elif dec["decision"] == "sell" and dec["quantity"] > 0 and sim_position >= dec["quantity"]:
            qty = dec["quantity"]
            revenue = price * qty
            sim_cash += revenue
            sim_position -= qty
            trades.append({"trade_type": "sell", "price": round(price, 2), "quantity": qty,
                           "amount": round(revenue, 2), "reason": dec["reason"],
                           "date": df.iloc[i]["date"]})

        total_value = sim_cash + sim_position * price
        equity_curve.append({"date": df.iloc[i]["date"], "value": round(total_value, 2)})

    # Final portfolio value
    final_price = float(df.iloc[-1]["close"])
    final_value = sim_cash + sim_position * final_price
    total_pnl = final_value - original_capital
    total_return = (total_pnl / original_capital) * 100

    # Max drawdown
    peak = 0
    max_dd = 0
    for entry in equity_curve:
        if entry["value"] > peak:
            peak = entry["value"]
        dd = (peak - entry["value"]) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

    win_count = sum(1 for t in trades if t["trade_type"] == "sell" and t["amount"] > 0)

    first_price = float(df.iloc[0]["close"]) if not df.empty else 0
    buy_hold_return = (final_price / first_price - 1) * 100 if first_price > 0 else 0

    summary = {
        "initial_capital": original_capital,
        "final_value": round(final_value, 2),
        "total_pnl": round(total_pnl, 2),
        "total_return_pct": round(total_return, 2),
        "trade_count": len(trades),
        "max_drawdown_pct": round(max_dd, 2),
        "win_rate": round(win_count / max(len([t for t in trades if t["trade_type"] == "sell"]), 1) * 100, 1),
        "buy_hold_return_pct": round(buy_hold_return, 2),
    }

    return {"trades": trades, "equity_curve": equity_curve, "summary": summary, "message": f"回测完成，共{len(trades)}笔交易"}

async def _make_decision(agent, granularity: str) -> dict:
    """Core decision logic - shared by live and backtest."""
    # Fetch latest data
    start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
    df = await fetcher.get_stock_hist(agent.stock_code, start, None, granularity)
    tech = await get_technical_analysis(df)

    if isinstance(tech, dict) and "error" in tech:
        return {"decision": "hold", "quantity": 0, "price": 0,
                "reason": f"数据获取失败: {tech['error']}", "indicators": tech}

    # Get real-time price for live trading
    rt = await fetcher.get_realtime_price(agent.stock_code)
    current_price = rt.get("price", tech.get("current_price", 0))
    tech["current_price"] = current_price

    if agent.strategy == "ai":
        stock_name = agent.stock.name if agent.stock else ""
        dec = await agent_decide_trade(
            agent.stock_code, stock_name, tech,
            agent.position, agent.avg_cost, agent.available_cash,
            agent.total_capital, granularity
        )
    else:
        dec = rule_decide(agent, tech)

    qty = dec.get("quantity", 0)
    decision = dec.get("decision", "hold")

    # Validate quantities
    if decision == "buy":
        cost = current_price * qty
        if cost > agent.available_cash:
            qty = int(agent.available_cash * 0.9 / (current_price * 100)) * 100
            qty = max(qty, 0)
        if qty < 100:
            decision = "hold"
            qty = 0
    elif decision == "sell":
        qty = min(qty, agent.position)
        if qty < 100:
            decision = "hold"
            qty = 0

    return {
        "decision": decision,
        "quantity": qty,
        "price": current_price,
        "reason": dec.get("reason", ""),
        "indicators": {k: v for k, v in tech.items() if k not in ("error",)},
        "ai_reasoning": dec.get("ai_reasoning"),
    }

def _execute_buy(agent, price: float, qty: int, reason: str, db: Session):
    cost = round(price * qty, 2)
    agent.available_cash = round(agent.available_cash - cost, 2)
    agent.avg_cost = round((agent.avg_cost * agent.position + cost) / (agent.position + qty), 2) if (agent.position + qty) > 0 else price
    agent.position += qty
    trade = TradeRecord(agent_id=agent.id, trade_type="buy", price=price,
                        quantity=qty, amount=cost, reason=reason)
    db.add(trade)
    _update_pnl(agent, price)
    return trade

def _execute_sell(agent, price: float, qty: int, reason: str, db: Session):
    revenue = round(price * qty, 2)
    agent.available_cash = round(agent.available_cash + revenue, 2)
    agent.position -= qty
    if agent.position == 0:
        agent.avg_cost = 0.0
    trade = TradeRecord(agent_id=agent.id, trade_type="sell", price=price,
                        quantity=qty, amount=revenue, reason=reason)
    db.add(trade)
    _update_pnl(agent, price)
    return trade

def _update_pnl(agent, current_price: float):
    total_value = agent.available_cash + agent.position * current_price


def _get_today_bought_qty(agent_id: int, db: Session) -> int:
    """Get total shares bought today for this agent (for T+1 enforcement).
    
    In A-share market, shares bought on trading day T cannot be sold until T+1.
    This function returns the quantity bought since today 00:00:00 UTC.
    """
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_buys = db.execute(
        select(TradeRecord).where(
            TradeRecord.agent_id == agent_id,
            TradeRecord.trade_type == "buy",
            TradeRecord.created_at >= today_start
        )
    ).scalars().all()
    return sum(t.quantity for t in today_buys)


def _apply_t1_restriction(agent, desired_qty: int, today_bought_qty: int) -> int:
    """Apply T+1 rule, returning the maximum sellable quantity.
    
    Returns:
        Adjusted sell quantity that respects T+1 (shares bought today not sold).
        If result < 100, the caller should treat it as a hold.
    """
    sellable = max(0, agent.position - today_bought_qty)
    return min(desired_qty, sellable)


# Backward-compatible aliases (used by older tests)
_execute_trade = execute_live


class Portfolio:
    """Portfolio tracking for backtesting."""
    def __init__(self, cash: float):
        self.cash = cash
        self.position = 0
        self.trades = []

    def add_trade(self, trade):
        self.trades.append(trade)
