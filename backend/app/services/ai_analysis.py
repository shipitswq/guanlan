"""Call LLM for AI-driven trading decisions."""
import json
from typing import Optional
from app.config import settings

SYSTEM_PROMPT = """你是一位经验丰富的A股交易员，擅长基于技术分析做出交易决策。

请你分析提供的股票技术指标和持仓信息，然后做出买入(buy)、卖出(sell)或持有(hold)的决策。

决策原则：
- 只基于技术指标和当前市场数据做判断
- 买入信号：RSI超卖且拐头、MACD金叉、价格站上均线、布林带下轨支撑
- 卖出信号：RSI超买且拐头、MACD死叉、价格跌破均线、布林带上轨压力
- 无明确信号时持有
- 注意控制仓位，不要满仓操作
- 考虑T+1限制，买入后次日才能卖出

请回复JSON格式：
{"decision": "buy|sell|hold", "quantity": 股数, "reason": "决策理由"}
- quantity: 买入时用可用资金的30%计算(100的整数倍)，卖出时卖1/3持仓(100的整数倍)
- reason: 用中文简洁说明判断依据
"""

async def agent_decide_trade(
    stock_code: str,
    stock_name: str,
    tech: dict,
    position: int,
    avg_cost: float,
    available_cash: float,
    total_capital: float,
    granularity: str = "daily"
) -> dict:
    """Ask LLM for a trading decision."""
    if not settings.openai_api_key:
        # Fall back to rule-based if no API key
        return {"decision": "hold", "quantity": 0, "reason": "未配置OpenAI API Key，跳过AI决策"}

    current_price = tech.get("current_price", 0)
    position_value = current_price * position
    total_assets = available_cash + position_value
    pnl = total_assets - total_capital
    return_rate = (pnl / total_capital * 100) if total_capital > 0 else 0

    user_prompt = f"""请分析以下A股数据并做出交易决策：

【股票信息】
代码: {stock_code}
名称: {stock_name}
K线周期: {"日线" if granularity == "daily" else "60分钟线"}

【当前价格】
最新价: {current_price} 元

【技术指标】
MA5: {tech.get("ma5", "N/A")}
MA20: {tech.get("ma20", "N/A")}
MA60: {tech.get("ma60", "N/A")}
RSI(14): {tech.get("rsi", "N/A")}
MACD: {tech.get("macd", {})}
布林带: {tech.get("bollinger", {})}
KDJ: {tech.get("kdj", {})}

【持仓情况】
持仓股数: {position} 股
持仓均价: {avg_cost:.2f} 元
可用现金: {available_cash:.2f} 元
总资产: {total_assets:.2f} 元
累计盈亏: {pnl:+.2f} 元 ({return_rate:+.2f}%)

请你做出交易决策，返回JSON格式结果。"""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=500,
        )
        content = resp.choices[0].message.content
        result = json.loads(content)
        decision = result.get("decision", "hold")
        qty = int(result.get("quantity", 0))
        reason = result.get("reason", "AI决策")

        # Validate decision
        if decision == "buy" and qty > 0:
            cost = current_price * qty
            if cost > available_cash:
                qty = int(available_cash * 0.9 / (current_price * 100)) * 100
                qty = max(qty, 0)
        elif decision == "sell" and qty > 0:
            qty = min(qty, position)
            if qty < 100:
                qty = 0

        return {"decision": decision, "quantity": qty, "reason": reason}
    except Exception as e:
        return {"decision": "hold", "quantity": 0, "reason": f"AI决策失败: {str(e)}"}
