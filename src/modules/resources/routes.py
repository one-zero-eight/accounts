from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.dependencies import UserIdDep
from src.modules.resources.repository import resource_repository
from src.storages.mongo.models import ScopeSettings, Resource

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/my")
async def get_my_resources(user_id: UserIdDep) -> list[Resource]:
    return await resource_repository.get_user_resources(user_id)


class CreateResource(BaseModel):
    resource_id: str
    scopes: dict[str, ScopeSettings | None] = Field(default_factory=dict)


@router.post("/")
async def create_resource(resource: CreateResource, user_id: UserIdDep) -> Resource:
    created = await resource_repository.create(
        Resource(resource_id=resource.resource_id, scopes=resource.scopes, owner_id=user_id)
    )
    return created
