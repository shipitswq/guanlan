from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.agent import Agent, TradeRecord, AgentLog
from app.schemas.agent import AgentCreate, AgentUpdate, BacktestRequest
from app.services.agent_engine import execute_live, run_backtest
from app.services.data_fetcher import DataFetcher

router = APIRouter(prefix="/api/agents", tags=["Agent"])
fetcher = DataFetcher()

def _agent_to_out(a):
    return {
        "id": a.id, "name": a.name,
        "stock_code": a.stock_code, "stock_name": a.stock.name if a.stock else "",
        "total_capital": a.total_capital, "available_cash": a.available_cash,
        "position": a.position, "avg_cost": a.avg_cost,
        "strategy": a.strategy, "mode": a.mode, "status": a.status,
        "pnl": a.pnl, "return_rate": a.return_rate,
        "trades": [], "logs": [],
        "created_at": a.created_at.isoformat() if a.created_at else "",
    }

@router.get("")
def list_agents(db: Session = Depends(get_db)):
    agents = db.execute(select(Agent)).scalars().all()
    return [_agent_to_out(a) for a in agents]

@router.post("")
def create_agent(req: AgentCreate, db: Session = Depends(get_db)):
    agent = Agent(
        name=req.name, stock_code=req.stock_code,
        total_capital=req.total_capital, available_cash=req.total_capital,
        strategy=req.strategy, mode=req.mode, status="active",
        position=0, avg_cost=0.0, pnl=0.0, return_rate=0.0,
    )
    db.add(agent); db.commit(); db.refresh(agent)
    return _agent_to_out(agent)

@router.get("/{agent_id}")
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    trades = db.execute(
        select(TradeRecord).where(TradeRecord.agent_id == agent_id).order_by(TradeRecord.created_at.desc())
    ).scalars().all()
    logs = db.execute(
        select(AgentLog).where(AgentLog.agent_id == agent_id).order_by(AgentLog.created_at.desc()).limit(50)
    ).scalars().all()
    r = _agent_to_out(agent)
    r["trades"] = [{"id": t.id, "trade_type": t.trade_type, "price": t.price,
                     "quantity": t.quantity, "amount": t.amount, "reason": t.reason,
                     "created_at": t.created_at.isoformat() if t.created_at else ""}
                    for t in trades]
    r["logs"] = [{"id": l.id, "decision": l.decision, "price": l.price,
                   "kline_granularity": l.kline_granularity, "indicators_json": l.indicators_json,
                   "ai_reasoning": l.ai_reasoning,
                   "created_at": l.created_at.isoformat() if l.created_at else ""}
                  for l in logs]
    return r

@router.patch("/{agent_id}")
def update_agent(agent_id: int, req: AgentUpdate, db: Session = Depends(get_db)):
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    if req.name is not None: agent.name = req.name
    if req.status is not None: agent.status = req.status
    if req.strategy is not None: agent.strategy = req.strategy
    db.commit(); db.refresh(agent)
    return _agent_to_out(agent)

@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    db.execute(TradeRecord.__table__.delete().where(TradeRecord.agent_id == agent_id))
    db.execute(AgentLog.__table__.delete().where(AgentLog.agent_id == agent_id))
    db.delete(agent); db.commit()
    return {"message": "Agent deleted"}

@router.post("/{agent_id}/execute")
async def execute_agent(agent_id: int, granularity: str = Query("daily", pattern="^(daily|60min)$"),
                         db: Session = Depends(get_db)):
    try:
        result = await execute_live(agent_id, db, granularity)
        return result
    except Exception as e:
        return {"message": f"Execute failed: {str(e)}", "decision": "hold", "trade": None}

@router.post("/{agent_id}/backtest")
async def backtest_agent(agent_id: int, req: BacktestRequest, db: Session = Depends(get_db)):
    try:
        result = await run_backtest(agent_id, req.start_date, req.end_date, db)
        return result
    except Exception as e:
        return {"trades": [], "summary": {}, "message": f"Backtest failed: {str(e)}"}

@router.post("/{agent_id}/reset")
def reset_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    agent.position = 0
    agent.available_cash = agent.total_capital
    agent.avg_cost = 0.0
    agent.pnl = 0.0
    agent.return_rate = 0.0
    db.execute(TradeRecord.__table__.delete().where(TradeRecord.agent_id == agent_id))
    db.execute(AgentLog.__table__.delete().where(AgentLog.agent_id == agent_id))
    db.commit()
    return {"message": "Agent reset"}

@router.post("/{agent_id}/pause")
def pause_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    agent.status = "paused"
    db.commit()
    return {"message": "Agent paused"}

@router.post("/{agent_id}/resume")
def resume_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    agent.status = "active"
    db.commit()
    return {"message": "Agent resumed"}

@router.get("/{agent_id}/logs")
def get_agent_logs(agent_id: int, limit: int = Query(50), db: Session = Depends(get_db)):
    logs = db.execute(
        select(AgentLog).where(AgentLog.agent_id == agent_id)
        .order_by(AgentLog.created_at.desc()).limit(limit)
    ).scalars().all()
    return [{"id": l.id, "decision": l.decision, "price": l.price,
              "kline_granularity": l.kline_granularity, "indicators_json": l.indicators_json,
              "ai_reasoning": l.ai_reasoning,
              "created_at": l.created_at.isoformat() if l.created_at else ""}
             for l in logs]