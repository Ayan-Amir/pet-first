# PetsFirst WhatsApp AI Agent - MCP Architecture Plan

## Architecture with Anthropic MCP + Pydantic AI

### Overview

Using **Anthropic's Model Context Protocol (MCP)** with **Pydantic AI** for structured tool calling:

```
WhatsApp → Django Backend (Orchestrator + MCP Client)
               │
               ├──► MCP Server 1: AI Agent Server
               │       └── Pydantic AI + OpenAI GPT-4o-mini
               │       └── Tools: classify_intent, extract_entities, etc.
               │
               ├──► MCP Server 2: PetsFirst API Server
               │       └── Proxies to MCP Backend
               │       └── Tools: get_user, get_pets, create_booking, etc.
               │
               └──► MCP Server 3: Knowledge Base Server
                       └── pgvector + Django
                       └── Tools: search_knowledge, get_canned_message
```

---

## MCP Servers (3 Total)

### 1. AI Agent MCP Server

**Purpose**: Natural language processing (intent, entities, responses)

**Location**: Separate service (FastAPI + Pydantic AI)

**Tools Exposed**:

| Tool | Input | Output |
|------|-------|--------|
| `classify_intent` | `{message, context}` | `{intent, confidence, language}` |
| `extract_entities` | `{message, user_context}` | `{entities: pets, dates, services}` |
| `map_service` | `{user_input, services}` | `{service, confidence, auto_select}` |
| `generate_response` | `{context, response_type}` | `{text}` |
| `answer_faq` | `{question, knowledge_context}` | `{answer}` |
| `create_embeddings` | `{texts}` | `{embeddings}` |

```python
# ai_agent_server/main.py (MCP Server with Pydantic AI)
from pydantic_ai import Agent
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ai-agent-server")

@mcp.tool()
async def classify_intent(message: str, context: dict) -> dict:
    """
    Classify user intent from WhatsApp message.
    
    Args:
        message: The user's message text
        context: Current flow state, user info
    
    Returns:
        Intent classification with confidence
    """
    agent = Agent('openai:gpt-4o-mini')
    
    result = await agent.run(f"""
        Classify this message for a pet clinic chatbot:
        "{message}"
        Context: {context}
        
        Return JSON with: primary_intent, confidence, detected_language
    """)
    
    return json.loads(result.data)


@mcp.tool()
async def extract_entities(message: str, user_context: dict) -> dict:
    """
    Extract entities (pets, dates, services) from message.
    """
    agent = Agent('openai:gpt-4o-mini')
    
    result = await agent.run(f"""
        Extract from: "{message}"
        User pets: {user_context.get('pets', [])}
        
        Return: pet_names, service_hints, date_references, time_references
    """)
    
    return json.loads(result.data)


@mcp.tool()
async def generate_response(context: dict, response_type: str) -> str:
    """
    Generate conversational WhatsApp response.
    """
    agent = Agent('openai:gpt-4o-mini')
    
    result = await agent.run(f"""
        Generate WhatsApp response for pet clinic:
        Type: {response_type}
        Context: {context}
        
        Guidelines: conversational, warm, use emojis sparingly (🐾), avoid "Please choose"
    """)
    
    return result.data


@mcp.tool()
async def answer_faq(question: str, retrieved_context: list) -> str:
    """
    Answer FAQ using retrieved knowledge context.
    """
    agent = Agent('openai:gpt-4o-mini')
    
    context_text = "\n\n".join([
        f"Q: {c['question']}\nA: {c['answer']}"
        for c in retrieved_context[:3]
    ])
    
    result = await agent.run(f"""
        Answer using ONLY this knowledge:
        {context_text}
        
        Question: "{question}"
        
        If not in context, say "I don't have that information."
    """)
    
    return result.data


@mcp.tool()
async def create_embeddings(texts: list) -> list:
    """
    Generate embeddings for RAG.
    """
    import openai
    client = openai.AsyncOpenAI()
    
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        dimensions=1536
    )
    
    return [d.embedding for d in response.data]


if __name__ == "__main__":
    mcp.run(transport="stdio")  # or "sse" for HTTP
```

