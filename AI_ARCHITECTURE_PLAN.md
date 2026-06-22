# PetsFirst WhatsApp AI Agent - AI Architecture Plan

## Summary

This document outlines the AI service architecture using **Anthropic's Model Context Protocol (MCP)** with **Pydantic AI**. The AI service is structured as **3 MCP servers with 14 tools** that expose LLM capabilities to the Django backend.

**Note**: Intent classification, service mapping, response generation, and embedding creation are handled automatically by Pydantic AI in Django orchestrator. Additionally, `get_user_by_phone` is called directly by Django webhook handler before LLM orchestration.

## Architecture Overview

### Complete System Architecture

```mermaid
flowchart TB
    subgraph external["External Systems"]
        user(["WhatsApp User"])
        waba["WhatsApp Business API\n(Meta)"]
        mcp_backend["MCP Backend API\n(PetsFirst Existing)"]
        openai["OpenAI API\n(GPT-4o-mini + Embeddings)"]
    end

    subgraph petsfirst_ai["PetsFirst AI System"]
        subgraph django["Django Backend\n(Orchestrator)"]
            webhook["Webhook Handler\n/apps/webhooks"]
            processor["Message Processor\n/apps/orchestrator"]
            session_mgr["Session Manager\nRedis Client"]
            event_logger["Event Logger\nPostgreSQL Client"]
            pydantic_ai["Pydantic AI\nMCP Client"]
        end

        subgraph mcp_servers["MCP Servers (3 Total)"]
            ai_server["AI Agent MCP Server\nPort: 8001\n\nTools (2):\n• extract_entities\n• answer_faq"]

            api_server["PetsFirst API MCP Server\nPort: 8002\n\nTools (9):\n• get_user_pets\n• get_clinics\n• get_services\n• get_slots\n• get_appointments\n• create_appointment\n• cancel_appointment\n• reschedule_appointment\n• validate_mobile_coverage"]

            kb_server["Knowledge Base MCP Server\nPort: 8003\n\nTools (3):\n• search_knowledge\n• get_canned_message\n• create_knowledge_entry"]
        end

        subgraph storage["Storage Layer"]
            redis[("Redis\nSession State\nTTL: 24h")]
            postgres[("PostgreSQL + pgvector\n• Conversation Events\n• Knowledge Entries\n• Embeddings (1536 dim)")]
        end
    end

    user -->|"1. Send Message"| waba
    waba -->|"2. POST /webhooks/whatsapp"| webhook
    webhook -->|"3. Route Message"| processor
    processor <-->|"4. Get/Set Session"| session_mgr
    session_mgr <-->|"5. Session Data"| redis
    processor -->|"6. Call MCP Tools"| pydantic_ai
    pydantic_ai <-->|"7a. stdio/SSE"| ai_server
    pydantic_ai <-->|"7b. stdio/SSE"| api_server
    pydantic_ai <-->|"7c. stdio/SSE"| kb_server
    ai_server <-->|"8a. LLM Calls"| openai
    api_server <-->|"8b. REST API"| mcp_backend
    kb_server <-->|"9. Vector Search"| postgres
    ai_server -.->|"10. Store Embeddings"| postgres
    processor -->|"11. Log Events"| event_logger
    event_logger -->|"12. Persist"| postgres
    processor -->|"13. POST /messages"| waba
    waba -->|"14. Deliver"| user
```

### Component Responsibilities

| Component | Technology | Responsibility |
|-----------|------------|--------------|
| **Django Backend** | Django + DRF | Webhook handler, orchestrator, session management |
| **Pydantic AI** | pydantic-ai | MCP client, agent orchestration, LLM-based intent classification, service mapping, response generation |
| **AI Agent MCP** | FastAPI + Pydantic AI | Entity extraction, FAQ answering with RAG |
| **PetsFirst API MCP** | FastAPI + httpx | Proxy to existing MCP Backend |
| **Knowledge MCP** | FastAPI + asyncpg | RAG with pgvector, canned messages |
| **Redis** | Redis | Ephemeral session state |
| **PostgreSQL** | PostgreSQL + pgvector | Events, knowledge base, embeddings |

### Tool Summary by Server

| Server | Tool Count | Primary Function |
|--------|-----------|------------------|
| AI Agent MCP | 2 | Entity extraction & FAQ answering |
| PetsFirst API MCP | 9 | Business data operations (proxy) |
| Knowledge Base MCP | 3 | Knowledge retrieval & management |
| **Total** | **14** | - |

**Note**: `get_user_by_phone` is called directly by Django webhook handler before LLM orchestration.

