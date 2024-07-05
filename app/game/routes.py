from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.exceptions import WebSocketException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketState

from app._security import create_signed_token, validate_client_id
from app.db import async_session_annotated_type
from app.game.game_manager import GameManager
from app.game.models import PlayerPoint
from app.game.services import get_all_points

templates = Jinja2Templates(directory="templates")


routes = APIRouter(tags=["game"])


@routes.get("/")
async def home_page(request: Request) -> HTMLResponse:
    new_signed_client_id, client_id = await create_signed_token()
    current_question = GameManager.get_current_question()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"client_id": client_id, "token": new_signed_client_id, **current_question},
    )


@routes.get("/game/points")
async def all_points(async_session: async_session_annotated_type) -> list[PlayerPoint]:
    return await get_all_points(async_session)


@routes.get("/game/online-players")
async def online_players() -> list[str]:
    return [str(key) for key in GameManager.online_players.keys()]


@routes.websocket("/ws")
async def join_game(websocket: WebSocket, token: Annotated[str | None, Query()]) -> None:
    try:
        client_id = validate_client_id(token)
        await GameManager.add_player(client_id, websocket)
    except WebSocketException:
        if websocket.client_state == WebSocketState.DISCONNECTED:
            await websocket.close()
