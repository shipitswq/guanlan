from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_engine("sqlite:///./stock_sim.db", echo=False)
SessionLocal = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models.agent import Agent, TradeRecord, AgentLog
    from app.models.stock import Stock
    Base.metadata.create_all(engine)