---

## Message Flow Diagram

### High-Level Flow

```mermaid
flowchart LR
    user([WhatsApp User])
    wa[WhatsApp Business API]
    django[Django Backend]
    ai[AI Agent MCP]
    api[PetsFirst API MCP]
    kb[Knowledge MCP]
    backend[MCP Backend]
    db[(PostgreSQL)]
    redis[(Redis)]

    user -->|1. Send Message| wa
    wa -->|2. Webhook| django
    django -->|3a. Classify (Pydantic AI)| django
    django -->|3b. Get User| api
    api -->|4. API Call| backend
    backend -->|User Data| api
    api -->|User Data| django
    django -->|5. Extract Entities| ai
    ai -->|Entities| django
    django -->|6. Get Services| api
    api -->|7. API Call| backend
    backend -->|Services| api
    api -->|Services| django
    django -->|8. Update State| redis
    django -->|9. Generate (Pydantic AI)| django
    django -->|10. Log Event| db
    django -->|11. Send Response| wa
    wa -->|12. Deliver| user
```

### Booking Flow Example

```mermaid
sequenceDiagram
    actor User
    participant WA as WhatsApp API
    participant DJ as Django Orchestrator
    participant AI as AI Agent MCP
    participant API as PetsFirst API MCP
    participant KB as Knowledge MCP
    participant Backend as MCP Backend
    participant Redis as Redis
    participant DB as PostgreSQL

    User->>WA: "Book grooming for Luna tomorrow"
    WA->>DJ: POST /webhooks/whatsapp
    
    rect rgb(255, 245, 230)
        Note over DJ,Backend: Step 1: Fetch User (Django Direct Call)
        DJ->>Backend: GET /users/identifyByPhone/{phone}
        Backend-->>DJ: User Data
    end
    
    rect rgb(230, 245, 255)
        Note over DJ: Step 2: Intent Classification (Pydantic AI)
        DJ->>DJ: Pydantic AI Agent classifies intent
        DJ->>DJ: {intent: "booking", confidence: 0.95}
    end
    
    rect rgb(255, 245, 230)
        Note over DJ,Backend: Step 3: Get User Pets
        DJ->>API: get_user_pets(phone)
        API->>Backend: GET /pets/fetchPetsByPhone/{phone}
        Backend-->>API: Pets List
        API-->>DJ: Pets
    end
    
    rect rgb(230, 255, 230)
        Note over DJ,AI: Step 4: Extract Entities
        DJ->>AI: extract_entities(message, user_context)
        AI->>AI: Match "Luna" to pet, "tomorrow" to date
        AI-->>DJ: {pet: "Luna", date: "2026-06-20"}
    end
    
    rect rgb(255, 230, 245)
        Note over DJ,Backend: Step 5: Get Available Services
        DJ->>API: get_services(clinic_id, pet_id)
        API->>Backend: GET /services/{clinic_id}
        Backend-->>API: Services
        API-->>DJ: [Grooming, Vaccination, Consultation]
    end
    
    DJ->>Redis: Update Session State
    
    rect rgb(230, 245, 255)
        Note over DJ: Step 6: Generate Response (Pydantic AI)
        DJ->>DJ: Pydantic AI Agent generates response
        DJ->>DJ: "Great! For Luna, we have..."
    end
    
    DJ->>DB: Log Conversation Event
    DJ->>WA: POST /messages
    WA->>User: "Great! For Luna, we have..."
```

### FAQ Flow Example

```mermaid
sequenceDiagram
    actor User
    participant WA as WhatsApp API
    participant DJ as Django Orchestrator
    participant AI as AI Agent MCP
    participant KB as Knowledge MCP
    participant DB as PostgreSQL
    participant Redis as Redis

    User->>WA: "What are your grooming prices?"
    WA->>DJ: POST /webhooks/whatsapp
    
    DJ->>Redis: Get Session
    Redis-->>DJ: Session Data
    
    rect rgb(230, 245, 255)
        Note over DJ: Intent Detection (Pydantic AI)
        DJ->>DJ: Pydantic AI classifies as FAQ
        DJ->>DJ: {intent: "faq"}
    end
    
    rect rgb(255, 245, 230)
        Note over DJ,KB: Vector Search
        DJ->>KB: search_knowledge(query)
        KB->>DB: SELECT ... ORDER BY embedding <=> query
        DB-->>KB: Top 3 Results
        KB-->>DJ: Knowledge Entries with similarity
    end
    
    rect rgb(230, 255, 230)
        Note over DJ,AI: Generate Answer
        DJ->>AI: answer_faq(question, context)
        AI->>AI: Use RAG context
        AI-->>DJ: "Our grooming services start at AED 200..."
    end
    
    DJ->>DB: Log Event
    DJ->>WA: Send Response
    WA->>User: "Our grooming services start at AED 200..."
```

