from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.game.models import PlayerPoint


async def save_user_point(client_id: str, question_id: str, round_id: str, session: AsyncSession) -> None:
    player_point = PlayerPoint(client_id=client_id, question_id=question_id, game_round_id=round_id)
    session.add(player_point)
    await session.commit()


async def get_all_points(session: AsyncSession) -> list[PlayerPoint]:
    # TODO(alireza) : for real production ready product we should support pagination
    stmt = select(PlayerPoint)
    all_player_points: list[PlayerPoint] = [item[0] for item in (await session.execute(stmt)).all()]
    return all_player_points
