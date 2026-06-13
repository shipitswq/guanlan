from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AgentCreate(BaseModel):
    name: str
    stock_code: str
    stock_name: str = ""
    total_capital: float = 100000.0
    strategy: str = "ai"
    mode: str = "live"

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    strategy: Optional[str] = None

class AgentOut(BaseModel):
    id: int
    name: str
    stock_code: str
    stock_name: str = ""
    total_capital: float
    available_cash: float
    position: int
    avg_cost: float
    strategy: str
    mode: str
    status: str
    pnl: float
    return_rate: float
    created_at: str = ""
    model_config = {"from_attributes": True}

class TradeRecordOut(BaseModel):
    id: int
    trade_type: str
    price: float
    quantity: int
    amount: float
    reason: Optional[str] = None
    created_at: str = ""
    model_config = {"from_attributes": True}

class AgentLogOut(BaseModel):
    id: int
    decision: str
    price: float
    kline_granularity: str
    indicators_json: Optional[dict] = None
    ai_reasoning: Optional[str] = None
    created_at: str = ""
    model_config = {"from_attributes": True}

class AgentDetailOut(AgentOut):
    trades: list[TradeRecordOut] = []
    logs: list[AgentLogOut] = []

class BacktestRequest(BaseModel):
    start_date: str
    end_date: str

class ExecuteResult(BaseModel):
    message: str
    trade: Optional[TradeRecordOut] = None
    decision: str = ""
