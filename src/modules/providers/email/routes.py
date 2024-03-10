__all__ = ["router"]

from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import EmailStr, BaseModel

from src.api.dependencies import UserIdDep
from src.config import settings
from src.modules.clients.dependencies import VerifiedClientIdDep
from src.modules.providers.email.repository import EmailFlowVerificationStatus, email_flow_repository
from src.modules.tokens.repository import TokenRepository
from beanie import PydanticObjectId

router = APIRouter(prefix="/email", tags=["Email"])


class EmailFlowReference(BaseModel):
    email_flow_id: PydanticObjectId


class EmailFlowResult(BaseModel):
    status: EmailFlowVerificationStatus
    email: str | None = None
    email_verification_token: str | None = None


if settings.smtp:

    @router.post("/connect")
    async def start_email_flow(email: Annotated[EmailStr, Body(embed=True)], user_id: UserIdDep) -> EmailFlowReference:
        from src.modules.smtp.repository import smtp_repository

        email_flow = await email_flow_repository.start_flow(email, user_id, None)
        message = smtp_repository.render_verification_message(email_flow.email, email_flow.verification_code)
        smtp_repository.send(message, email_flow.email)
        await email_flow_repository.set_sent(email_flow.id)
        return EmailFlowReference(email_flow_id=email_flow.id)

    @router.post("/validate-code-for-users", response_model=EmailFlowResult)
    async def end_email_flow(
        email_flow_id: Annotated[PydanticObjectId, Body()],
        verification_code: Annotated[str, Body()],
        user_id: UserIdDep,
    ) -> EmailFlowResult:
        return await _validate_code_route(email_flow_id, verification_code, user_id, None)

    @router.post("/validate-code-for-clients", response_model=EmailFlowResult)
    async def end_email_flow_for_clients(
        email_flow_id: Annotated[PydanticObjectId, Body()],
        verification_code: Annotated[str, Body()],
        client_id: VerifiedClientIdDep,
    ) -> EmailFlowResult:
        return await _validate_code_route(email_flow_id, verification_code, None, client_id)

    async def _validate_code_route(
        email_flow_id: PydanticObjectId,
        verification_code: str,
        user_id: PydanticObjectId | None,
        client_id: PydanticObjectId | None,
    ):
        verification_result = await email_flow_repository.verify_flow(
            email_flow_id, verification_code, user_id=user_id, client_id=client_id
        )
        if verification_result.status == EmailFlowVerificationStatus.SUCCESS:
            return EmailFlowResult(
                status=verification_result.status,
                email=verification_result.email_flow.email,
                email_verification_token=TokenRepository.create_email_flow_token(verification_result.email_flow.id),
            )
        else:
            return EmailFlowResult(status=verification_result.status)