### Multi-Pet Booking Flow

```mermaid
flowchart TB
    subgraph step1["Step 1: Intent Detection (Pydantic AI)"]
        A[User: "Book for Luna and Max"] --> B[Django]
        B --> C[Pydantic AI Agent]
        C --> D[Intent: booking<br/>multi_pet: true]
    end

    subgraph step2["Step 2: User & Pets"]
        D --> E[Django]
        E --> F[PetsFirst API MCP<br/>get_user_by_phone]
        F --> G[User Data]
        E --> H[PetsFirst API MCP<br/>get_user_pets]
        H --> I[Pets: Luna, Max, Charlie]
    end

    subgraph step3["Step 3: Pet Matching"]
        I --> J[AI Agent MCP<br/>extract_entities]
        J --> K[Matched: Luna, Max<br/>Missed: Charlie]
    end

    subgraph step4["Step 4: Sequential Booking"]
        K --> L[Django asks:<br/>"Book for both Luna and Max?"]
        L --> M[User confirms]
        M --> N[Booking for Luna]
        N --> O[PetsFirst API MCP<br/>create_appointment]
        O --> P[Booking for Max]
        P --> Q[PetsFirst API MCP<br/>create_appointment]
    end

    subgraph step5["Step 5: Confirmation (Pydantic AI)"]
        Q --> R[Django + Pydantic AI]
        R --> S["All set! Booked:<br/>• Luna - June 20, 3pm<br/>• Max - June 20, 4pm"]
    end

    step1 --> step2 --> step3 --> step4 --> step5
```

---

## MCP Servers

### Server 1: AI Agent MCP Server

**Purpose**: Natural language processing using LLM
**Framework**: FastAPI + Pydantic AI + OpenAI GPT-4o-mini
**Transport**: stdio or SSE (HTTP Server-Sent Events)

#### Tools (2 total)

**Note**: Intent classification, service mapping, response generation, and embedding creation are now handled automatically by Pydantic AI in the Django orchestrator, not as explicit MCP tools.

| # | Tool Name | Purpose | Input | Output |
|---|-----------|---------|-------|--------|
| 1 | `extract_entities` | Extract pets/dates/services | message, user_context | entities dict |
| 2 | `answer_faq` | Answer using RAG context | question, retrieved_context | answer |

#### Code