---

### 2. PetsFirst API MCP Server

**Purpose**: Proxy to existing MCP Backend (business data)

**Location**: Django app (or separate service)

**Tools Exposed**:

| Tool | Input | Output | MCP Backend Call |
|------|-------|--------|------------------|
| `get_user_by_phone` | `{phone}` | `user dict` | `GET /users/identifyByPhone/{phone}` |
| `get_user_pets` | `{phone}` | `list of pets` | `GET /pets/fetchPetsByPhone/{phone}` |
| `get_clinics` | `{}` | `list of clinics` | `GET /clinics` |
| `get_services` | `{clinic_id, pet_id}` | `list of services` | `GET /services/{clinic_id}` |
| `get_slots` | `{clinic_id, date}` | `list of slots` | `GET /slots` |
| `get_appointments` | `{phone}` | `list of appointments` | `GET /appointments/fetchAppointmentsByPhone/{phone}` |
| `create_appointment` | `{clinicId, petId, packageId, packageType, dateTime}` | `appointment` | `POST /appointments` |
| `cancel_appointment` | `{appointment_id, phone}` | `status` | `DELETE /appointments/{id}` |
| `reschedule_appointment` | `{appointment_id, new_start, phone}` | `appointment` | `PATCH /appointments/{id}` |
| `validate_mobile_coverage` | `{lat, lng}` | `{serviceable, message}` | `GET /clinics/mobile/operationalArea` |

```python
# petsfirst_api_server/main.py (MCP Server)
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("petsfirst-api-server")

# Base URL for PetsFirst MCP Backend
MCP_BASE_URL = "https://stage-petsfirst-backend.azurewebsites.net/api/mcp"
client = httpx.AsyncClient(timeout=30.0)


@mcp.tool()
async def get_user_by_phone(phone: str) -> dict:
    """
    Get user by phone number.
    Returns user data or null if not registered.
    """
    response = await client.get(
        f"{MCP_BASE_URL}/users/identifyByPhone/{phone}"
    )
    result = response.json()
    return result.get("data")  # None if not registered


@mcp.tool()
async def get_user_pets(phone: str) -> list:
    """
    Get all pets for a user.
    """
    response = await client.get(
        f"{MCP_BASE_URL}/pets/fetchPetsByPhone/{phone}"
    )
    return response.json().get("data", [])


@mcp.tool()
async def get_clinics() -> list:
    """
    Get all available clinics.
    """
    response = await client.get(f"{MCP_BASE_URL}/clinics")
    return response.json().get("data", [])


@mcp.tool()
async def get_services(clinic_id: int, pet_id: int = None) -> list:
    """
    Get services available at a clinic for a specific pet.
    """
    params = {"petId": pet_id} if pet_id else None
    response = await client.get(
        f"{MCP_BASE_URL}/services/{clinic_id}",
        params=params
    )
    return response.json().get("services", [])


@mcp.tool()
async def get_slots(clinic_id: int, date: str) -> list:
    """
    Get available time slots for a clinic on a specific date.
    """
    response = await client.get(
        f"{MCP_BASE_URL}/slots",
        params={"clinicId": clinic_id, "startDate": date}
    )
    return response.json().get("data", [])


@mcp.tool()
async def get_appointments(phone: str) -> list:
    """
    Get user's upcoming appointments.
    """
    response = await client.get(
        f"{MCP_BASE_URL}/appointments/fetchAppointmentsByPhone/{phone}"
    )
    return response.json().get("data", [])


@mcp.tool()
async def create_appointment(
    clinicId: int,
    petId: int,
    packageId: int,
    packageType: str,
    dateTime: str,
    phone: str,
    campaignId: int = None
) -> dict:
    """
    Create a new appointment (booking).
    Requires all 5 fields: clinicId, petId, packageId, packageType, dateTime.
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
    
    response = await client.post(
        f"{MCP_BASE_URL}/appointments",
        json=data
    )
    return response.json()


@mcp.tool()
async def cancel_appointment(appointment_id: int, phone: str) -> dict:
    """
    Cancel an existing appointment.
    """
    response = await client.delete(
        f"{MCP_BASE_URL}/appointments/{appointment_id}?phone={phone}"
    )
    return response.json()


@mcp.tool()
async def reschedule_appointment(
    appointment_id: int,
    new_start: str,
    phone: str
) -> dict:
    """
    Reschedule an appointment to a new time.
    """
    response = await client.patch(
        f"{MCP_BASE_URL}/appointments/{appointment_id}",
        json={"data": {"startTime": new_start}, "phone": phone}
    )
    return response.json()


@mcp.tool()
async def validate_mobile_coverage(lat: float, lng: float) -> dict:
    """
    Check if a location is within the mobile clinic service area.
    """
    response = await client.get(
        f"{MCP_BASE_URL}/clinics/mobile/operationalArea",
        params={"lat": lat, "lng": lng}
    )
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

### 3. Knowledge Base MCP Server

**Purpose**: RAG knowledge base and canned messages

**Location**: Django app (shares database)

**Tools Exposed**:

| Tool | Input | Output |
|------|-------|--------|
| `search_knowledge` | `{query, category, clinic_id, top_k}` | `list of results` |
| `get_canned_message` | `{key, lang}` | `message text` |
| `create_knowledge_entry` | `{question, answer, category, tags}` | `entry id` |
| `update_knowledge_embedding` | `{entry_id, text}` | `success` |

```python
# knowledge_base_server/main.py (MCP Server)
from mcp.server.fastmcp import FastMCP
import asyncpg
import openai

