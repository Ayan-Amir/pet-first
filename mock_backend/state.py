"""In-memory mutable state for mock write endpoints."""

from __future__ import annotations

import threading
from copy import deepcopy
from typing import Any

from mock_backend.fixtures import DEFAULT_APPOINTMENTS, DEFAULT_PETS, REGISTERED_PHONES, normalize_phone


class MockState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pets_by_phone: dict[str, list[dict[str, Any]]] = {}
        self._appointments_by_phone: dict[str, list[dict[str, Any]]] = {}
        self._next_pet_id = 5000
        self._next_appointment_id = 20000

    def pets(self, phone: str) -> list[dict[str, Any]]:
        key = normalize_phone(phone)
        with self._lock:
            if key not in self._pets_by_phone:
                self._pets_by_phone[key] = deepcopy(DEFAULT_PETS)
            return deepcopy(self._pets_by_phone[key])

    def add_pet(self, user_id: int, pet_type: int, name: str | None, size: int | None) -> dict[str, Any]:
        with self._lock:
            pet_id = self._next_pet_id
            self._next_pet_id += 1
        pet = {
            "id": pet_id,
            "name": name or "New Pet",
            "gender": "Unknown",
            "dob": None,
            "age": None,
            "petType": {1: "Dog", 2: "Cat"}.get(pet_type, "Dog"),
            "petSize": {1: "Small", 2: "Medium", 3: "Large"}.get(size or 2, "Medium"),
            "user": user_id,
        }
        with self._lock:
            for phone in REGISTERED_PHONES:
                self._pets_by_phone.setdefault(phone, deepcopy(DEFAULT_PETS)).append(pet)
        return {"status": 200, "message": "Pet created", "data": pet}

    def update_pet(self, pet_id: str, name: str | None, size: str | None) -> dict[str, Any]:
        with self._lock:
            for rows in self._pets_by_phone.values():
                for row in rows:
                    if str(row.get("id")) == str(pet_id):
                        if name:
                            row["name"] = name
                        if size:
                            row["petSize"] = size
                        return {"status": 200, "message": "Pet updated", "data": row}
        return {"status": 404, "message": "Pet not found", "data": None}

    def appointments(self, phone: str) -> list[dict[str, Any]]:
        key = normalize_phone(phone)
        with self._lock:
            if key not in self._appointments_by_phone:
                self._appointments_by_phone[key] = deepcopy(DEFAULT_APPOINTMENTS)
            return deepcopy(self._appointments_by_phone[key])

    def create_booking(self, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            appt_id = self._next_appointment_id
            self._next_appointment_id += 1
        phone = normalize_phone(str(body.get("phone", "")))
        record = {
            "id": appt_id,
            "name": "Booked visit",
            "status": "Confirmed",
            "startTime": str(body.get("time", "")),
            "endTime": None,
            "audit": {
                "clinic": body.get("clinicId"),
                "pet": body.get("petId"),
                "package_bundle": body.get("packageId") if body.get("packageType") == "Bundle" else None,
            },
            "pet": {"id": body.get("petId"), "name": "Pet"},
            "package": {"id": body.get("packageId")} if body.get("packageType") == "Package" else None,
            "package_bundle": {"id": body.get("packageId")} if body.get("packageType") == "Bundle" else None,
            "price": {"price": 250.0},
        }
        with self._lock:
            self._appointments_by_phone.setdefault(phone, []).append(record)
        return {"status": 200, "message": "Appointment booked", "data": record}

    def reschedule(self, appointment_id: str, start_time: str) -> dict[str, Any]:
        with self._lock:
            for rows in self._appointments_by_phone.values():
                for row in rows:
                    if str(row.get("id")) == str(appointment_id):
                        row["startTime"] = start_time
                        return {"status": 200, "message": "Rescheduled"}
        return {"status": 404, "message": "Appointment not found"}

    def cancel(self, appointment_id: str) -> dict[str, Any]:
        with self._lock:
            for phone, rows in self._appointments_by_phone.items():
                kept = [row for row in rows if str(row.get("id")) != str(appointment_id)]
                if len(kept) != len(rows):
                    self._appointments_by_phone[phone] = kept
                    return {"status": 200, "message": "Cancelled"}
        return {"status": 404, "message": "Appointment not found"}


STATE = MockState()