```python
# ai_agent_server/main.py
"""
AI Agent MCP Server
Exposes LLM capabilities via Model Context Protocol.
"""

import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Initialize MCP Server
mcp = FastMCP("ai-agent-server")

# Initialize Pydantic AI Agent with OpenAI
model = OpenAIModel('gpt-4o-mini')
agent = Agent(model)


# ============================================================
# TOOL 1: classify_intent
# ============================================================

@mcp.tool()
async def classify_intent(
    message: str,
    context: dict
) -> dict:
    """
    Classify user intent from WhatsApp message.
    
    Detects: booking, reschedule, cancel, view_appointments, 
             view_pets, faq, handoff, greeting, goodbye, ambiguous
    
    Args:
        message: The user's message text (supports English/Arabic)
        context: Current conversation state including active_flow, current_step
    
    Returns:
        {
            "primary_intent": "booking",
            "confidence": 0.95,
            "detected_language": "en",
            "requires_clarification": false,
            "secondary_intent": "faq"
        }
    """
    result = await agent.run(f"""
You are an intent classifier for a pet clinic WhatsApp chatbot.

USER MESSAGE: "{message}"
CONVERSATION CONTEXT: {json.dumps(context, indent=2)}

TASK: Classify the user's intent.

INTENT OPTIONS:
- booking: User wants to make an appointment
- reschedule: User wants to change an existing appointment
- cancel: User wants to cancel an appointment
- view_appointments: User wants to see their upcoming appointments
- view_pets: User wants to see their registered pets
- faq: User is asking a question about services, prices, policies
- handoff: User wants to talk to a human agent
- greeting: User is saying hello
- goodbye: User is ending the conversation
- ambiguous: Cannot determine intent

GUIDELINES:
1. Detect language (en or ar)
2. Consider conversation context - is there an active flow?
3. Calculate confidence (0.0 to 1.0)
4. Flag if clarification is needed

OUTPUT FORMAT (JSON):
{{
    "primary_intent": "<intent>",
    "confidence": <0.0-1.0>,
    "detected_language": "en|ar",
    "requires_clarification": true|false,
    "secondary_intent": "<intent>|null"
}}

Respond with only the JSON object.
""")
    
    return json.loads(result.data)


# ============================================================
# TOOL 2: extract_entities
# ============================================================

@mcp.tool()
async def extract_entities(
    message: str,
    user_context: dict
) -> dict:
    """
    Extract entities (pets, dates, times, services) from message.
    
    Args:
        message: User's message text
        user_context: User's pets and other context from MCP Backend
    
    Returns:
        {
            "pet_names": ["Buddy", "Max"],
            "date_references": ["tomorrow", "next Monday"],
            "time_references": ["3pm", "morning"],
            "service_hints": ["grooming", "vaccination"],
            "clinic_hints": ["Dubai Marina"],
            "normalized_dates": ["2024-06-20"],
            "confidence": 0.85
        }
    """
    result = await agent.run(f"""
You are an entity extractor for a pet clinic WhatsApp chatbot.

USER MESSAGE: "{message}"
USER PETS: {json.dumps(user_context.get('pets', []), indent=2)}

TASK: Extract relevant entities for appointment booking.

ENTITY TYPES:
1. Pet names (match against user's registered pets)
2. Date references (today, tomorrow, next Monday, etc.)
3. Time references (3pm, morning, evening, etc.)
4. Service hints (grooming, vaccination, checkup, etc.)
5. Clinic hints (location names)

GUIDELINES:
- Normalize dates to YYYY-MM-DD format (today = {user_context.get('today', '2024-06-19')})
- Extract partial matches for pet names
- Capture service hints even if not exact matches
- Handle both English and Arabic

OUTPUT FORMAT (JSON):
{{
    "pet_names": ["extracted pet names"],
    "date_references": ["raw date mentions"],
    "time_references": ["raw time mentions"],
    "service_hints": ["extracted services"],
    "clinic_hints": ["extracted clinic locations"],
    "normalized_dates": ["YYYY-MM-DD"],
    "confidence": 0.0-1.0
}}

Respond with only the JSON object.
""")
    
    return json.loads(result.data)


# ============================================================
# TOOL 3: map_service
# ============================================================

@mcp.tool()
async def map_service(
    user_input: str,
    services: list
) -> dict:
    """
    Match user service request to available services.
    
    Args:
        user_input: What the user said they want (e.g., "grooming", "bath")
        services: List of available services from MCP Backend
    
    Returns:
        {
            "service_id": 123,
            "service_name": "Pet Grooming",
            "confidence": 0.92,
            "auto_select": true,
            "alternatives": [
                {"id": 124, "name": "Full Grooming", "confidence": 0.75}
            ]
        }
    """
    result = await agent.run(f"""
You are a service mapper for a pet clinic WhatsApp chatbot.

USER INPUT: "{user_input}"

AVAILABLE SERVICES:
{json.dumps(services, indent=2)}

TASK: Find the best matching service.

GUIDELINES:
1. Calculate similarity for each service
2. Return the best match if confidence >= 0.8
3. Set auto_select=true if confidence >= 0.9
4. Return top 3 alternatives if confidence < 0.9
5. Handle variations: "shot" → "Vaccination", "bath" → "Grooming"

OUTPUT FORMAT (JSON):
{{
    "service_id": <id or null>,
    "service_name": "<matched name or null>",
    "confidence": 0.0-1.0,
    "auto_select": true|false,
    "alternatives": [
        {{"id": <id>, "name": "<name>", "confidence": 0.0-1.0}}
    ]
}}

Respond with only the JSON object.
""")
    
    return json.loads(result.data)


# ============================================================
# TOOL 4: generate_response
# ============================================================

@mcp.tool()
async def generate_response(
    context: dict,
    response_type: str
) -> str:
    """
    Generate conversational WhatsApp response.
    
    Args:
        context: Response context including step, user info, selection options
        response_type: Type of response needed
    
    Returns:
        Response text string
    """
    result = await agent.run(f"""
You are a warm, friendly WhatsApp chatbot for a pet clinic.

RESPONSE TYPE: {response_type}
CONTEXT: {json.dumps(context, indent=2)}

TONE GUIDELINES:
- Conversational and warm like talking to a friend
- Use pet-related emojis sparingly (🐾, 🐶, 🐱)
- Show personality: "That sounds perfect for Buddy!"
- Avoid robotic language: no "Please select from the following"
- Use warm phrases: "We're excited to see", "That works great"
- Max 2-3 sentences per bubble for WhatsApp

RESPONSE TYPES:
- booking_confirmation: Confirm booking details
- slot_suggestion: Suggest available time slots
- service_selection: Ask user to choose service
- pet_confirmation: Confirm which pet
- welcome_greeting: First-time greeting
- goodbye: End conversation
- error: Handle errors gracefully
- handoff: Transfer to human agent

For selections, use bullet points with numbers, not formal lists.
Example: "Here are some options:
• 1. Monday 10am - 12pm
• 2. Wednesday 2pm - 4pm"

Generate the response now:
""")
    
    return result.data


# ============================================================
# TOOL 5: answer_faq
# ============================================================

@mcp.tool()
async def answer_faq(
    question: str,
    retrieved_context: list
) -> str:
    """
    Answer FAQ using retrieved knowledge context (RAG).
    
    Args:
        question: User's question
        retrieved_context: Top-k retrieved knowledge entries with similarity scores
    
    Returns:
        Natural language answer
    """
    # Build context from retrieved knowledge
    context_text = "\n\n---\n\n".join([
        f"Knowledge Entry {i+1} (Similarity: {entry.get('similarity', 0):.2f}):\n"
        f"Q: {entry.get('question', '')}\n"
        f"A: {entry.get('answer', '')}"
        for i, entry in enumerate(retrieved_context[:3])
    ])
    
    result = await agent.run(f"""
You are a helpful FAQ assistant for a pet clinic WhatsApp chatbot.

USER QUESTION: "{question}"

RETRIEVED KNOWLEDGE:
{context_text}

TASK: Answer the user's question using ONLY the provided knowledge.

GUIDELINES:
1. If answer is in knowledge → provide helpful, conversational response
2. If answer not found → say "I don't have that specific information. Let me connect you with our team who can help!"
3. Keep it warm and friendly
4. Add relevant emoji if appropriate
5. If multiple relevant entries, synthesize them
6. Cite confidence: only answer if similarity >= 0.75

OUTPUT: Direct response text (not JSON)
""")
    
    return result.data


# ============================================================
# TOOL 6: create_embeddings
# ============================================================

@mcp.tool()
async def create_embeddings(
    texts: list
) -> list:
    """
    Generate vector embeddings for RAG.
    
    Args:
        texts: List of texts to embed
    
    Returns:
        List of embedding vectors (1536 dimensions each)
    """
    import openai
    
    client = openai.AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        dimensions=1536
    )
    
    return [d.embedding for d in response.data]


# ============================================================
# SERVER STARTUP
# ============================================================

if __name__ == "__main__":
    # Run with stdio transport (for local process communication)
    # Alternative: mcp.run(transport="sse", port=8001) for HTTP
    mcp.run(transport="stdio")
```

