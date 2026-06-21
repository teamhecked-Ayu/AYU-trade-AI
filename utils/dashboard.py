from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from datetime import datetime
import random

class AYUDashboard:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self._setup_layout()

    def _setup_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="signals", ratio=1),
            Layout(name="portfolio", ratio=1)
        )

    def generate_header(self):
        title = Text("AYU-trade-AI | Self-Learning Multi-Strategy Oracle", style="bold white on blue", justify="center")
        return Panel(title)

    def generate_signals_table(self):
        table = Table(title="Live Consensus Signals", expand=True)
        table.add_column("Asset", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Confidence", justify="right")
        table.add_column("Action", style="bold")

        assets = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        for asset in assets:
            score = random.uniform(-1, 1)
            conf = random.uniform(0.6, 0.99)
            action = "BUY" if score > 0.5 else "SELL" if score < -0.5 else "HOLD"
            color = "green" if action == "BUY" else "red" if action == "SELL" else "yellow"
            table.add_row(asset, f"{score:.4f}", f"{conf:.2%}", Text(action, style=color))
        
        return Panel(table, title="Signal Fusion Layer")

    def generate_portfolio_panel(self):
        table = Table(title="Execution Monitor", expand=True)
        table.add_column("Exchange", style="magenta")
        table.add_column("Balance", justify="right")
        table.add_column("Daily PnL", justify="right")

        table.add_row("Binance", "$12,450.00", Text("+2.4%", style="green"))
        table.add_row("Kraken", "$5,200.00", Text("-0.5%", style="red"))
        table.add_row("Kite", "₹4,50,000", Text("+1.2%", style="green"))

        return Panel(table, title="Risk & Portfolio Layer")

    def generate_footer(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = Text(f"Status: OPERATIONAL | Mode: PAPER_TRADE | Time: {now}", style="italic dim")
        return Panel(status)

    def update_display(self):
        self.layout["header"].update(self.generate_header())
        self.layout["signals"].update(self.generate_signals_table())
        self.layout["portfolio"].update(self.generate_portfolio_panel())
        self.layout["footer"].update(self.generate_footer())
        return self.layout

    async def run(self):
        with Live(self.update_display(), console=self.console, refresh_per_second=4, screen=True) as live:
            while True:
                live.update(self.update_display())
                await asyncio.sleep(0.5)
