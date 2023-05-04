import asyncio
import json

import aiohttp
from typing import Any, Awaitable, Callable, Mapping, Optional
from urllib.parse import urljoin
from pydantic import BaseModel

from ..interfaces.api_types import DodgeballError, DodgeballResponse, DodgeballCheckpointResponse
from ..utils.logging import DodgeballLogger


def string_null_or_empty(val: Optional[str])-> bool:
    if not val or len(val) == 0:
        return True
    else:
        return False


def nullable_boolean_matches(val: Optional[bool], target: bool)-> bool:
    if val is None:
        return False

    return val == target


def not_null_or_value(val: Any, default: Any):
    if val is None:
        return default

    return val


class HttpQuery:

    def __init__(self, base_url: str, call_path: str):
        self.headers = {}
        self.base_url = base_url
        self.call_path = call_path
        self.body: BaseModel = None

    def set_dodgeball_headers(
            self,
            secret_key: str,
            session_id: str,
            source_token: Optional[str] = None,
            user_id: Optional[str] = None,
            use_verification_id: Optional[str] = None):

        if string_null_or_empty(secret_key):
            raise Exception("Must specify a non-empty API Key")

        if string_null_or_empty(session_id):
            raise Exception("Must specify a non-empty Session ID")

        if not self.headers:
            self.headers = {}

        self.headers["dodgeball-session-id"] = session_id
        self.headers["dodgeball-secret-key"] = secret_key

        if not string_null_or_empty(source_token):
            self.headers["dodgeball-source-token"] = source_token

        if not string_null_or_empty(user_id):
            self.headers["dodgeball-customer-id"] = user_id

        if not string_null_or_empty(use_verification_id):
            self.headers["dodgeball-verification-id"] = use_verification_id;

        return self

    def set_headers(self, headers:Mapping[str, str]):
        self.headers = headers
        return self

    def set_body(self, body: BaseModel):
        self.body = body
        return self

    async def try_post_dodgeball(self, url):
        try:
            DodgeballLogger.info("About to invoke logger")

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(url, json=self.transform_event_body(self.body)) as response:
                    response_dict = await response.json()
                    to_return = DodgeballResponse.parse_obj(response_dict)
                    success = True

                    return {
                        "success": True,
                        "response": to_return
                    }

        except Exception as exc:
            DodgeballLogger.error("Possibly empty error", exc_info=exc)
            return {"success": False, "response": None, "error": exc}

    async def post_dodgeball(self) -> asyncio.Future[DodgeballResponse]:
        if not self.body:
            raise Exception("Must provide non-null base url")

        urlToCall = self.base_url
        if not string_null_or_empty(self.call_path):
            urlToCall = urljoin(urlToCall, self.call_path)

        success: bool = False
        try_num = 0
        error_message = "Unknown Error"
        while try_num < 3 and not success:
            response_block = await self.try_post_dodgeball(urlToCall)
            if response_block["success"]:
                return response_block["response"]
            else:
                try_num += 1
                exc = response_block.get("error", None)
                if exc:
                    error_message = str(exc)
                    DodgeballLogger.error("Possibly temporary error", exc)

        return DodgeballResponse(
            success=False,
            errors = [DodgeballError(message = error_message)]
        )

    def transform_event_body(self, body: BaseModel):
        if body is None:
            return None

        body_json = body.json(exclude_none=True, exclude_unset=True)
        return json.loads(body_json)


    async def try_post_dodgeball_checkpoint(self, url):
        try:
            DodgeballLogger.info("About to try posting a checkpoint")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(url, json=self.transform_event_body(self.body)) as response:
                    response_dict = await response.json()
                    to_return = DodgeballCheckpointResponse.parse_obj(response_dict)

                    return {
                        "success": True,
                        "response": to_return
                    }

        except Exception as exc:
            DodgeballLogger.error("Possibly empty error", exc_info=exc)
            return {"success": False, "response": None, "error": exc}


    async def post_dodgeball_checkpoint(self) -> asyncio.Future[DodgeballCheckpointResponse]:
        if self.body is None:
            raise Exception("Must provide non-null base url")

        urlToCall = self.base_url
        if not string_null_or_empty(self.call_path):
            urlToCall = urljoin(urlToCall, self.call_path)

        error_message = "Uknown Error"
        try_num = 0
        while try_num < 3:
            response_body = await self.try_post_dodgeball_checkpoint(
                urlToCall)

            if response_body["success"]:
                return response_body["response"]
            else:
                exc = response_body.get("error", None)
                DodgeballLogger.error("Possibly empty error", exc)
                try_num += 1

        return DodgeballResponse(
            success=False,
            errors=[DodgeballError(message=error_message)])

    async def get_dodgeball_checkpoint(self) -> asyncio.Future[DodgeballCheckpointResponse]:
        urlToCall = self.base_url
        if not string_null_or_empty(self.call_path):
            urlToCall = urljoin(urlToCall, self.call_path)

        success: bool = False
        try_num = 0
        while try_num < 3 and not success:
            try:
                DodgeballLogger.info("About to invoke logger")

                async with aiohttp.ClientSession(headers = self.headers) as session:
                    async with session.get(urlToCall) as response:
                        response_dict = await response.json()
                        to_return = DodgeballCheckpointResponse.parse_obj(
                            response_dict
                        )

                        success = True
                        return to_return

            except Exception:
                DodgeballLogger.error("Possibly empty error", exc_info = True)
                try_num += 1

        raise Exception("Could not evaluate")