---

### Server 2: PetsFirst API MCP Server

**Purpose**: Proxy to existing MCP Backend API  
**Framework**: FastAPI + httpx  
**Transport**: stdio or SSE

**Note**: `get_user_by_phone` is called directly by Django (not an MCP tool) before LLM orchestration.

#### Tools (9 total)

| # | Tool Name | Purpose | MCP Backend Endpoint |
|---|-----------|---------|---------------------|
| 1 | `get_user_pets` | Get all user pets | `GET /pets/fetchPetsByPhone/{phone}` |
| 2 | `get_clinics` | Get all clinics | `GET /clinics` |
| 3 | `get_services` | Get services for clinic/pet | `GET /services/{clinic_id}?petId={pet_id}` |
| 4 | `get_slots` | Get available time slots | `GET /slots?clinicId={id}&startDate={date}` |
| 5 | `get_appointments` | Get user appointments | `GET /appointments/fetchAppointmentsByPhone/{phone}` |
| 6 | `create_appointment` | Book new appointment | `POST /appointments` |
| 7 | `cancel_appointment` | Cancel appointment | `DELETE /appointments/{id}?phone={phone}` |
| 8 | `reschedule_appointment` | Reschedule appointment | `PATCH /appointments/{id}` |
| 9 | `validate_mobile_coverage` | Check mobile clinic area | `GET /clinics/mobile/operationalArea?lat={lat}&lng={lng}` |

#### Code

