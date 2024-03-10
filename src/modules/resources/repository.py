from beanie import PydanticObjectId

from src.modules.resources.schemas import CreateResource
from src.storages.mongo.models import Resource


# noinspection PyMethodMayBeStatic
class ResourceRepository:
    async def create(self, obj: CreateResource) -> Resource:
        resource = Resource.model_validate(obj, from_attributes=True)
        await resource.insert()
        return resource

    async def get_user_resources(self, user_id: PydanticObjectId) -> list[Resource]:
        resources = await Resource.find_many(Resource.owner_id == user_id).to_list()
        return resources

    async def read(self, resource_id: str) -> Resource | None:
        resource = await Resource.find_one(Resource.resource_id == resource_id)
        return resource


resource_repository: ResourceRepository = ResourceRepository()
