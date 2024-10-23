import datetime
import random
from enum import StrEnum

from beanie import PydanticObjectId
from beanie.odm.operators.update.general import Set
from pydantic import BaseModel

from src.storages.mongo.models import EmailFlow


def _generate_auth_code() -> str:
    # return random 6-digit code
    return str(random.randint(100_000, 999_999))


EXPIRATION_TIME = 30  # minutes


class EmailFlowVerificationStatus(StrEnum):
    SUCCESS = "success"
    EXPIRED = "expired"
    INCORRECT = "incorrect"
    NOT_FOUND = "not_found"


class EmailFlowVerificationResult(BaseModel):
    status: EmailFlowVerificationStatus
    email_flow: EmailFlow | None = None


# noinspection PyMethodMayBeStatic
class EmailFlowRepository:
    async def start_flow(self, email: str, user_id: PydanticObjectId | None, client_id: str | None) -> EmailFlow:
        verification_code = _generate_auth_code()
        verification_code_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=EXPIRATION_TIME)

        email_flow = EmailFlow(
            email=email,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at,
            user_id=user_id,
            client_id=client_id,
        )
        await email_flow.save()
        return email_flow

    async def verify_flow(
        self,
        email_flow_id: PydanticObjectId,
        verification_code: str,
        *,
        user_id: PydanticObjectId | None,
        client_id: str | None,
    ) -> EmailFlowVerificationResult:
        email_flow = await EmailFlow.find_one(EmailFlow.id == email_flow_id)
        if email_flow is None:
            return EmailFlowVerificationResult(status=EmailFlowVerificationStatus.NOT_FOUND)
        if email_flow.verification_code_expires_at < datetime.datetime.utcnow():
            # delete flow
            await email_flow.delete()
            return EmailFlowVerificationResult(status=EmailFlowVerificationStatus.EXPIRED)
        if (
            email_flow.verification_code != verification_code
            or email_flow.client_id != client_id
            or email_flow.user_id != user_id
        ):
            return EmailFlowVerificationResult(status=EmailFlowVerificationStatus.INCORRECT)
        # clear all other verification codes
        await EmailFlow.find_many(
            EmailFlow.email == email_flow.email,
            EmailFlow.id != email_flow.id,
            EmailFlow.is_verified is False,
        ).delete()

        # update
        await email_flow.update(Set({EmailFlow.verified_at: datetime.datetime.utcnow(), EmailFlow.is_verified: True}))

        return EmailFlowVerificationResult(status=EmailFlowVerificationStatus.SUCCESS, email_flow=email_flow)

    async def set_sent(self, id: PydanticObjectId) -> None:
        await EmailFlow.find_one(EmailFlow.id == id).update(
            Set({EmailFlow.is_sent: True, EmailFlow.sent_at: datetime.datetime.utcnow()})
        )


email_flow_repository: EmailFlowRepository = EmailFlowRepository()
