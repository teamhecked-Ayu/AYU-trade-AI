from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from core.paper_portfolio import PaperPortfolio, Position


class SQLitePortfolioStore:
    def __init__(self, path: str = "data/paper_portfolio.db"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS portfolio_state (id INTEGER PRIMARY KEY CHECK (id=1), cash REAL NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS positions (symbol TEXT PRIMARY KEY, quantity REAL NOT NULL, average_price REAL NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)")

    def load(self, initial_cash: float = 10000.0, fee_rate: float = 0.001) -> PaperPortfolio:
        with self._connect() as conn:
            row = conn.execute("SELECT cash FROM portfolio_state WHERE id=1").fetchone()
            portfolio = PaperPortfolio(cash=row[0] if row else initial_cash, fee_rate=fee_rate)
            for symbol, quantity, average_price in conn.execute("SELECT symbol, quantity, average_price FROM positions"):
                portfolio.positions[symbol] = Position(quantity, average_price)
            portfolio.trades = [json.loads(row[0]) for row in conn.execute("SELECT payload FROM trades ORDER BY id")]
            return portfolio

    def save(self, portfolio: PaperPortfolio) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO portfolio_state(id, cash) VALUES(1, ?) ON CONFLICT(id) DO UPDATE SET cash=excluded.cash", (portfolio.cash,))
            conn.execute("DELETE FROM positions")
            conn.executemany("INSERT INTO positions(symbol, quantity, average_price) VALUES (?, ?, ?)", [(s, p.quantity, p.average_price) for s, p in portfolio.positions.items()])
            conn.execute("DELETE FROM trades")
            conn.executemany("INSERT INTO trades(payload) VALUES (?)", [(json.dumps(t),) for t in portfolio.trades])
