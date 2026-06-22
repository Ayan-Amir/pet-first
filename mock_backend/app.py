"""Starlette app implementing the PetsFirst MCP REST surface with fixture data."""

from __future__ import annotations

import os
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mock_backend import fixtures
from mock_backend.state import STATE


def _prefix() -> str:
    raw = os.environ.get("MOCK_API_PREFIX", "/api/v1.0/mcp").strip().rstrip("/")
    return raw if raw.startswith("/") else f"/{raw}"


def _ok(data: Any, *, status: int = 200) -> JSONResponse:
    return JSONResponse({"status": status, "data": data}, status_code=status)


async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok"})


async def auth(request: Request) -> JSONResponse:
    _ = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    return JSONResponse({"access_token": "mock-access-token", "expires_in": 86_400})


async def identify_user(request: Request) -> JSONResponse:
    phone = request.path_params["phone"]
    if not fixtures.is_registered_phone(phone):
        return JSONResponse({"status": 200, "message": "not found", "data": None})
    return _ok(fixtures.REGISTERED_USER)


async def fetch_pets(request: Request) -> JSONResponse:
    phone = request.path_params["phone"]
    if not fixtures.is_registered_phone(phone):
        return _ok([])
    return _ok(STATE.pets(phone))


async def fetch_clinics(_: Request) -> JSONResponse:
    return _ok(fixtures.CLINICS)


async def validate_coverage(request: Request) -> JSONResponse:
    lat = float(request.query_params.get("lat", "0"))
    # Rough UAE bounding box for “serviceable” in local dev.
    serviceable = 22.0 <= lat <= 26.5
    body = {"message": "You are in operational area" if serviceable else "We are not yet operational in the selected area"}
    status = 200 if serviceable else 451
    return JSONResponse({**body, "status": status}, status_code=status)


async def fetch_services(request: Request) -> JSONResponse:
    clinic_id = request.path_params["clinic_id"]
    pet_id = request.query_params.get("petId", "1")
    return JSONResponse(fixtures.services_payload(clinic_id, pet_id))


async def fetch_service_catalog(_: Request) -> JSONResponse:
    return _ok(fixtures.service_catalog())


async def fetch_monthly_discount(request: Request) -> JSONResponse:
    clinic_id = request.query_params.get("clinicId", "")
    package_id = request.query_params.get("packageId", "")
    package_type = request.query_params.get("packageType", "")
    return _ok(fixtures.monthly_discount(clinic_id, package_id, package_type))


async def fetch_slots(request: Request) -> JSONResponse:
    date_str = (request.query_params.get("startDate") or "2026-06-10")[:10]
    # Empty on the 1st of the month to exercise client fall-forward in tests.
    if date_str.endswith("-01"):
        return _ok([])
    return _ok(fixtures.slots_for_date(date_str))


async def fetch_appointments(request: Request) -> JSONResponse:
    phone = request.path_params["phone"]
    if not fixtures.is_registered_phone(phone):
        return _ok([])
    return _ok(STATE.appointments(phone))


async def fetch_discounts(_: Request) -> JSONResponse:
    return _ok(fixtures.DISCOUNTS)


async def create_pet(request: Request) -> JSONResponse:
    body = await request.json()
    return JSONResponse(
        STATE.add_pet(
            int(body.get("user", fixtures.REGISTERED_USER["id"])),
            int(body.get("petType", 1)),
            body.get("name"),
            body.get("size"),
        )
    )


async def update_pet(request: Request) -> JSONResponse:
    body = await request.json()
    result = STATE.update_pet(request.path_params["pet_id"], body.get("name"), body.get("size"))
    return JSONResponse(result, status_code=result.get("status", 200))


async def update_parent(request: Request) -> JSONResponse:
    _ = request.path_params["user_id"]
    body = await request.json()
    if not body:
        return JSONResponse({"status": 400, "message": "No fields to update"}, status_code=400)
    return JSONResponse({"status": 200, "message": "User updated successfully", "data": body})


async def create_booking(request: Request) -> JSONResponse:
    body = await request.json()
    return JSONResponse(STATE.create_booking(body))


async def reschedule_appointment(request: Request) -> JSONResponse:
    payload = await request.json()
    data = payload.get("data") if isinstance(payload, dict) else {}
    start_time = data.get("startTime", "") if isinstance(data, dict) else ""
    result = STATE.reschedule(request.path_params["appointment_id"], start_time)
    return JSONResponse(result, status_code=result.get("status", 200))


async def cancel_appointment(request: Request) -> JSONResponse:
    result = STATE.cancel(request.path_params["appointment_id"])
    return JSONResponse(result, status_code=result.get("status", 200))


def create_app() -> Starlette:
    p = _prefix()

    routes = [
        Route("/health", health, methods=["GET"]),
        Route(f"{p}/auth", auth, methods=["POST"]),
        Route(f"{p}/users/identifyByPhone/{{phone}}", identify_user, methods=["GET"]),
        Route(f"{p}/pets/fetchPetsByPhone/{{phone}}", fetch_pets, methods=["GET"]),
        Route(f"{p}/clinics", fetch_clinics, methods=["GET"]),
        Route(f"{p}/clinics/mobile/operationalArea", validate_coverage, methods=["GET"]),
        Route(f"{p}/services/{{clinic_id}}", fetch_services, methods=["GET"]),
        Route(f"{p}/services", fetch_service_catalog, methods=["GET"]),
        Route(f"{p}/slots/fetchMonthlyDiscount", fetch_monthly_discount, methods=["GET"]),
        Route(f"{p}/slots", fetch_slots, methods=["GET"]),
        Route(f"{p}/appointments/fetchAppointmentsByPhone/{{phone}}", fetch_appointments, methods=["GET"]),
        Route(f"{p}/discounts", fetch_discounts, methods=["GET"]),
        Route(f"{p}/pets", create_pet, methods=["POST"]),
        Route(f"{p}/pets/{{pet_id}}", update_pet, methods=["PATCH"]),
        Route(f"{p}/users/{{user_id}}", update_parent, methods=["PATCH"]),
        Route(f"{p}/appointments", create_booking, methods=["POST"]),
        Route(f"{p}/appointments/{{appointment_id}}", reschedule_appointment, methods=["PATCH"]),
        Route(f"{p}/appointments/{{appointment_id}}", cancel_appointment, methods=["DELETE"]),
    ]
    return Starlette(routes=routes)
