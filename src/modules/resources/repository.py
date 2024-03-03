from beanie import PydanticObjectId
from src.storages.mongo.models import Resource


# noinspection PyMethodMayBeStatic
class ResourceRepository:
    async def create(self, obj: Resource) -> Resource:
        await obj.save()
        return obj

    async def get_user_resources(self, user_id: PydanticObjectId) -> list[Resource]:
        resources = await Resource.find_many(Resource.owner_id == user_id).to_list()
        return resources

    async def read(self, resource_id: str) -> Resource | None:
        resource = await Resource.find_one(Resource.resource_id == resource_id)
        return resource


resource_repository = ResourceRepository()