mcp = FastMCP("knowledge-base-server")

# Database connection
DATABASE_URL = "postgresql://..."


@mcp.tool()
async def search_knowledge(
    query: str,
    category: str = None,
    clinic_id: int = None,
    top_k: int = 3
) -> list:
    """
    Search knowledge base using vector similarity.
    Returns relevant FAQ entries for RAG.
    """
    # Generate query embedding
    client = openai.AsyncOpenAI()
    embedding_response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        dimensions=1536
    )
    query_embedding = embedding_response.data[0].embedding
    
    # Search in PostgreSQL with pgvector
    conn = await asyncpg.connect(DATABASE_URL)
    
    sql = """
        SELECT question, answer, category, tags,
               1 - (embedding <=> $1) as similarity
        FROM knowledge_entries
        WHERE is_active = true
    """
    params = [query_embedding]
    
    if category:
        sql += " AND category = $2"
        params.append(category)
    
    if clinic_id:
        sql += f" AND (clinic_id = ${len(params) + 1} OR clinic_id IS NULL)"
        params.append(clinic_id)
    
    sql += f"""
        ORDER BY embedding <=> $1
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
            "similarity": row["similarity"]
        }
        for row in rows
    ]


@mcp.tool()
async def get_canned_message(key: str, lang: str = "en") -> str:
    """
    Get a canned message template by key.
    Returns message in specified language (en or ar).
    """
    conn = await asyncpg.connect(DATABASE_URL)
    
    row = await conn.fetchrow(
        "SELECT message_en, message_ar FROM canned_messages WHERE message_key = $1",
        key
    )
    
    await conn.close()
    
    if not row:
        return f"Message not found: {key}"
    
    return row["message_ar"] if lang == "ar" else row["message_en"]


@mcp.tool()
async def create_knowledge_entry(
    question: str,
    answer: str,
    category: str,
    tags: list = None,
    clinic_id: int = None
) -> int:
    """
    Create a new knowledge base entry.
    Automatically generates embedding.
    """
    # Generate embedding
    client = openai.AsyncOpenAI()
    text_to_embed = f"{question} {answer}"
    
    embedding_response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text_to_embed,
        dimensions=1536
    )
    embedding = embedding_response.data[0].embedding
    
    # Insert into database
    conn = await asyncpg.connect(DATABASE_URL)
    
    entry_id = await conn.fetchval(
        """
        INSERT INTO knowledge_entries (question, answer, category, tags, clinic_id, embedding, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, true)
        RETURNING id
        """,
        question, answer, category, tags or [], clinic_id, embedding
    )
    
    await conn.close()
    
    return entry_id


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## Django Backend (MCP Client + Orchestrator)

```python
# django_backend/apps/orchestrator/services/mcp_client.py
from mcp import ClientSession, StdioServerParameters
from contextlib import asynccontextmanager
import json


class MCPClientManager:
    """
    Manages connections to all MCP servers.
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


