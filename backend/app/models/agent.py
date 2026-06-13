from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    stock_code = Column(String(10), ForeignKey("stocks.code"))
    stock = relationship("Stock")
    total_capital = Column(Float, default=100000.0)
    available_cash = Column(Float, default=100000.0)
    position = Column(Integer, default=0)
    avg_cost = Column(Float, default=0.0)
    strategy = Column(String(20), default="ai")        # ai / rule
    mode = Column(String(20), default="live")           # live / backtest
    status = Column(String(20), default="active")       # active / paused
    pnl = Column(Float, default=0.0)
    return_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trades = relationship("TradeRecord", back_populates="agent", order_by="TradeRecord.created_at.desc()")
    logs = relationship("AgentLog", back_populates="agent", order_by="AgentLog.created_at.desc()")

class TradeRecord(Base):
    __tablename__ = "trade_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    agent = relationship("Agent", back_populates="trades")
    trade_type = Column(String(10))  # buy / sell
    price = Column(Float)
    quantity = Column(Integer)
    amount = Column(Float)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    agent = relationship("Agent", back_populates="logs")
    decision = Column(String(10))   # buy / sell / hold
    price = Column(Float)
    kline_granularity = Column(String(20), default="daily")  # daily / 60min
    indicators_json = Column(JSON, nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
