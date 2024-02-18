from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from src.mongo_object_id import PyObjectId


class ScopeSettings(BaseModel):
    client_id: str


class Resource(BaseModel):
    resource_id: str
    scopes: dict[str, ScopeSettings | None] = Field(default_factory=dict)
    owner_id: PyObjectId


class MongoResource(BaseModel):
    id: PyObjectId = Field(..., alias="_id")


class ResourceRepository:
    def __init__(self, database: AsyncIOMotorDatabase, *, collection: str = "resources") -> None:
        self.__database = database
        self.__collection = database[collection]

    async def __post_init__(self):
        # unique constraint
        await self.__collection.create_index("resource_id", unique=True)

    async def create(self, obj: Resource) -> Resource:
        obj_dict = obj.model_dump()
        result = await self.__collection.insert_one(obj_dict)
        return Resource.model_validate(await self.__collection.find_one({"_id": result.inserted_id}))

    async def get_user_resources(self, user_id: PyObjectId) -> list[Resource]:
        return [Resource.model_validate(x) async for x in self.__collection.find({"owner_id": user_id})]

    async def read(self, resource_id: str) -> Resource | None:
        resource_dict = await self.__collection.find_one({"resource_id": resource_id})
        if resource_dict is not None:
            return Resource.model_validate(resource_dict)
