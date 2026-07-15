"""
Generate access token for room TV.
"""

import datetime
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api import docs
from src.api.dependencies import AdminDep
from src.exceptions import NotEnoughPermissionsException, UserWithoutSessionException
from src.modules.tokens.repository import TokenRepository

router = APIRouter(tags=["Rooms"])
docs.TAGS_INFO.append({"description": __doc__, "name": str(router.tags[0])})


class DeviceFlowContainer(BaseModel):
    at: datetime.datetime
    secret_string: str
    room_id: str | None
    token: str | None


device_flows: dict[str, DeviceFlowContainer] = {}


class StartDeviceFlowResponse(BaseModel):
    code: str
    secret_string: str


@router.post(
    "/rooms/start-device-flow",
    responses={200: {"description": "Code and secret string"}},
)
async def start_device_flow() -> StartDeviceFlowResponse:
    code = secrets.token_hex(3).upper()
    secret_string = secrets.token_hex(16)
    device_flows[code] = DeviceFlowContainer(
        at=datetime.datetime.now(datetime.UTC), secret_string=secret_string, room_id=None, token=None
    )

    # Delete old flows
    now = datetime.datetime.now(datetime.UTC)
    to_delete: set[str] = set()
    for code, device_flow in device_flows.items():
        if device_flow.at < (now - datetime.timedelta(hours=1)):
            to_delete.add(code)
    for code in to_delete:
        del device_flows[code]

    return StartDeviceFlowResponse(code=code, secret_string=secret_string)


@router.post(
    "/rooms/approve-device-flow",
    responses={
        200: {"description": "Approved"},
        **UserWithoutSessionException.responses,
        **NotEnoughPermissionsException.responses,
    },
)
async def approve_device_flow(
    code: str,
    room_id: str,
    _user: AdminDep,
) -> DeviceFlowContainer:
    if code not in device_flows:
        raise HTTPException(status_code=404, detail="Device flow code not found")

    token = TokenRepository.create_room_tv_token(room_id)
    device_flows[code].room_id = room_id
    device_flows[code].token = token
    return device_flows[code]


@router.post(
    "/rooms/device-flow-token",
    responses={
        200: {"description": "Token"},
        403: {"description": "Incorrect secret string"},
        404: {"description": "Device flow code not found"},
    },
)
async def get_device_flow_token(
    code: str,
    secret_string: str,
) -> DeviceFlowContainer | None:
    if code not in device_flows:
        raise HTTPException(status_code=404, detail="Device flow code not found")

    if device_flows[code].secret_string != secret_string:
        raise HTTPException(status_code=403, detail="Incorrect secret string")

    if device_flows[code].token is None:
        return None

    return device_flows.pop(code)