class MessageProcessor:
    """
    Main orchestrator using MCP tools.
    """
    
    def __init__(self):
        self.mcp = MCPClientManager()
    
    async def process(self, phone: str, message: str, message_id: str):
        """Process message using MCP tools."""
        
        # 1. Mark as read via WhatsApp client (not MCP)
        await self.whatsapp.mark_as_read(message_id)
        
        # 2. Get or create session
        session = await self._get_or_create_session(phone)
        
        # 3. Classify intent using AI Agent MCP Server
        async with self.mcp.ai_agent_session() as ai_session:
            intent_result = await ai_session.call_tool(
                "classify_intent",
                {
                    "message": message,
                    "context": {
                        "active_flow": session.active_flow,
                        "current_step": session.current_step
                    }
                }
            )
        
        # 4. Log event
        await self._log_event(session, "intent_classified", intent_result)
        
        # 5. Get user from PetsFirst API MCP Server
        async with self.mcp.petsfirst_api_session() as api_session:
            user = await api_session.call_tool(
                "get_user_by_phone",
                {"phone": phone}
            )
        
        if not user:
            return await self._handle_unregistered(phone)
        
        # 6. Route to handler
        intent = intent_result["primary_intent"]
        
        if intent == "booking":
            await self._handle_booking(session, user, message, intent_result)
        elif intent == "faq":
            await self._handle_faq(session, user, message)
        # ... other handlers
    
    async def _handle_faq(self, session, user, message):
        """Handle FAQ using MCP tools."""
        
        # 1. Search knowledge base
        async with self.mcp.knowledge_base_session() as kb_session:
            knowledge_results = await kb_session.call_tool(
                "search_knowledge",
                {
                    "query": message,
                    "category": "faq",
                    "clinic_id": session.state_data.get("selected_clinic_id"),
                    "top_k": 3
                }
            )
        
        # 2. Generate answer using AI Agent
        async with self.mcp.ai_agent_session() as ai_session:
            answer = await ai_session.call_tool(
                "answer_faq",
                {
                    "question": message,
                    "retrieved_context": knowledge_results
                }
            )
        
        # 3. Send response via WhatsApp
        await self.whatsapp.send_message(session.phone, answer)
    
    async def _handle_booking(self, session, user, message, intent_result):
        """Handle booking flow using MCP tools."""
        
        # 1. Extract entities
        async with self.mcp.ai_agent_session() as ai_session:
            entities = await ai_session.call_tool(
                "extract_entities",
                {
                    "message": message,
                    "user_context": {"pets": user.get("pets", [])}
                }
            )
        
        # 2. Get pets from API
        async with self.mcp.petsfirst_api_session() as api_session:
            pets = await api_session.call_tool(
                "get_user_pets",
                {"phone": user["phone"]}
            )
        
        # 3. Match pet and update state
        pet_id = self._match_pet(entities.get("pet_names", []), pets)
        session.state_data["selected_pet_id"] = pet_id
        await self._update_session(session)
        
        # 4. Get services
        clinic_id = session.state_data.get("selected_clinic_id", user.get("default_clinic_id"))
        async with self.mcp.petsfirst_api_session() as api_session:
            services = await api_session.call_tool(
                "get_services",
                {"clinic_id": clinic_id, "pet_id": pet_id}
            )
        
        # 5. Map service using AI
        async with self.mcp.ai_agent_session() as ai_session:
            service_mapping = await ai_session.call_tool(
                "map_service",
                {
                    "user_input": entities.get("service_hints", [""])[0],
                    "services": services
                }
            )
        
        # 6. Generate response
        async with self.mcp.ai_agent_session() as ai_session:
            response_text = await ai_session.call_tool(
                "generate_response",
                {
                    "context": {
                        "step": "service_selection",
                        "pet_name": entities.get("pet_names", [""])[0],
                        "service_name": service_mapping.get("mapped_service")
                    },
                    "response_type": "booking_confirmation"
                }
            )
        
        # 7. Send response
        await self.whatsapp.send_message(session.phone, response_text)


