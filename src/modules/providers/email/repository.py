import datetime
import random
from enum import StrEnum

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from pymongo import ReturnDocument

from src.mongo_object_id import PyObjectId


def _generate_auth_code() -> str:
    # return random 6-digit code
    return str(random.randint(100_000, 999_999))


class EmailFlow(BaseModel):
    email: str
    is_sent: bool = False
    sent_at: datetime.datetime | None = None
    is_verified: bool = False
    verified_at: datetime.datetime | None = None
    verification_code: str | None = None
    verification_code_expires_at: datetime.datetime | None = None
    user_id: PyObjectId | None = None
    client_id: str | None = None


class MongoEmailFlow(EmailFlow):
    object_id: PyObjectId


EXPIRATION_TIME = 30  # minutes


class EmailFlowVerificationStatus(StrEnum):
    SUCCESS = "success"
    EXPIRED = "expired"
    INCORRECT = "incorrect"
    NOT_FOUND = "not_found"


class EmailFlowVerificationResult(BaseModel):
    status: EmailFlowVerificationStatus
    email_flow: MongoEmailFlow | None = None


class EmailFlowRepository:
    def __init__(self, database: AsyncIOMotorDatabase, *, collection: str = "emailFlows") -> None:
        self.__database = database
        self.__collection = database[collection]

    async def start_flow(self, email: str, user_id: PyObjectId | None, client_id: str | None) -> MongoEmailFlow:
        verification_code = _generate_auth_code()
        verification_code_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=EXPIRATION_TIME)

        email_flow = dict(
            email=email,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at,
            user_id=user_id,
            client_id=client_id,
        )
        EmailFlow.model_validate(email_flow)
        insert_result = await self.__collection.insert_one(email_flow)
        return MongoEmailFlow.model_validate(await self.__collection.find_one({"_id": insert_result.inserted_id}))

    async def verify_flow(
        self, email_flow_id: PyObjectId, verification_code: str, *, user_id: PyObjectId | None, client_id: str | None
    ) -> EmailFlowVerificationResult:
        email_flow = await self.__collection.find_one({"_id": email_flow_id})
        if email_flow is None:
            return EmailFlowVerificationResult(status=EmailFlowVerificationStatus.NOT_FOUND)
        if email_flow["verification_code_expires_at"] < datetime.datetime.utcnow():
            # delete flow
            await self.__collection.delete_one({"_id": email_flow["_id"]})
            return EmailFlowVerificationResult(status=EmailFlowVerificationStatus.EXPIRED)
        if (
            email_flow["verification_code"] != verification_code
            or email_flow["client_id"] != client_id
            or email_flow["user_id"] != user_id
        ):
            return EmailFlowVerificationResult(status=EmailFlowVerificationStatus.INCORRECT)
        # clear all other verification codes
        await self.__collection.delete_many(
            {"email": email_flow["email"], "_id": {"$ne": email_flow["_id"]}, "is_verified": False}
        )

        email_flow = await self.__collection.find_one_and_update(
            {"_id": email_flow["_id"]},
            {"$set": {"is_verified": True, "verification_code": None, "verified_at": datetime.datetime.utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return EmailFlowVerificationResult(
            status=EmailFlowVerificationStatus.SUCCESS, email_flow=MongoEmailFlow.model_validate(email_flow)
        )

    async def set_sent(self, id: PyObjectId) -> None:
        await self.__collection.update_one(
            {"_id": id}, {"$set": {"is_sent": True, "sent_at": datetime.datetime.utcnow()}}
        )
