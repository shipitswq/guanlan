"""
Test suite for the A-share simulation trader backend.
Run with: pytest tests/backend/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal
from app.models.agent import Agent, TradeRecord, AgentLog
from sqlalchemy import select
from app.models.stock import Stock
from app.services.rule_engine import decide
from app.services.technical_service import get_technical_analysis
import pandas as pd
import numpy as np

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Initialize clean database for each test."""
    init_db()
    yield
    # Clean up
    db = SessionLocal()
    db.execute(TradeRecord.__table__.delete())
    db.execute(AgentLog.__table__.delete())
    db.execute(Agent.__table__.delete())
    db.execute(Stock.__table__.delete())
    db.commit()
    db.close()


def make_agent(name="TestAgent", stock="000001"):
    """Helper to create an agent via API."""
    resp = client.post("/api/agents", json={
        "name": name, "stock_code": stock, "total_capital": 100000,
        "strategy": "rule", "mode": "live",
    })
    assert resp.status_code == 200
    return resp.json()


# ===== API Tests =====

class TestAgentAPI:
    def test_health(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_create_agent(self):
        a = make_agent()
        assert a["name"] == "TestAgent"
        assert a["total_capital"] == 100000
        assert a["available_cash"] == 100000
        assert a["strategy"] == "rule"
        assert a["status"] == "active"

    def test_list_agents(self):
        make_agent("Agent1")
        make_agent("Agent2", "600519")
        resp = client.get("/api/agents")
        data = resp.json()
        assert len(data) == 2

    def test_get_agent(self):
        a = make_agent()
        resp = client.get(f"/api/agents/{a['id']}")
        data = resp.json()
        assert data["id"] == a["id"]
        assert "trades" in data
        assert "logs" in data

    def test_update_agent(self):
        a = make_agent()
        resp = client.patch(f"/api/agents/{a['id']}", json={"status": "paused"})
        assert resp.json()["status"] == "paused"
        resp = client.patch(f"/api/agents/{a['id']}", json={"strategy": "ai"})
        assert resp.json()["strategy"] == "ai"

    def test_delete_agent(self):
        a = make_agent()
        resp = client.delete(f"/api/agents/{a['id']}")
        assert resp.status_code == 200
        resp = client.get("/api/agents")
        assert len(resp.json()) == 0

    def test_execute_agent(self):
        a = make_agent()
        resp = client.post(f"/api/agents/{a['id']}/execute")
        assert resp.status_code == 200
        result = resp.json()
        assert result["decision"] in ("buy", "sell", "hold")

    def test_execute_granularity(self):
        a = make_agent()
        resp = client.post(f"/api/agents/{a['id']}/execute?granularity=60min")
        assert resp.status_code == 200
        result = resp.json()
        assert result["decision"] in ("buy", "sell", "hold")

    def test_pause_resume(self):
        a = make_agent()
        client.post(f"/api/agents/{a['id']}/pause")
        resp = client.post(f"/api/agents/{a['id']}/execute")
        assert resp.json()["message"] == "Agent paused"
        client.post(f"/api/agents/{a['id']}/resume")
        resp = client.post(f"/api/agents/{a['id']}/execute")
        assert resp.json()["decision"] in ("buy", "sell", "hold")

    def test_reset_agent(self):
        a = make_agent()
        client.post(f"/api/agents/{a['id']}/execute")
        resp = client.post(f"/api/agents/{a['id']}/reset")
        assert resp.status_code == 200
        data = client.get(f"/api/agents/{a['id']}").json()
        assert data["position"] == 0
        assert data["pnl"] == 0.0

    def test_backtest(self):
        a = make_agent()
        resp = client.post(f"/api/agents/{a['id']}/backtest", json={
            "start_date": "2025-01-01", "end_date": "2025-12-31"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "trades" in data

    def test_agent_logs(self):
        a = make_agent()
        client.post(f"/api/agents/{a['id']}/execute")
        resp = client.get(f"/api/agents/{a['id']}/logs")
        logs = resp.json()
        assert len(logs) >= 1
        assert logs[0]["decision"] in ("buy", "sell", "hold")


class TestStockAPI:
    def test_search(self):
        resp = client.get("/api/stocks/search?q=000001")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    def test_stock_info(self):
        resp = client.get("/api/stocks/000001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "000001"


# ===== Unit Tests =====

class TestTechnicalService:
    def test_synthetic_data_analysis(self):
        np.random.seed(42)
        dates = pd.date_range("2025-01-01", periods=120, freq="D")
        prices = 50 + np.cumsum(np.random.normal(0, 0.5, 120))
        df = pd.DataFrame({
            "date": dates.strftime("%Y-%m-%d"),
            "open": prices, "close": prices,
            "high": prices * 1.02, "low": prices * 0.98,
            "volume": np.abs(prices) * 5000,
        })
        import asyncio
        tech = asyncio.run(get_technical_analysis(df))
        assert "current_price" in tech
        assert tech["rsi"] is not None
        assert 0 <= tech["rsi"] <= 100
        assert tech["ma5"] is not None
        assert tech["ma20"] is not None
        assert isinstance(tech["bollinger"]["position"], str)

    def test_ma_calculation(self):
        close = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        from app.services.technical_service import _ma
        result = _ma(close, 3)
        assert result is not None
        assert len(result) == 6  # 8 - 3 + 1
        assert np.isclose(result[0], 2.0)


class TestRuleEngine:
    def test_buy_decision(self):
        class MockAgent:
            available_cash = 100000
            position = 0
        agent = MockAgent()
        tech = {
            "current_price": 50.0,
            "rsi": 30.0,
            "rsi_trend": "up",
            "ma5": 48.0,
            "ma20": 46.0,
            "ma5_trend": "up",
            "macd": {"golden_cross": True, "histogram": 0.5, "macd": 0, "signal": 0, "dead_cross": False},
            "bollinger": {"position": "below_lower", "upper": 55, "mid": 50, "lower": 45},
            "kdj": {"k": 20, "d": 22, "j": 16},
        }
        result = decide(agent, tech)
        assert result["decision"] == "buy"
        assert result["quantity"] >= 100

    def test_sell_decision(self):
        class MockAgent:
            available_cash = 50000
            position = 1000
        agent = MockAgent()
        tech = {
            "current_price": 60.0,
            "rsi": 75.0,
            "rsi_trend": "down",
            "ma5": 62.0,
            "ma20": 58.0,
            "ma20_trend": "down",
            "ma5_trend": "down",
            "macd": {"dead_cross": True, "histogram": -0.5, "macd": 0, "signal": 0, "golden_cross": False},
            "bollinger": {"position": "above_upper", "upper": 65, "mid": 58, "lower": 51},
            "kdj": {"k": 80, "d": 78, "j": 84},
        }
        result = decide(agent, tech)
        assert result["decision"] in ("sell", "hold")

    def test_hold_decision(self):
        class MockAgent:
            available_cash = 100000
            position = 0
        agent = MockAgent()
        tech = {
            "current_price": 50.0,
            "rsi": 50.0,
            "rsi_trend": "flat",
            "ma5": 50.5, "ma20": 50.0,
            "ma5_trend": "flat", "ma20_trend": "flat",
            "macd": {"histogram": 0, "macd": 0, "signal": 0, "golden_cross": False, "dead_cross": False},
            "bollinger": {"position": "middle", "upper": 55, "mid": 50, "lower": 45},
            "kdj": {"k": 50, "d": 50, "j": 50},
        }
        result = decide(agent, tech)
        assert result["decision"] == "hold"

    def test_no_cash_for_buy(self):
        class MockAgent:
            available_cash = 100
            position = 0
        agent = MockAgent()
        tech = {"current_price": 50.0, "rsi": 30.0, "rsi_trend": "up",
                "macd": {"golden_cross": True, "histogram": 0.5, "macd": 0, "signal": 0, "dead_cross": False},
                "bollinger": {"position": "below_lower", "upper": 55, "mid": 50, "lower": 45},
                "kdj": {"k": 20, "d": 22, "j": 16}}
        result = decide(agent, tech)
        assert result["decision"] != "buy"

# ===== Edge Case & Boundary Tests =====

class TestEdgeCases:
    """Boundary conditions, error handling, and A-share market rule enforcement."""

    def test_invalid_agent_id(self):
        """???? Agent ID ?? 404"""
        resp = client.get("/api/agents/99999")
        assert resp.status_code == 404

        resp = client.patch("/api/agents/99999", json={"status": "paused"})
        assert resp.status_code == 404

        resp = client.delete("/api/agents/99999")
        assert resp.status_code == 404

        resp = client.post("/api/agents/99999/execute")
        data = resp.json()
        assert data["decision"] == "hold"
        assert "does not exist" in data["message"]

    def test_t1_restriction_blocks_sell(self):
        """T+1 ??????????????????????"""
        from app.services import rule_engine
        from datetime import datetime

        a = make_agent()
        agent_id = a["id"]

        # Set up: agent holds 1000 shares, 800 bought today
        db = SessionLocal()
        agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one()
        agent.position = 1000
        agent.available_cash = 50000
        agent.avg_cost = 50.0

        today_buy = TradeRecord(
            agent_id=agent_id, trade_type="buy", price=50.0,
            quantity=800, amount=40000.0, reason="Today buy",
            created_at=datetime.utcnow(),
        )
        db.add(today_buy)
        db.commit()
        db.close()

        original_decide = rule_engine.decide
        def mock_sell_above_t1(agt, tech):
            return {"decision": "sell", "quantity": 1000, "reason": "Mock sell signal"}
        rule_engine.decide = mock_sell_above_t1

        try:
            resp = client.post(f"/api/agents/{agent_id}/execute")
            result = resp.json()
            assert result["decision"] in ("sell", "hold")
            if result["trade"] and result["trade"]["trade_type"] == "sell":
                # T+1 restricts: 1000 - 800 = 200 max sellable
                assert result["trade"]["quantity"] <= 200, \
                    f"T+1 should cap sell to <=200, got {result['trade']['quantity']}"
            if result["decision"] == "hold" and today_buy.quantity >= 900:
                pass  # T+1 may block entirely if sellable < 100
        finally:
            rule_engine.decide = original_decide

    def test_t1_restriction_full_block(self):
        """T+1 ?????????????????"""
        from app.services import rule_engine
        from datetime import datetime

        a = make_agent()
        agent_id = a["id"]

        db = SessionLocal()
        agent = db.execute(select(Agent).where(Agent.id == agent_id)).scalar_one()
        agent.position = 500
        agent.available_cash = 50000

        today_buy = TradeRecord(
            agent_id=agent_id, trade_type="buy", price=50.0,
            quantity=500, amount=25000.0, reason="All today buy",
            created_at=datetime.utcnow(),
        )
        db.add(today_buy)
        db.commit()
        db.close()

        original_decide = rule_engine.decide
        def mock_sell_all(agt, tech):
            return {"decision": "sell", "quantity": 500, "reason": "Mock full sell"}
        rule_engine.decide = mock_sell_all

        try:
            resp = client.post(f"/api/agents/{agent_id}/execute")
            result = resp.json()
            # all 500 bought today ? sellable=0 ? should hold
            assert result["decision"] == "hold", \
                f"T+1 should force hold when all shares bought today, got {result['decision']}"
            assert result["trade"] is None
        finally:
            rule_engine.decide = original_decide

    def test_buy_quantity_multiple_of_100(self):
        """??????? 100 ???"""
        from app.services import rule_engine

        a = make_agent()

        original_decide = rule_engine.decide
        def mock_buy(agt, tech):
            return {"decision": "buy", "quantity": 250, "reason": "Mock buy"}
        rule_engine.decide = mock_buy

        try:
            resp = client.post(f"/api/agents/{a['id']}/execute")
            result = resp.json()
            if result["trade"] and result["trade"]["trade_type"] == "buy":
                assert result["trade"]["quantity"] % 100 == 0, \
                    f"Buy quantity should be multiple of 100, got {result['trade']['quantity']}"
        finally:
            rule_engine.decide = original_decide

    def test_no_short_selling(self):
        """??????????0?????"""
        from app.services import rule_engine

        a = make_agent()
        # Agent has position=0 and cash=100k by default

        original_decide = rule_engine.decide
        def mock_short(agt, tech):
            return {"decision": "sell", "quantity": 500, "reason": "Mock short sell"}
        rule_engine.decide = mock_short

        try:
            resp = client.post(f"/api/agents/{a['id']}/execute")
            result = resp.json()
            assert result["decision"] == "hold", \
                f"Should not sell with 0 position, got {result['decision']}"
            assert result["trade"] is None
        finally:
            rule_engine.decide = original_decide

    def test_empty_cash_no_buy(self):
        """?????????????100??????"""
        from app.services import rule_engine

        a = make_agent()

        db = SessionLocal()
        agent = db.execute(select(Agent).where(Agent.id == a["id"])).scalar_one()
        agent.available_cash = 50  # Not enough for 1 share
        db.commit()
        db.close()

        original_decide = rule_engine.decide
        def mock_buy_empty(agt, tech):
            return {"decision": "buy", "quantity": 1000, "reason": "Mock buy"}
        rule_engine.decide = mock_buy_empty

        try:
            resp = client.post(f"/api/agents/{a['id']}/execute")
            result = resp.json()
            assert result["decision"] == "hold", \
                f"Should not buy with insufficient cash, got {result['decision']}"
            assert result["trade"] is None
        finally:
            rule_engine.decide = original_decide

    def test_empty_position_no_sell(self):
        """?????????0?????"""
        from app.services import rule_engine

        a = make_agent()

        original_decide = rule_engine.decide
        def mock_sell_empty(agt, tech):
            return {"decision": "sell", "quantity": 100, "reason": "Mock sell"}
        rule_engine.decide = mock_sell_empty

        try:
            resp = client.post(f"/api/agents/{a['id']}/execute")
            result = resp.json()
            assert result["decision"] == "hold"
            assert result["trade"] is None
        finally:
            rule_engine.decide = original_decide

    def test_execute_60min_granularity(self):
        """60?????? - ??60min???????????"""
        a = make_agent()
        resp = client.post(f"/api/agents/{a['id']}/execute?granularity=60min")
        assert resp.status_code == 200
        result = resp.json()
        assert result["decision"] in ("buy", "sell", "hold")

        # Verify log records the 60min granularity
        logs_resp = client.get(f"/api/agents/{a['id']}/logs")
        logs = logs_resp.json()
        if logs:
            assert logs[0]["kline_granularity"] == "60min", \
                f"Expected 60min in log, got {logs[0]['kline_granularity']}"

    def test_search_stock_results_format(self):
        """???? API - ??????"""
        resp = client.get("/api/stocks/search?q=000001")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        if data["results"]:
            r = data["results"][0]
            assert "code" in r
            assert "name" in r
