"""Fetch A-share market data via akshare, with synthetic/cached fallback."""
from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd
import numpy as np
import os, json, hashlib, asyncio

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

COMMON_STOCKS = [
    {"code": "000001", "name": "平安银行"}, {"code": "000002", "name": "万科A"},
    {"code": "000333", "name": "美的集团"}, {"code": "000651", "name": "格力电器"},
    {"code": "000858", "name": "五粮液"}, {"code": "002415", "name": "海康威视"},
    {"code": "002594", "name": "比亚迪"}, {"code": "002714", "name": "牧原股份"},
    {"code": "002475", "name": "立讯精密"}, {"code": "300750", "name": "宁德时代"},
    {"code": "300059", "name": "东方财富"}, {"code": "600000", "name": "浦发银行"},
    {"code": "600036", "name": "招商银行"}, {"code": "600104", "name": "上汽集团"},
    {"code": "600276", "name": "恒瑞医药"}, {"code": "600309", "name": "万华化学"},
    {"code": "600519", "name": "贵州茅台"}, {"code": "600900", "name": "长江电力"},
    {"code": "601318", "name": "中国平安"}, {"code": "601398", "name": "工商银行"},
    {"code": "601857", "name": "中国石油"}, {"code": "601988", "name": "中国银行"},
    {"code": "603259", "name": "药明康德"}, {"code": "688981", "name": "中芯国际"},
]

class DataFetcher:
    """Fetch stock data from akshare; use cached/synthetic fallback."""

    def __init__(self):
        self._akshare = None
        self._has_akshare = False
        try:
            import akshare as ak
            self._akshare = ak
            self._has_akshare = True
        except ImportError:
            pass

    _stock_cache = None
    _last_errors = []
    async def search_stocks(self, query: str) -> List[dict]:
        """Search stocks by code or name."""
        if DataFetcher._stock_cache is None:
            await self._load_stock_list()
        ql = query.lower()
        return [s for s in DataFetcher._stock_cache if ql in s["code"] or ql in s["name"]][:20]

    async def preload_stocks(self):
        """Preload stock list on startup."""
        await self._load_stock_list()

    async def _load_stock_list(self):
        """Load stock list - try akshare, fall back to COMMON_STOCKS."""
        if self._has_akshare:
            try:
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(None, self._akshare.stock_info_a_code_name)
                stocks = []
                for _, r in df.iterrows():
                    stocks.append({"code": str(r["code"]), "name": str(r["name"])})
                DataFetcher._stock_cache = stocks
                return
            except Exception:
                pass
        DataFetcher._stock_cache = COMMON_STOCKS

    async def get_stock_name(self, code: str) -> str:
        if DataFetcher._stock_cache is None:
            await self._load_stock_list()
        for s in DataFetcher._stock_cache:
            if s["code"] == code:
                return s["name"]
        return code

    def _exchange_prefix(self, code: str) -> str:
        if code.startswith(('6',)):
            return 'sh'
        elif code.startswith(('0', '3')):
            return 'sz'
        elif code.startswith(('4', '8')):
            return 'bj'
        return ''

    async def get_stock_hist(self, code: str, start: Optional[str] = None,
                              end: Optional[str] = None, period: str = "daily") -> pd.DataFrame:
        cache_key = f"{code}_{period}_{start or ''}_{end or ''}"
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached
        prefix = self._exchange_prefix(code)
        sources = []
        if self._has_akshare:
            sources.append(("em", lambda: self._fetch_em(code, start or "20240101", end or datetime.now().strftime("%Y%m%d"), period)))
            if prefix:
                sources.append(("tx", lambda: self._fetch_tx(prefix + code, start or "20240101", end or datetime.now().strftime("%Y%m%d"), period)))
                sources.append(("sina", lambda: self._fetch_sina(prefix + code, start or "20240101", end or datetime.now().strftime("%Y%m%d"), period)))
        for _name, _fn in sources:
            try:
                df = await _fn()
                if df is not None and not df.empty:
                    df = self._standardize_df(df, period)
                    self._write_cache(cache_key, df)
                    return df
            except Exception as e:
                DataFetcher._last_errors.append(f"{_name}: {type(e).__name__}: {str(e)[:100]}")
                continue
        return pd.DataFrame()

    async def _fetch_em(self, code, start, end, period):
        if period == "daily":
            return self._akshare.stock_zh_a_hist(symbol=code, period="daily",
                start_date=start, end_date=end, adjust="qfq")
        return self._akshare.stock_zh_a_hist_min_em(symbol=code, period="60",
            start_date=start, end_date=end)

    async def _fetch_tx(self, code, start, end, period):
        if period == "daily":
            return self._akshare.stock_zh_a_hist_tx(symbol=code, start_date=start, end_date=end)
        return self._akshare.stock_zh_a_hist_min_em(symbol=code[2:], period="60",
            start_date=start, end_date=end)

    async def _fetch_sina(self, code, start, end, period):
        if period == "daily":
            return self._akshare.stock_zh_a_daily(symbol=code, start_date=start, end_date=end, adjust="qfq")
        return pd.DataFrame()

    def _standardize_df(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        col_map = {}
        for src, dst in [("日期", "date"), ("时间", "date"), ("开盘", "open"), ("收盘", "close"),
                         ("最高", "high"), ("最低", "low"), ("成交量", "volume"), ("成交额", "amount")]:
            if src in df.columns: col_map[src] = dst
        needed = {"date", "open", "close", "high", "low", "volume"}
        if not needed.issubset(set(df.columns)) and col_map:
            df = df.rename(columns=col_map)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d" if period == "daily" else "%Y-%m-%d %H:%M")
        for c in ["open", "close", "high", "low"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        return df.sort_values("date").reset_index(drop=True)

    def _read_cache(self, key: str):
        path = os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".pkl")
        if os.path.exists(path):
            if datetime.now().timestamp() - os.path.getmtime(path) < 6 * 3600:
                try: return pd.read_pickle(path)
                except: pass
        return None

    def _write_cache(self, key: str, df: pd.DataFrame):
        path = os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".pkl")
        try: df.to_pickle(path)
        except: pass