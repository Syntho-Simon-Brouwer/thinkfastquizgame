from app._app import create_app
from app.game.routes import routes

app = create_app(routers=[routes])
