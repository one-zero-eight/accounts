from fastapi import APIRouter

from src.api.dependencies import UserIdDep
from src.exceptions import ObjectNotFound
from src.modules.resources.repository import resource_repository
from src.storages.mongo.models import Resource

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/my")
async def get_my_resources(user_id: UserIdDep) -> list[Resource]:
    return await resource_repository.get_user_resources(user_id)


@router.get("/{resource_id}")
async def get_resource(resource_id: str) -> Resource:
    resource = await resource_repository.read(resource_id)
    if resource is None:
        raise ObjectNotFound("Resource not found")
    return await resource_repository.read(resource_id)


# @router.post("/")
# async def create_resource(resource: CreateResource, user_id: UserIdDep) -> Resource:
#     if resource.owner_id is not None and resource.owner_id != user_id:
#         raise NotEnoughPermissionsException("You can't create owned by another user")
#     resource.owner_id = user_id
#     created = await resource_repository.create(resource)
#     return created
