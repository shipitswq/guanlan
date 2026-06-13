from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Stock(Base):
    __tablename__ = "stocks"
    code = Column(String(10), primary_key=True)
    name = Column(String(100))
    sector = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
