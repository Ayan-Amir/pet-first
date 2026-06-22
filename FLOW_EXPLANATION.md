# PetsFirst WhatsApp AI Agent - Flow Explanation for Lead

## Simple High-Level Flow

```
WhatsApp User
      ↓
WhatsApp Business API (Webhooks)
      ↓
Django Backend (Orchestrator)
      ↓
   ┌──┴──┐
   │     │
   ▼     ▼
MCP     MCP     MCP
┌─────┐ ┌──────────┐ ┌──────────┐
│ AI  │ │PetsFirst │ │Knowledge │
│Tools│ │ API Tools│ │  Tools   │
│(6)  │ │  (10)    │ │   (3)    │
└──┬──┘ └────┬─────┘ └────┬─────┘
   │         │            │
   ▼         ▼            ▼
OpenAI   MCP Backend   PostgreSQL
         (Existing)    + pgvector
```

---

## Detailed Flow Steps

### Step 1: User Sends WhatsApp Message
```
User: "I want to book an appointment for Luna tomorrow"
```

### Step 2: WhatsApp API Sends Webhook to Django
```python
# Django receives webhook
POST /webhooks/whatsapp
{
    "phone": "+971501234567",
    "message": "I want to book an appointment for Luna tomorrow",
    "message_id": "wamid.123..."
}
```

### Step 3: Django Gets Session from Redis
```python
# Django checks Redis for existing session
session = redis.get("session:+971501234567")
# Returns: {active_flow: "booking", current_step: "select_pet", ...}
```

### Step 4: Django Calls MCP Servers via Pydantic AI

**4a. Call AI Agent MCP Server**
```python
# Tool: classify_intent
{
    "message": "I want to book an appointment for Luna tomorrow",
    "context": {"active_flow": "idle"}
}

# Returns:
{
    "primary_intent": "booking",
    "confidence": 0.95,
    "detected_language": "en"
}
```

**4b. Call PetsFirst API MCP Server**
```python
# Tool: get_user_by_phone
{"phone": "+971501234567"}

# Returns:
{
    "id": 123,
    "phone": "+971501234567",
    "default_clinic_id": 5
}
```

**4c. Call PetsFirst API MCP Server**
```python
# Tool: get_user_pets
{"phone": "+971501234567"}

# Returns:
[
    {"id": 1, "name": "Luna", "type": "Cat"},
    {"id": 2, "name": "Max", "type": "Dog"}
]
```

**4d. Call AI Agent MCP Server**
```python
# Tool: extract_entities
{
    "message": "...for Luna tomorrow",
    "user_context": {"pets": [{"name": "Luna"}, {"name": "Max"}]}
}

# Returns:
{
    "pet_names": ["Luna"],
    "date_references": ["tomorrow"],
    "normalized_dates": ["2026-06-20"],
    "service_hints": []
}
```

### Step 5: Django Updates Session State
```python
# Save to Redis
session.active_flow = "booking"
session.current_step = "select_service"
session.state_data = {
    "selected_pet_id": 1,
    "selected_date": "2026-06-20"
}
redis.set("session:+971501234567", session)
```

### Step 6: Django Gets Services via MCP
```python
# Call PetsFirst API MCP Server
# Tool: get_services
{"clinic_id": 5, "pet_id": 1}

# Returns:
[
    {"id": 10, "name": "Vaccination", "price": 150},
    {"id": 11, "name": "Grooming", "price": 200},
    {"id": 12, "name": "Consultation", "price": 100}
]
```

### Step 7: Django Calls AI for Response Generation
```python
# Call AI Agent MCP Server
# Tool: generate_response
{
    "context": {
        "step": "service_selection",
        "pet_name": "Luna",
        "services": [...]
    },
    "response_type": "service_list"
}

# Returns:
"Great! I found Luna in your profile 🐱\n\n"
"For tomorrow (June 20th), here are the services available:\n\n"
"• 1. Vaccination - AED 150\n"
"• 2. Grooming - AED 200\n"
"• 3. Consultation - AED 100\n\n"
"Which one would work best for Luna?"
```

### Step 8: Django Sends WhatsApp Response
```python
# Call WhatsApp API
POST https://graph.facebook.com/v18.0/.../messages
{
    "messaging_product": "whatsapp",
    "to": "+971501234567",
    "text": {"body": "Great! I found Luna..."}
}
```

