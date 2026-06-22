"""Static PetsFirst API payloads for local AI development.

Phones:
  - 923001234567, 971500000000 → registered customer (user 893)
  - prefix 99999… → unregistered (identify returns null data)
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

REGISTERED_PHONES = frozenset({"923001234567", "971500000000"})

REGISTERED_USER: dict[str, Any] = {
    "id": 893,
    "name": "Zahra",
    "referenceId": 4,
    "referenceName": "PetsFirst, Al Furjan",
}

DEFAULT_PETS: list[dict[str, Any]] = [
    {
        "id": 4298,
        "name": "Bruno",
        "gender": "Male",
        "dob": None,
        "age": "3 years",
        "petType": "Dog",
        "petSize": "Medium",
    },
    {
        "id": 4184,
        "name": "Lucy",
        "gender": "Female",
        "dob": None,
        "age": "2 years",
        "petType": "Cat",
        "petSize": "Small",
    },
]

CLINICS: list[dict[str, Any]] = [
    {
        "id": 4,
        "name": "PetsFirst, Al Furjan",
        "phone": "04 451 9138",
        "isMobile": False,
        "location": {"areaName": "Al Furjan", "city": "Dubai"},
        "distance": 2.4,
    },
    {
        "id": 14,
        "name": "PetsFirst, City Walk",
        "phone": "04 575 9646",
        "isMobile": False,
        "location": {"areaName": "Building 13B, City Walk", "city": "Dubai"},
        "distance": 5.1,
    },
    {
        "id": 20,
        "name": "Book a mobile clinic visit",
        "phone": "04 451 9138",
        "isMobile": True,
        "location": {"areaName": "Mobile service", "city": "Dubai"},
    },
]

DEFAULT_APPOINTMENTS: list[dict[str, Any]] = [
    {
        "id": 12374,
        "name": "Pet Grooming",
        "status": "Confirmed",
        "startTime": "2026-06-07 13:00:00",
        "endTime": "2026-06-07 16:00:00",
        "audit": {"clinic": 14, "pet": 4184, "package_bundle": 61},
        "pet": {"id": 4184, "name": "Lucy"},
        "package": None,
        "package_bundle": {"id": 61, "name": "Full Groom", "price": 341.25},
        "price": {"price": 341.25},
    }
]

DISCOUNTS: list[dict[str, Any]] = [
    {"id": 7, "name": "Summer promo", "discountType": "percentage", "discountValue": 10},
]


def normalize_phone(phone: str) -> str:
    return phone.lstrip("+")


def is_registered_phone(phone: str) -> bool:
    normalized = normalize_phone(phone)
    if normalized in REGISTERED_PHONES:
        return True
    return not normalized.startswith("99999")


def services_payload(clinic_id: str, pet_id: str) -> dict[str, Any]:
    _ = pet_id
    clinic_key = int(clinic_id) if clinic_id.isdigit() else 4
    return {
        "clinic": {"id": clinic_key},
        "services": [
            {
                "name": "Consultation",
                "vetType": "Vet",
                "petTypes": [
                    {
                        "packages": [
                            {
                                "id": 55,
                                "name": "General Consultation",
                                "duration": 30,
                                "price": 250.0,
                            }
                        ],
                        "package_bundles": [],
                    }
                ],
            },
            {
                "name": "Pet Grooming",
                "vetType": "Groomer",
                "petTypes": [
                    {
                        "packages": [],
                        "package_bundles": [
                            {
                                "id": 61,
                                "name": "Full Groom - Cat",
                                "duration": 120,
                                "price": 341.25,
                                "discountType": "percentage",
                                "discountValue": 20,
                                "priceAfterDiscount": 273.0,
                            }
                        ],
                    }
                ],
            },
            {
                "name": "Vaccination",
                "vetType": "Vet",
                "petTypes": [
                    {
                        "packages": [{"id": 628, "name": "Annual Vaccination", "duration": 20, "price": 180.0}],
                        "package_bundles": [],
                    }
                ],
            },
        ],
    }


def service_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": clinic["id"],
            "name": clinic["name"],
            "services": deepcopy(services_payload(str(clinic["id"]), "1")["services"]),
        }
        for clinic in CLINICS
        if not clinic.get("isMobile")
    ]


def slots_for_date(date_str: str) -> list[dict[str, Any]]:
    return [
        {"id": f"slot-{date_str}-1", "dateTime": f"{date_str}T09:00:00+04:00", "label": "9:00 AM"},
        {"id": f"slot-{date_str}-2", "dateTime": f"{date_str}T11:00:00+04:00", "label": "11:00 AM"},
        {"id": f"slot-{date_str}-3", "dateTime": f"{date_str}T14:00:00+04:00", "label": "2:00 PM"},
    ]


def monthly_discount(clinic_id: str, package_id: str, package_type: str) -> list[dict[str, Any]]:
    _ = (clinic_id, package_id, package_type)
    return [{"date": "2026-06-01", "discount": {"id": 7}}]
