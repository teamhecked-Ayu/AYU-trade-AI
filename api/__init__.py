"""Combined AYUAI and paper-trading API package.

The former root-level api.py has moved to paper_api.py so Python can import
this package and its AYUAI submodule as api.main.
"""
from .main import app

from paper_api import app as paper_trading_app

# Keep the existing paper portfolio endpoints on the combined application.
# /health is defined by api.main and is intentionally not duplicated.
_PAPER_ENDPOINTS = {"/ready", "/metrics", "/portfolio", "/paper/orders"}
_registered = {getattr(route, "path", None) for route in app.router.routes}
for _route in paper_trading_app.router.routes:
    _path = getattr(_route, "path", None)
    if _path in _PAPER_ENDPOINTS and _path not in _registered:
        app.router.routes.append(_route)
        _registered.add(_path)

app.title = "AYU Trade AI API"