### Step 9: Django Logs Event
```python
# Save to PostgreSQL
ConversationEvent.objects.create(
    session=session,
    event_type="ai_response",
    data={"intent": "booking", "step": "service_selection"}
)
```

---

## FAQ Flow Example

```
User: "What are your grooming prices?"
         ↓
    WhatsApp API
         ↓
    Django (Orchestrator)
         ↓
    ┌─────────────────┐
    │ AI Agent MCP    │ → classify_intent → {"intent": "faq"}
    └─────────────────┘
         ↓
    ┌─────────────────┐
    │ Knowledge MCP   │ → search_knowledge(query)
    │                 │   Returns top 3 matches
    └─────────────────┘
         ↓
    ┌─────────────────┐
    │ AI Agent MCP    │ → answer_faq(question, context)
    │                 │   Returns answer text
    └─────────────────┘
         ↓
    Django → WhatsApp API → User
    
Response: "Our grooming services start at AED 200 for cats 
           and AED 250 for dogs 🐾 Would you like to book 
           an appointment?"
```

---

## Booking Completion Flow Example

```
User: "Book grooming for Luna tomorrow at 3pm"
         ↓
    Django collects all data via MCP calls:
    - User: get_user_by_phone ✓
    - Pet: "Luna" matched to pet_id: 1 ✓
    - Service: "grooming" mapped to service_id: 11 ✓
    - Date: "tomorrow" → "2026-06-20" ✓
    - Time: "3pm" → find slot via get_slots ✓
         ↓
    ┌──────────────────────────┐
    │ PetsFirst API MCP        │
    │ Tool: create_appointment │
    └──────────────────────────┘
         ↓
    MCP Backend creates booking
         ↓
    Django → AI Agent → generate_response
         ↓
    WhatsApp to User:
    "Perfect! I've booked grooming for Luna on June 20th 
     at 3:00 PM 🎉 Your booking reference is #PF12345. 
     You'll receive a confirmation SMS shortly!"
```

---

## Key Points for Lead

### 1. **MCP Servers = Specialized Tools**
- AI Agent MCP: 6 tools for language tasks (OpenAI)
- PetsFirst API MCP: 10 tools for business data (proxy to existing backend)
- Knowledge MCP: 3 tools for RAG (pgvector)

### 2. **Django is the Brain**
- Receives all webhooks
- Manages session state (Redis)
- Decides which MCP tools to call
- Orchestrates the flow
- Sends WhatsApp responses

### 3. **MCP Servers are Stateless**
- Each tool call is independent
- No session management in MCP servers
- No database in MCP servers (except Knowledge)
- Django manages all state

### 4. **Pydantic AI = Bridge**
- Django uses Pydantic AI Agent
- Pydantic AI connects to MCP servers
- Type-safe tool calling
- Can use AI to decide which tools to call

### 5. **Existing Backend Protected**
- PetsFirst API MCP proxies to existing MCP Backend
- No data duplication
- No database changes
- Read-only from our side (except booking operations)

---

## Comparison: Old vs New

| Aspect | Traditional REST | New MCP Approach |
|--------|-----------------|------------------|
| **API Design** | 6 endpoints | 19 tools |
| **Protocol** | HTTP/REST | MCP (Model Context Protocol) |
| **Discovery** | API docs | Tool listing |
| **Type Safety** | Pydantic models | Pydantic AI integration |
| **Extensibility** | Add endpoints | Add tools to servers |
| **Scaling** | Monolithic | 3 independent servers |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Django** | Python, Django REST Framework |
| **MCP SDK** | Anthropic's `mcp` library |
| **Pydantic AI** | Agent framework |
| **LLM** | OpenAI GPT-4o-mini |
| **Embeddings** | OpenAI text-embedding-3-small |
| **Database** | PostgreSQL + pgvector (RAG) |
| **Cache** | Redis (sessions) |
| **Transport** | stdio or SSE |

---

## Summary

**WhatsApp → Django (Orchestrator) → MCP Servers (3) → Various Backends**

1. **Django** receives webhook, manages session
2. **Django** calls MCP servers via Pydantic AI
3. **MCP servers** do specialized work (AI, API proxy, RAG)
4. **Django** combines results and sends WhatsApp response
5. **Django** logs everything to PostgreSQL