import asyncio
from time import sleep
from typing import Optional

from dodgeball.interfaces.api_types import (
    CheckpointRequest,
    CheckpointResponseOptions,
    DodgeballCheckpointResponse,
    DodgeballError,
    DodgeballEvent,
    DodgeballResponse,
    DodgeballVerification
)

from .dodgeball_config import DodgeballConfig
from ..utils.query_utils import (
    HttpQuery,
    not_null_or_value,
    nullable_boolean_matches,
    string_null_or_empty
)

from ..utils.logging import DodgeballLogger


class DodgeballApiVersion:
    V1 = "v1"


class VerificationStatus:

    # In Process on the server
    PENDING = "PENDING";

    # Waiting on some action, for example MFA
    BLOCKED = "BLOCKED";

    # Workflow evaluated successfully
    COMPLETE = "COMPLETE";

    # Workflow execution failure
    FAILED = "FAILED"


class VerificationOutcome:
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING = "PENDING"
    ERROR = "ERROR"


class Dodgeball:
    def __init__(self, secret_key: str, config: DodgeballConfig = None):
        self.secretKey = secret_key
        self.config = config

    BASE_CHECKPOINT_TIMEOUT_MS = 100
    MAX_TIMEOUT = 10000
    MAX_RETRY_COUNT = 3
    BASE_URL = "https://api.dodgeballhq.com"

    async def post_event(
            self,
            source_token: Optional[str],
            session_id: str,
            user_id: Optional[str],
            dodgeballEvent: DodgeballEvent) -> asyncio.Future[DodgeballResponse]:
        try:
            base_url = self.BASE_URL
            if self.config and not string_null_or_empty(self.config.apiUrl):
                base_url = self.config.apiUrl


            http_query = HttpQuery(
                base_url,
                "/v1/track/").set_dodgeball_headers(
                self.secretKey,
                session_id,
                source_token,
                user_id).set_body(
                dodgeballEvent)

            response = await http_query.post_dodgeball()
            return response

        except Exception as exc:
            DodgeballLogger.error("Could not POST Event", exc_info=exc)

            return DodgeballResponse(
                success = False,
                errors = [DodgeballError(message = exc.message)])

    async def get_checkpoint(
            self,
            source_token: Optional[str],
            session_id: str,
            user_id: Optional[str],
            use_verification_id: str) -> asyncio.Future[DodgeballResponse]:
        try:
            if string_null_or_empty(use_verification_id):
                raise Exception("Must specify a non-empty Verification ID")

            base_url = self.BASE_URL
            if self.config and not string_null_or_empty(self.config.apiUrl):
                base_url = self.config.apiUrl

            method_url = "/v1/verification/{verification_id}".format(
                verification_id = use_verification_id
            )


            http_query = HttpQuery(
                base_url,
                method_url,
            ).set_dodgeball_headers(
                self.secretKey,
                session_id,
                source_token,
                user_id,
                use_verification_id)

            response = await http_query.get_dodgeball_checkpoint()
            return response

        except Exception as exc:
            DodgeballLogger.error("Could not GET Checkpoint", exc_info=exc)

            return DodgeballResponse(
                success = False,
                errors = [DodgeballError(message = exc.message)])

    async def checkpoint(
        self,
        dodgeball_event: DodgeballEvent,
        source_token: Optional[str],
        session_id: str,
        user_id: Optional[str] = None,
        use_verification_id: Optional[str] = None,
        checkpoint_response_options: Optional[CheckpointResponseOptions] = None)->asyncio.Future[DodgeballCheckpointResponse]:

        if not string_null_or_empty(use_verification_id):
            to_return = await self.get_checkpoint(
                source_token,
                session_id,
                user_id,
                use_verification_id
            )

            return to_return;

        if not dodgeball_event:
            raise TypeError("Must provide a non-null dodgeball_event")

        if string_null_or_empty(dodgeball_event.type):
            raise TypeError("Must provide a non-null Dodgeball Event Type")

        if string_null_or_empty(session_id):
            raise TypeError("Must provide a non-null Session ID")

        if dodgeball_event.eventTime:
            # This must be set on the server side
            dodgeball_event.eventTime = None

        try:
            if not checkpoint_response_options:
                checkpoint_response_options = CheckpointResponseOptions(
                    sync = True,
                    timeout = -1)

            base_url = self.BASE_URL
            if self.config and not string_null_or_empty(self.config.apiUrl):
                base_url = self.config.apiUrl

            timeout = checkpoint_response_options.timeout
            if not timeout:
                timeout = -1

            trivial_timeout = timeout <= 0;
            large_timeout = timeout > 5 * self.BASE_CHECKPOINT_TIMEOUT_MS;
            must_poll = trivial_timeout or large_timeout
            active_timeout = self.BASE_CHECKPOINT_TIMEOUT_MS if must_poll else \
                self.BASE_CHECKPOINT_TIMEOUT_MS

            maximal_timeout = self.MAX_TIMEOUT
            max_duration = self.BASE_CHECKPOINT_TIMEOUT_MS
            if checkpoint_response_options and \
                    checkpoint_response_options.timeout is not None and \
                    checkpoint_response_options.timeout > 0:
                max_duration = checkpoint_response_options.timeout


            sync_response = checkpoint_response_options.sync
            if sync_response is None:
                sync_response = True

            internal_options = CheckpointResponseOptions(
                sync = sync_response,
                timeout = active_timeout,
                webhook = checkpoint_response_options.webhook)

            response: Optional[DodgeballCheckpointResponse] = None
            num_repeats = 0
            num_failures = 0
            is_disabled = self.config and nullable_boolean_matches(self.config.isEnabled, False)
            is_timeout = False

            if is_disabled:
                return DodgeballCheckpointResponse(
                    success = True,
                    errors = [],
                    version = DodgeballApiVersion.V1,
                    verification = DodgeballVerification(
                        id = "DODGEBALL_IS_DISABLED",
                        status = VerificationStatus.COMPLETE,
                        outcome = VerificationOutcome.APPROVED))

            body = CheckpointRequest(
                event=dodgeball_event,
                options=internal_options)

            httpQuery = HttpQuery(
                base_url,
                "/v1/checkpoint"
            ).set_body(body
            ).set_dodgeball_headers(
                self.secretKey,
                session_id,
                source_token,
                user_id
            )

            response = await httpQuery.post_dodgeball_checkpoint()

            if response is None or response.verification is None:
                return DodgeballCheckpointResponse(
                    success = False,
                    errors = [
                        DodgeballError("UNKNOWN", "Unknown evaluation error")
                    ])

            verification = response.verification
            status = verification.status
            outcome = verification.outcome
            verification_id = verification.id
            is_resolved = status != VerificationStatus.PENDING;

            while not is_resolved and num_failures < self.MAX_RETRY_COUNT and \
                not is_timeout:

                sleep(activeTimeout/1000)
                if activeTimeout < maximal_timeout:
                    activeTimeout = 2*active_timeout

                response = await self.get_checkpoint(
                    source_token,
                    session_id,
                    user_id,
                    verification_id)

                num_repeats += 1

                if response and response.success and response.verification:
                    status = response.verification.status
                    if string_null_or_empty(status):
                        num_failures += 1
                    else:
                        is_resolved = status != VerificationStatus.PENDING

                if not trivial_timeout and active_timeout*num_repeats > max_duration:
                    is_timeout = True

            if is_resolved:
                return response

            if is_timeout:
                return DodgeballCheckpointResponse(
                    success = False,
                    version = DodgeballApiVersion.V1,
                    errors = [DodgeballError(
                        category="UNAVAILABLE",
                        message = "Service Unavailable: Maximum retry count exceeded")],
                    isTimeout = True)

            if response and response.success:
                return response
            else:
                return DodgeballCheckpointResponse(
                    success = False,
                    status = VerificationStatus.FAILED,
                    outcome = VerificationOutcome.ERROR,
                    version = DodgeballApiVersion.V1,
                    errors = [DodgeballError(
                        category="UNKNOWN",
                        message = "Checkpoint evaluation failed")])
        except Exception as exc:
            return DodgeballCheckpointResponse(
                success=False,
                status=VerificationStatus.FAILED,
                outcome=VerificationOutcome.ERROR,
                version=DodgeballApiVersion.V1,
                errors=[DodgeballError(message=exc.message)])

    def is_running(self, checkpoint_response:DodgeballCheckpointResponse)->bool:
        if not checkpoint_response or not checkpoint_response.verification:
            return False

        if not checkpoint_response.success:
            return False

        status = not_null_or_value(checkpoint_response.verification.status, "")
        if status == VerificationStatus.PENDING or status == VerificationStatus.BLOCKED:
            return True

        return False

    def is_allowed(self, checkpoint_response: DodgeballCheckpointResponse)->bool:
        if not checkpoint_response or not checkpoint_response.verification:
            return False

        if not checkpoint_response.success:
            return False

        status = not_null_or_value(checkpoint_response.verification.status, "")
        outcome = not_null_or_value(checkpoint_response.verification.outcome, "")

        return status == VerificationStatus.COMPLETE and outcome ==  VerificationOutcome.APPROVED;

    def is_denied(self, checkpoint_response:DodgeballCheckpointResponse)->bool:
        if not checkpoint_response or not checkpoint_response.verification:
            return False

        if not checkpoint_response.success:
            return False

        outcome = not_null_or_value(checkpoint_response.verification.outcome, "")
        return outcome == VerificationOutcome.DENIED;

    def is_undecided(self, checkpoint_response:DodgeballCheckpointResponse)->bool:
        if not checkpoint_response or not checkpoint_response.verification:
            return False

        if not checkpoint_response.success:
            return False

        status = not_null_or_value(checkpoint_response.verification.outcome, "")
        outcome = not_null_or_value(checkpoint_response.verification.outcome, "")

        return status == VerificationStatus.COMPLETE and outcome == VerificationOutcome.PENDING


    def has_error(self, checkpoint_response:DodgeballCheckpointResponse)->bool:
        if not checkpoint_response or not checkpoint_response.verification:
            return False

        if not checkpoint_response.success:
            return True

        status = not_null_or_value(checkpoint_response.verification.outcome, "")
        outcome = not_null_or_value(checkpoint_response.verification.outcome, "")

        return status == VerificationStatus.FAILED and outcome == VerificationOutcome.ERROR

    def is_timeout(self, checkpoint_response:DodgeballCheckpointResponse)->bool:
        if not checkpoint_response or not checkpoint_response.verification:
            return False

        return not checkpoint_response.success and \
            nullable_boolean_matches(checkpoint_response.isTimeout, True)



