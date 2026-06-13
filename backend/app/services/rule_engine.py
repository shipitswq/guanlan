"""Rule-based trading strategy using technical indicators."""

def decide(agent, tech: dict) -> dict:
    """Make a trading decision based on technical indicators."""
    if not tech or "error" in tech:
        return {"decision": "hold", "quantity": 0, "reason": "No valid indicators"}

    current_price = float(tech.get("current_price", 0))
    if current_price <= 0:
        return {"decision": "hold", "quantity": 0, "reason": "Invalid price"}

    score = 0.0
    signals = []

    # RSI
    rsi = float(tech.get("rsi", 50))
    rsi_trend = tech.get("rsi_trend", "flat")
    if rsi < 35:
        score += 1.0
        signals.append("RSI oversold")
    elif rsi < 45:
        score += 0.5
        signals.append("RSI weak")
    elif rsi > 70:
        score -= 1.0
        signals.append("RSI overbought")
    elif rsi > 60:
        score -= 0.5
        signals.append("RSI strong")

    if rsi_trend == "up" and rsi < 50:
        score += 0.5
    elif rsi_trend == "down" and rsi > 50:
        score -= 0.5

    # MACD
    macd = tech.get("macd", {})
    if macd.get("golden_cross"):
        score += 1.5
        signals.append("MACD golden cross")
    elif macd.get("dead_cross"):
        score -= 1.5
        signals.append("MACD dead cross")
    hist = float(macd.get("histogram", 0))
    if hist > 0:
        score += 0.5
        signals.append("MACD positive")
    elif hist < 0:
        score -= 0.5
        signals.append("MACD negative")

    # MA
    ma5_val = tech.get("ma5")
    ma20_val = tech.get("ma20")
    if ma5_val is not None and ma20_val is not None:
        ma5_f = float(ma5_val)
        ma20_f = float(ma20_val)
        if current_price > ma5_f > ma20_f:
            score += 1.0
            signals.append("Bullish alignment")
        elif current_price < ma5_f < ma20_f:
            score -= 1.0
            signals.append("Bearish alignment")

    ma5_trend = tech.get("ma5_trend", "flat")
    if ma5_trend == "up":
        score += 0.5
    elif ma5_trend == "down":
        score -= 0.5

    # Bollinger
    bb = tech.get("bollinger", {})
    bb_pos = bb.get("position", "unknown")
    if bb_pos == "below_lower":
        score += 0.5
        signals.append("Below lower BB")
    elif bb_pos == "above_upper":
        score -= 0.5
        signals.append("Above upper BB")
    elif bb_pos == "lower_band":
        score += 0.3
    elif bb_pos == "upper_band":
        score -= 0.3

    # KDJ
    kdj = tech.get("kdj", {})
    try:
        k_val = float(kdj.get("k", 50))
        d_val = float(kdj.get("d", 50))
        if k_val < 25 and d_val < 25:
            score += 0.5
            signals.append("KDJ oversold")
        elif k_val > 75 and d_val > 75:
            score -= 0.5
            signals.append("KDJ overbought")
    except (TypeError, ValueError):
        pass

    cash = agent.available_cash
    position = agent.position

    reason = " | ".join(signals) + f" [score={score:.1f}]" if signals else f"No clear signal [score={score:.1f}]"

    if score >= 2.5 and cash > current_price * 100:
        max_shares = int(cash * 0.3 / (current_price * 100)) * 100
        if max_shares >= 100:
            return {"decision": "buy", "quantity": min(max_shares, 10000), "reason": reason}

    elif score <= -2.0 and position >= 100:
        sell_qty = max(100, position // 3)
        return {"decision": "sell", "quantity": sell_qty, "reason": reason}

    return {"decision": "hold", "quantity": 0, "reason": reason}