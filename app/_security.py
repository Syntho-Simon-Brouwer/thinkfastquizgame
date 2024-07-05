from uuid import uuid1

import jwt
from fastapi import WebSocketException, status
from jwt.exceptions import InvalidTokenError

from app._settings import settings


def validate_client_id(token: str | None) -> str:
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        client_id: str = payload["client_id"]
    except InvalidTokenError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from None

    return client_id


async def create_signed_token() -> tuple[str, str]:
    token_payload = {"client_id": str(uuid1())}
    encoded_jwt = jwt.encode(token_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt, token_payload["client_id"]
