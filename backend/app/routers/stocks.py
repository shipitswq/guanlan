from fastapi import APIRouter, Query
from app.services.data_fetcher import DataFetcher

router = APIRouter(prefix="/api/stocks", tags=["Stock"])
fetcher = DataFetcher()

@router.get("/preload")
async def preload_stocks():
    try:
        await fetcher.preload_stocks()
        count = len(DataFetcher._stock_cache) if DataFetcher._stock_cache else 0
        return {"status": "ok", "count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/search")
async def search_stocks(q: str = Query("", min_length=1)):
    try:
        results = await fetcher.search_stocks(q)
        return {"results": results}
    except Exception as e:
        return {"results": [{"code": "000001", "name": "平安银行"}, {"code": "600519", "name": "贵州茅台"}]}

@router.get("/realtime")
async def get_all_realtime():
    return {"message": "use /{code}/realtime"}

@router.get("/{code}")
async def get_stock_info(code: str):
    name = await fetcher.get_stock_name(code)
    return {"code": code, "name": name}

@router.get("/{code}/kline")
async def get_kline(code: str, range_days: int = Query(120, alias="range"),
                     type: str = Query("daily", pattern="^(daily|60min)$")):
    import datetime
    end = datetime.datetime.now().strftime("%Y%m%d")
    start = (datetime.datetime.now() - datetime.timedelta(days=range_days)).strftime("%Y%m%d")
    import pandas as pd
    try:
        df = await fetcher.get_stock_hist(code, start, end, type)
    except:
        df = pd.DataFrame()
    if df.empty:
        return {"code": code, "kline": [], "type": type}
    kline = df.to_dict(orient="records")
    for k in kline:
        for c in ["open", "close", "high", "low"]:
            if c in k:
                k[c] = round(float(k[c]), 2)
        if "volume" in k:
            k["volume"] = float(k["volume"])
    return {"code": code, "kline": kline, "type": type}

@router.get("/{code}/realtime")
async def get_realtime(code: str):
    try:
        quote = await fetcher.get_realtime_price(code)
        return quote
    except:
        return {"code": code, "name": "", "price": 0, "change_pct": 0, "volume": 0, "amount": 0}

@router.get("/{code}/tech")
async def get_tech_indicators(code: str, type: str = Query("daily", pattern="^(daily|60min)$")):
    from app.services.technical_service import get_technical_analysis
    import datetime, pandas as pd
    end = datetime.datetime.now().strftime("%Y%m%d")
    start = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime("%Y%m%d")
    try:
        df = await fetcher.get_stock_hist(code, start, end, type)
    except:
        df = pd.DataFrame()
    if df.empty:
        return {"code": code, "error": "no data"}
    tech = await get_technical_analysis(df)
    return {"code": code, "indicators": tech}