```python
# petsfirst_api_server/main.py
"""
PetsFirst API MCP Server
Proxies calls to the existing MCP Backend API.
"""

import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize MCP Server
mcp = FastMCP("petsfirst-api-server")

# MCP Backend configuration
MCP_BASE_URL = os.getenv(
    "MCP_BACKEND_URL",
    "https://stage-petsfirst-backend.azurewebsites.net/api/mcp"
)

# HTTP client for API calls
http_client = httpx.AsyncClient(timeout=30.0)


# ============================================================
# TOOL 1: get_user_by_phone
# ============================================================

@mcp.tool()
async def get_user_by_phone(phone: str) -> Optional[dict]:
    """
    Get user by phone number from MCP Backend.
    
    Returns user data dict or None if not registered.
    """
    response = await http_client.get(
        f"{MCP_BASE_URL}/users/identifyByPhone/{phone}"
    )
    result = response.json()
    return result.get("data")  # None if user not found


# ============================================================
# TOOL 2: get_user_pets
# ============================================================

@mcp.tool()
async def get_user_pets(phone: str) -> list:
    """
    Get all pets for a user.
    """
    response = await http_client.get(
        f"{MCP_BASE_URL}/pets/fetchPetsByPhone/{phone}"
    )
    return response.json().get("data", [])


# ============================================================
# TOOL 3: get_clinics
# ============================================================

@mcp.tool()
async def get_clinics() -> list:
    """
    Get all available clinics.
    """
    response = await http_client.get(f"{MCP_BASE_URL}/clinics")
    return response.json().get("data", [])


# ============================================================
# TOOL 4: get_services
# ============================================================

@mcp.tool()
async def get_services(
    clinic_id: int,
    pet_id: Optional[int] = None
) -> list:
    """
    Get services available at a clinic for a specific pet.
    """
    params = {"petId": pet_id} if pet_id else None
    response = await http_client.get(
        f"{MCP_BASE_URL}/services/{clinic_id}",
        params=params
    )
    return response.json().get("services", [])


# ============================================================
# TOOL 5: get_slots
# ============================================================

@mcp.tool()
async def get_slots(
    clinic_id: int,
    date: str
) -> list:
    """
    Get available time slots for a clinic on a specific date.
    
    Args:
        clinic_id: Clinic ID
        date: Date in YYYY-MM-DD format
    """
    response = await http_client.get(
        f"{MCP_BASE_URL}/slots",
        params={"clinicId": clinic_id, "startDate": date}
    )
    return response.json().get("data", [])


# ============================================================
# TOOL 6: get_appointments
# ============================================================

@mcp.tool()
async def get_appointments(phone: str) -> list:
    """
    Get user's upcoming appointments.
    """
    response = await http_client.get(
        f"{MCP_BASE_URL}/appointments/fetchAppointmentsByPhone/{phone}"
    )
    return response.json().get("data", [])


# ============================================================
# TOOL 7: create_appointment
# ============================================================

@mcp.tool()
async def create_appointment(
    clinicId: int,
    petId: int,
    packageId: int,
    packageType: str,
    dateTime: str,
    phone: str,
    campaignId: Optional[int] = None
) -> dict:
    """
    Create a new appointment (booking).
    
    All 5 fields are required: clinicId, petId, packageId, packageType, dateTime.
    
    Returns created appointment data.
    """
    data = {
        "clinicId": clinicId,
        "petId": petId,
        "packageId": packageId,
        "packageType": packageType,
        "dateTime": dateTime,
        "phone": phone
    }
    if campaignId:
        data["campaignId"] = campaignId
    
    response = await http_client.post(
        f"{MCP_BASE_URL}/appointments",
        json=data
    )
    return response.json()


# ============================================================
# TOOL 8: cancel_appointment
# ============================================================

@mcp.tool()
async def cancel_appointment(
    appointment_id: int,
    phone: str
) -> dict:
    """
    Cancel an existing appointment.
    
    Returns cancellation status.
    """
    response = await http_client.delete(
        f"{MCP_BASE_URL}/appointments/{appointment_id}?phone={phone}"
    )
    return response.json()


# ============================================================
# TOOL 9: reschedule_appointment
# ============================================================

@mcp.tool()
async def reschedule_appointment(
    appointment_id: int,
    new_start: str,
    phone: str
) -> dict:
    """
    Reschedule an appointment to a new time.
    
    Args:
        appointment_id: Appointment to reschedule
        new_start: New start time (ISO 8601 format)
        phone: User's phone number
    
    Returns updated appointment data.
    """
    response = await http_client.patch(
        f"{MCP_BASE_URL}/appointments/{appointment_id}",
        json={
            "data": {"startTime": new_start},
            "phone": phone
        }
    )
    return response.json()


# ============================================================
# TOOL 10: validate_mobile_coverage
# ============================================================

@mcp.tool()
async def validate_mobile_coverage(
    lat: float,
    lng: float
) -> dict:
    """
    Check if a location is within the mobile clinic service area.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        {
            "serviceable": true,
            "message": "We service this area!"
        }
    """
    response = await http_client.get(
        f"{MCP_BASE_URL}/clinics/mobile/operationalArea",
        params={"lat": lat, "lng": lng}
    )
    return response.json()


# ============================================================
# SERVER STARTUP
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

### Server 3: Knowledge Base MCP Server

**Purpose**: RAG knowledge base and canned messages
**Framework**: FastAPI + asyncpg + pgvector
**Transport**: stdio or SSE

#### Tools (3 total)

| # | Tool Name | Purpose | Database |
|---|-----------|---------|----------|
| 1 | `search_knowledge` | Vector search for RAG | `knowledge_entries` |
| 2 | `get_canned_message` | Get templated response | `canned_messages` |
| 3 | `create_knowledge_entry` | Add FAQ entry | `knowledge_entries` |

#### Code

```python
# knowledge_base_server/main.py
"""
Knowledge Base MCP Server
Handles RAG (Retrieval-Augmented Generation) and canned messages.
"""

