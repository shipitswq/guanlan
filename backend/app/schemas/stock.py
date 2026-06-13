from pydantic import BaseModel
from typing import Optional

class StockInfo(BaseModel):
    code: str
    name: str
    sector: Optional[str] = ""

class KlineItem(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float

class RealtimeQuote(BaseModel):
    code: str
    name: str
    price: float
    change_pct: float
    volume: float
    amount: float
