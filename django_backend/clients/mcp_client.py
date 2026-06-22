"""Async HTTP client for the PetsFirst MCP Backend API with retries."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
MAX_RETRIES = 3


class MCPClientError(Exception):
    """Raised when MCP Backend returns an error or is unreachable."""


class MCPClient:
    def __init__(self, base_url: str | None = None) -> None:
        raw = (base_url or settings.MCP_BACKEND_URL).rstrip("/")
        self.base_url = raw

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_exc: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                    response = await client.request(method, url, params=params, json=json)
                    response.raise_for_status()
                    data = response.json()
                    if isinstance(data, dict):
                        return data
                    return {"data": data}
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                logger.warning(
                    "MCP request failed (%s %s) attempt %s/%s: %s",
                    method,
                    path,
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt == MAX_RETRIES:
                    break

        raise MCPClientError(f"MCP request failed after {MAX_RETRIES} attempts: {last_exc}")

    async def get_user_by_phone(self, phone: str) -> Optional[dict[str, Any]]:
        payload = await self._request("GET", f"/users/identifyByPhone/{phone}")
        return payload.get("data")

    async def get_user_pets(self, phone: str) -> list[Any]:
        payload = await self._request("GET", f"/pets/fetchPetsByPhone/{phone}")
        data = payload.get("data")
        return data if isinstance(data, list) else []

    async def get_clinics(self) -> list[Any]:
        payload = await self._request("GET", "/clinics")
        data = payload.get("data")
        return data if isinstance(data, list) else []

    async def get_services(self, clinic_id: int, pet_id: Optional[int] = None) -> list[Any]:
        params = {"petId": pet_id} if pet_id is not None else None
        payload = await self._request("GET", f"/services/{clinic_id}", params=params)
        services = payload.get("services")
        if isinstance(services, list):
            return services
        data = payload.get("data")
        return data if isinstance(data, list) else []

    async def get_slots(self, clinic_id: int, date: str) -> list[Any]:
        payload = await self._request(
            "GET",
            "/slots",
            params={"clinicId": clinic_id, "startDate": date},
        )
        data = payload.get("data")
        return data if isinstance(data, list) else []

    async def get_appointments(self, phone: str) -> list[Any]:
        payload = await self._request(
            "GET", f"/appointments/fetchAppointmentsByPhone/{phone}"
        )
        data = payload.get("data")
        return data if isinstance(data, list) else []

    async def get_monthly_discount(
        self, clinic_id: str, package_id: str, package_type: str
    ) -> dict[str, Any]:
        payload = await self._request(
            "GET",
            "/slots/fetchMonthlyDiscount",
            params={
                "clinicId": clinic_id,
                "packageId": package_id,
                "packageType": package_type,
            },
        )
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    async def get_discounts(self) -> list[Any]:
        payload = await self._request("GET", "/discounts")
        data = payload.get("data")
        return data if isinstance(data, list) else []

    async def create_appointment(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/appointments", json=body)

    async def cancel_appointment(self, appointment_id: int, phone: str) -> dict[str, Any]:
        return await self._request(
            "DELETE",
            f"/appointments/{appointment_id}",
            params={"phone": phone},
        )

    async def reschedule_appointment(
        self, appointment_id: int, new_start: str, phone: str
    ) -> dict[str, Any]:
        return await self._request(
            "PATCH",
            f"/appointments/{appointment_id}",
            json={"data": {"startTime": new_start, "phone": phone}},
        )

    async def validate_mobile_coverage(self, latitude: float, longitude: float) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/clinics/mobile/operationalArea",
            params={"lat": latitude, "lng": longitude},
        )


_default_client: MCPClient | None = None


def get_mcp_client() -> MCPClient:
    global _default_client
    if _default_client is None:
        _default_client = MCPClient()
    return _default_client
