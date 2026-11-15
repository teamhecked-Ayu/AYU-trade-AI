from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from core.paper_portfolio import PaperPortfolio, Position


class SQLitePortfolioStore:
    """Atomic shared storage for the application's single simulated portfolio."""

    def __init__(self, path: str = "data/paper_portfolio.db"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS portfolio_state "
                "(id INTEGER PRIMARY KEY CHECK (id=1), cash REAL NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS positions "
                "(symbol TEXT PRIMARY KEY, quantity REAL NOT NULL, average_price REAL NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS trades "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)"
            )

    @staticmethod
    def _load_from_connection(
        connection: sqlite3.Connection,
        *,
        initial_cash: float,
        fee_rate: float,
    ) -> PaperPortfolio:
        row = connection.execute(
            "SELECT cash FROM portfolio_state WHERE id=1"
        ).fetchone()
        portfolio = PaperPortfolio(
            cash=row[0] if row else initial_cash,
            fee_rate=fee_rate,
        )
        for symbol, quantity, average_price in connection.execute(
            "SELECT symbol, quantity, average_price FROM positions"
        ):
            portfolio.positions[symbol] = Position(quantity, average_price)
        portfolio.trades = [
            json.loads(row[0])
            for row in connection.execute("SELECT payload FROM trades ORDER BY id")
        ]
        return portfolio

    @staticmethod
    def _save_to_connection(
        connection: sqlite3.Connection,
        portfolio: PaperPortfolio,
    ) -> None:
        connection.execute(
            "INSERT INTO portfolio_state(id, cash) VALUES(1, ?) "
            "ON CONFLICT(id) DO UPDATE SET cash=excluded.cash",
            (portfolio.cash,),
        )
        connection.execute("DELETE FROM positions")
        connection.executemany(
            "INSERT INTO positions(symbol, quantity, average_price) VALUES (?, ?, ?)",
            [
                (symbol, position.quantity, position.average_price)
                for symbol, position in portfolio.positions.items()
            ],
        )
        connection.execute("DELETE FROM trades")
        connection.executemany(
            "INSERT INTO trades(payload) VALUES (?)",
            [(json.dumps(trade),) for trade in portfolio.trades],
        )

    def load(
        self,
        initial_cash: float = 10_000.0,
        fee_rate: float = 0.001,
    ) -> PaperPortfolio:
        with self._connect() as connection:
            return self._load_from_connection(
                connection,
                initial_cash=initial_cash,
                fee_rate=fee_rate,
            )

    def save(self, portfolio: PaperPortfolio) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._save_to_connection(connection, portfolio)

    def execute(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        *,
        initial_cash: float = 10_000.0,
        fee_rate: float = 0.001,
    ) -> dict:
        """Apply one simulated order in a single SQLite write transaction."""
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            portfolio = self._load_from_connection(
                connection,
                initial_cash=initial_cash,
                fee_rate=fee_rate,
            )
            trade = portfolio.execute(symbol, side, quantity, price)
            self._save_to_connection(connection, portfolio)
            return trade