# Alternative: Pydantic AI Agent with MCP Tools
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Create agent with MCP servers
agent = Agent(
    'openai:gpt-4o-mini',
    mcp_servers=[
        MCPServerStdio('ai-agent', command='python -m ai_agent_server.main'),
        MCPServerStdio('petsfirst-api', command='python -m petsfirst_api_server.main'),
        MCPServerStdio('knowledge-base', command='python -m knowledge_base_server.main'),
    ]
)


@agent.tool
async def process_whatsapp_message(ctx, phone: str, message: str) -> str:
    """
    Process a WhatsApp message and return the response.
    
    This tool orchestrates the entire conversation flow:
    1. Get/create session
    2. Classify intent
    3. Extract entities
    4. Route to appropriate handler
    5. Generate response
    """
    
    # Get session
    session = await ctx.deps.get_session(phone)
    
    # The agent can now call any MCP tool!
    # It will use tools based on the conversation context
    
    # Example: Agent decides to call get_user_by_phone
    user = await ctx.tools.petsfirst_api.get_user_by_phone(phone=phone)
    
    # Example: Agent decides to classify intent
    intent = await ctx.tools.ai_agent.classify_intent(
        message=message,
        context={"active_flow": session.active_flow}
    )
    
    # Agent continues with tool calls...
    
    return response
```

---

## Summary

### 3 MCP Servers

1. **AI Agent MCP Server** (FastAPI + Pydantic AI + OpenAI)
   - 6 tools: classify_intent, extract_entities, map_service, generate_response, answer_faq, create_embeddings

2. **PetsFirst API MCP Server** (FastAPI + httpx)
   - 10 tools: get_user_by_phone, get_user_pets, get_clinics, get_services, get_slots, get_appointments, create_appointment, cancel_appointment, reschedule_appointment, validate_mobile_coverage

3. **Knowledge Base MCP Server** (FastAPI + asyncpg + pgvector)
   - 3 tools: search_knowledge, get_canned_message, create_knowledge_entry

### Total: 19 Tools across 3 MCP Servers

### Django Backend

- **MCP Client**: Connects to all 3 servers
- **Orchestrator**: Uses Pydantic AI Agent with MCP tools
- **Session Management**: Redis + PostgreSQL
- **WhatsApp Integration**: Direct HTTP calls (not MCP)

---

## Dependencies

```txt
# requirements.txt for AI Agent Server
pydantic-ai>=0.0.10
mcp>=0.9.0
openai>=1.10.0

# requirements.txt for PetsFirst API Server
mcp>=0.9.0
httpx>=0.26.0

# requirements.txt for Knowledge Base Server
mcp>=0.9.0
asyncpg>=0.29.0
openai>=1.10.0
pgvector>=0.2.5

# requirements.txt for Django Backend
pydantic-ai>=0.0.10
mcp>=0.9.0
django>=5.0
djangorestframework>=3.14
redis>=5.0
psycopg2-binary>=2.9
```

---

## Alternative: SSE Transport (HTTP)

Instead of stdio, can use HTTP Server-Sent Events:

```python
# Start MCP servers with SSE transport
mcp.run(transport="sse", port=8001)  # AI Agent
mcp.run(transport="sse", port=8002)  # PetsFirst API
mcp.run(transport="sse", port=8003)  # Knowledge Base

# Django connects via HTTP
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8001/sse") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("classify_intent", {...})
```

This allows running MCP servers as separate containers/services.