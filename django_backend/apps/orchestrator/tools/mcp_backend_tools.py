"""MCP Backend API tool functions registered on the shared agent."""

from __future__ import annotations

from typing import Any, Optional

from apps.orchestrator.services.ai_agent import AgentDeps, agent


@agent.tool
async def get_user_pets(ctx, phone: str) -> list[Any]:
    """Get all pets for a user from MCP Backend."""
    return await ctx.deps.mcp.get_user_pets(phone)


@agent.tool
async def get_clinics(ctx) -> list[Any]:
    """Get all available clinics."""
    return await ctx.deps.mcp.get_clinics()


@agent.tool
async def get_services(ctx, clinic_id: int, pet_id: Optional[int] = None) -> list[Any]:
    """Get services available at a clinic for a specific pet."""
    return await ctx.deps.mcp.get_services(clinic_id, pet_id)


@agent.tool
async def get_slots(ctx, clinic_id: int, date: str) -> list[Any]:
    """Get available time slots for a clinic on a specific date (YYYY-MM-DD)."""
    return await ctx.deps.mcp.get_slots(clinic_id, date)


@agent.tool
async def get_appointments(ctx, phone: str) -> list[Any]:
    """Get user's upcoming appointments."""
    return await ctx.deps.mcp.get_appointments(phone)


@agent.tool
async def get_monthly_discount(
    ctx, clinic_id: str, package_id: str, package_type: str
) -> dict[str, Any]:
    """Get monthly discount for a specific package."""
    return await ctx.deps.mcp.get_monthly_discount(clinic_id, package_id, package_type)


@agent.tool
async def get_discounts(ctx) -> list[Any]:
    """Get all available discounts and promotions."""
    return await ctx.deps.mcp.get_discounts()


@agent.tool
async def create_appointment(
    ctx,
    clinicId: int,
    petId: int,
    packageId: int,
    packageType: str,
    dateTime: str,
    phone: str,
    campaignId: Optional[int] = None,
) -> dict[str, Any]:
    """Create a new appointment (booking)."""
    body: dict[str, Any] = {
        "clinicId": clinicId,
        "petId": petId,
        "packageId": packageId,
        "packageType": packageType,
        "dateTime": dateTime,
        "phone": phone,
    }
    if campaignId is not None:
        body["campaignId"] = campaignId
    return await ctx.deps.mcp.create_appointment(body)


@agent.tool
async def cancel_appointment(ctx, appointment_id: int, phone: str) -> dict[str, Any]:
    """Cancel an existing appointment."""
    return await ctx.deps.mcp.cancel_appointment(appointment_id, phone)


@agent.tool
async def reschedule_appointment(
    ctx, appointment_id: int, new_start: str, phone: str
) -> dict[str, Any]:
    """Reschedule an appointment to a new time."""
    return await ctx.deps.mcp.reschedule_appointment(appointment_id, new_start, phone)


@agent.tool
async def validate_mobile_coverage(
    ctx, latitude: float, longitude: float
) -> dict[str, Any]:
    """Check if mobile clinic operates in the given area."""
    return await ctx.deps.mcp.validate_mobile_coverage(latitude, longitude)
