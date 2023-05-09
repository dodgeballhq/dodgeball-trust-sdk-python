from typing import Any, List, Mapping, Optional
from pydantic import BaseModel


class DodgeballError(BaseModel):
    category: Optional[str]
    message: str


class DodgeballResponse(BaseModel):
    success: bool
    errors: List[DodgeballError]


class DodgeballEvent(BaseModel):
    type: str
    ip: str
    data: Mapping[str, Any]
    eventTime: Optional[float]


class CheckpointResponseOptions(BaseModel):
    sync: Optional[bool]
    timeout: Optional[int]
    webhook: Optional[str]


class CheckpointRequest(BaseModel):
    event: DodgeballEvent
    options: Optional[CheckpointResponseOptions]


class VerificationStatus:
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class VerificationOutcome:
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING = "PENDING"
    ERROR = "ERROR"


class VerificationStepData(BaseModel):
    customMessage: Optional[str]


class LibContent(BaseModel):
    url: Optional[str]
    text: Optional[str]


class LibConfig(BaseModel):
    name: str
    url: str
    config: Any
    method: Optional[str]
    content: Optional[LibContent]
    loadTimeout: Optional[int]


class VerificationStep(LibConfig):
    id: str
    verificationStepId: str


class DodgeballVerification(BaseModel):
    id: str
    status: str
    outcome: str
    stepData: Optional[VerificationStepData]
    nextSteps: Optional[List[VerificationStep]]
    error: Optional[DodgeballError]


class DodgeballCheckpointResponse(DodgeballResponse):
    success: bool
    errors: Optional[List[DodgeballError]]
    version: Optional[str]
    verification: Optional[DodgeballVerification]
    isTimeout: Optional[bool]
