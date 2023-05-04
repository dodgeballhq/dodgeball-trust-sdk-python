import pytest
import json
import asyncio
import aiohttp
import requests
import aiohttp_cors
from aiohttp import web
from tests.simple_env import SimpleEnv
from dodgeball.interfaces.api_types import DodgeballEvent
from dodgeball.api.dodgeball import Dodgeball
from dodgeball.api.dodgeball_config import DodgeballConfig


routes = web.RouteTableDef()
print("\nroutes = {}".format(routes))

@routes.post("/checkpoint")
async def post_verification_ticket(request: web.Request) -> web.Response:
    try:
        data = await request.json()

        base_url = SimpleEnv.get_value("BASE_URL")
        secret_key = SimpleEnv.get_value("PRIVATE_API_KEY")

        db_agent = Dodgeball(
            secret_key,
            DodgeballConfig(base_url))


        db_event = DodgeballEvent(
            type=data["checkpointName"],
            ip ="76.90.54.224",
            data=data["payload"]
        )

        checkpoint_response = await db_agent.checkpoint(
            db_event,
            data["sourceToken"],
            data["sessionId"],
            data["userId"],
            data.get("verificationId", None))

        verification_dict = checkpoint_response.verification.dict()
        if db_agent.is_allowed(checkpoint_response):
            return web.json_response({
                "verification": verification_dict},
            status=200)
        elif db_agent.is_running(checkpoint_response):
            # If the outcome is pending, send the verification to the frontend to do additional checks (such as MFA, KYC)
            return web.json_response({
                "verification": verification_dict},
                status=202)
        elif db_agent.is_denied(checkpoint_response):
            # If the request is denied, you can return the verification to the frontend to display a reason message
            return web.json_response({
                "verification": verification_dict},
                status=403)
        else:
            # If the checkpoint failed, decide how you would like to proceed. You can return the error, choose to proceed, retry, or reject the request.
            return web.json_response({
                "message": checkpoint_response.errors},
                status=500)
    except Exception as exc:
        console.log("Error", exc)
        return web.json_response({
            "message": str(exc)
        }, status=501)

def init_app() -> web.Application:
    app = web.Application()
    app.router.add_route('POST', '/checkpoint', post_verification_ticket)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

    return app


if __name__ == '__main__':
    app = init_app()
    web.run_app(app, port=3020)