import os
from typing import Optional

import asyncpg
import openai
from mcp.server.fastmcp import FastMCP

# Initialize MCP Server
mcp = FastMCP("knowledge-base-server")

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pass@localhost:5432/petsfirst"
)

# OpenAI client
openai_client = openai.AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# TOOL 1: search_knowledge
# ============================================================

@mcp.tool()
async def search_knowledge(
    query: str,
    category: Optional[str] = None,
    clinic_id: Optional[int] = None,
    top_k: int = 3
) -> list:
    """
    Search knowledge base using vector similarity (RAG).
    
    Args:
        query: User's question or query
        category: Filter by category (optional)
        clinic_id: Filter by clinic (optional)
        top_k: Number of results to return
    
    Returns:
        List of knowledge entries with similarity scores
        [
            {
                "question": "What are your grooming prices?",
                "answer": "Grooming starts at 150 AED...",
                "category": "pricing",
                "tags": ["grooming", "pricing"],
                "similarity": 0.92
            }
        ]
    """
    # Generate query embedding
    embedding_response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        dimensions=1536
    )
    query_embedding = embedding_response.data[0].embedding
    
    # Search in PostgreSQL with pgvector
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Build query
    sql = """
        SELECT 
            question, 
            answer, 
            category, 
            tags,
            1 - (embedding <=> $1::vector) as similarity
        FROM knowledge_entries
        WHERE is_active = true
    """
    params = [query_embedding]
    
    if category:
        sql += f" AND category = ${len(params) + 1}"
        params.append(category)
    
    if clinic_id:
        sql += f" AND (clinic_id = ${len(params) + 1} OR clinic_id IS NULL)"
        params.append(clinic_id)
    
    sql += f"""
        ORDER BY embedding <=> $1::vector
        LIMIT ${len(params) + 1}
    """
    params.append(top_k)
    
    rows = await conn.fetch(sql, *params)
    await conn.close()
    
    return [
        {
            "question": row["question"],
            "answer": row["answer"],
            "category": row["category"],
            "tags": row["tags"],
            "similarity": float(row["similarity"])
        }
        for row in rows
    ]


# ============================================================
# TOOL 2: get_canned_message
# ============================================================

@mcp.tool()
async def get_canned_message(
    key: str,
    lang: str = "en"
) -> str:
    """
    Get a canned message template by key.
    
    Args:
        key: Message template key (e.g., "welcome", "booking_confirmed")
        lang: Language code (en or ar)
    
    Returns:
        Message text in requested language
    """
    conn = await asyncpg.connect(DATABASE_URL)
    
    row = await conn.fetchrow(
        """
        SELECT message_en, message_ar 
        FROM canned_messages 
        WHERE message_key = $1 AND is_active = true
        """,
        key
    )
    
    await conn.close()
    
    if not row:
        return f"[Message not found: {key}]"
    
    return row["message_ar"] if lang == "ar" else row["message_en"]


# ============================================================
# TOOL 3: create_knowledge_entry
# ============================================================

@mcp.tool()
async def create_knowledge_entry(
    question: str,
    answer: str,
    category: str,
    tags: list = None,
    clinic_id: Optional[int] = None
) -> int:
    """
    Create a new knowledge base entry.
    
    Automatically generates embedding for the entry.
    
    Args:
        question: The question/FAQ
        answer: The answer
        category: Category (e.g., "pricing", "services", "policies")
        tags: List of tags for filtering
        clinic_id: Optional clinic-specific entry
    
    Returns:
        New entry ID
    """
    # Generate embedding
    text_to_embed = f"{question} {answer}"
    
    embedding_response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text_to_embed,
        dimensions=1536
    )
    embedding = embedding_response.data[0].embedding
    
    # Insert into database
    conn = await asyncpg.connect(DATABASE_URL)
    
    entry_id = await conn.fetchval(
        """
        INSERT INTO knowledge_entries 
            (question, answer, category, tags, clinic_id, embedding, is_active, created_at, updated_at)
        VALUES 
            ($1, $2, $3, $4, $5, $6::vector, true, NOW(), NOW())
        RETURNING id
        """,
        question, answer, category, tags or [], clinic_id, embedding
    )
    
    await conn.close()
    
    return entry_id


# ============================================================
# SERVER STARTUP
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Django Backend Integration

### MCP Client Setup

```python
# django_backend/apps/orchestrator/services/mcp_client.py
"""
MCP Client for Django Backend.
Manages connections to all MCP servers.
"""

from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio


class MCPClientManager:
    """
    Manages MCP server connections for Django orchestrator.
    """
    
    def __init__(self):
        self.servers = {}
    
    @asynccontextmanager
    async def ai_agent_session(self):
        """Connect to AI Agent MCP Server."""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "ai_agent_server.main"],
            env=None
        )
        
        async with ClientSession(server_params) as session:
            await session.initialize()
            yield session
    
    @asynccontextmanager
    async def petsfirst_api_session(self):
        """Connect to PetsFirst API MCP Server."""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "petsfirst_api_server.main"],
            env=None
        )
        
        async with ClientSession(server_params) as session:
            await session.initialize()
            yield session
    
    @asynccontextmanager
    async def knowledge_base_session(self):
        """Connect to Knowledge Base MCP Server."""
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "knowledge_base_server.main"],
            env=None
        )
        
        async with ClientSession(server_params) as session:
            await session.initialize()
            yield session


class PydanticAIMCPAgent:
    """
    Pydantic AI Agent with MCP server integration.
    """
    
    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o-mini',
            mcp_servers=[
                MCPServerStdio(
                    'ai-agent',
                    command='python',
                    args=['-m', 'ai_agent_server.main']
                ),
                MCPServerStdio(
                    'petsfirst-api',
                    command='python',
                    args=['-m', 'petsfirst_api_server.main']
                ),
                MCPServerStdio(
                    'knowledge-base',
                    command='python',
                    args=['-m', 'knowledge_base_server.main']
                ),
            ]
        )
```

---

## Dependencies

```txt
# ai_agent_server/requirements.txt
pydantic-ai>=0.0.10
mcp>=0.9.0
openai>=1.10.0

# petsfirst_api_server/requirements.txt
mcp>=0.9.0
httpx>=0.26.0

# knowledge_base_server/requirements.txt
mcp>=0.9.0
asyncpg>=0.29.0
openai>=1.10.0
pgvector>=0.2.5

# django_backend/requirements.txt (add to existing)
pydantic-ai>=0.0.10
mcp>=0.9.0
```

---

## Transport Options

### Option 1: stdio (Local Process)
```python
mcp.run(transport="stdio")
# Django spawns processes and communicates via stdin/stdout
```

### Option 2: SSE (HTTP)
```python
mcp.run(transport="sse", port=8001)
# Django connects via HTTP to localhost:8001/sse
```

### Option 3: Separate Containers
```yaml
# docker-compose.yml
services:
  ai-agent-server:
    build: ./ai_agent_server
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  petsfirst-api-server:
    build: ./petsfirst_api_server
    ports:
      - "8002:8002"
    environment:
      - MCP_BACKEND_URL=${MCP_BACKEND_URL}
  
  knowledge-base-server:
    build: ./knowledge_base_server
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  django:
    build: ./django_backend
    depends_on:
      - ai-agent-server
      - petsfirst-api-server
      - knowledge-base-server
```

---

## Summary

| Component | Tools | Transport | LLM |
|-----------|-------|-----------|-----|
| AI Agent MCP Server | 2 | stdio/SSE | OpenAI GPT-4o-mini |
| PetsFirst API MCP Server | 9 | stdio/SSE | None (proxy) |
| Knowledge Base MCP Server | 3 | stdio/SSE | OpenAI (embeddings) |
| **Total** | **14 Tools** | - | - |

**Note**: `get_user_by_phone` is called directly by Django webhook handler before LLM orchestration.

**Key Benefits:**
- Standardized tool interface via MCP
- Pydantic AI for type-safe LLM interactions
- Django orchestrates via MCP client
- Each server can be scaled independently
- Easy to add new tools to any server