# StayEase API Contract

Base URL: `http://localhost:8000`

All requests and responses use `Content-Type: application/json`.

---

## 1. Send a Guest Message

```
POST /api/chat/{conversation_id}/message
```

Sends a guest message to the StayEase AI agent and returns the agent's response.

### Path Parameters

| Parameter         | Type   | Description                          |
|-------------------|--------|--------------------------------------|
| `conversation_id` | `UUID` | Unique identifier for the chat session |

### Request Headers

```
Content-Type: application/json
```

### Request Body

```json
{
  "message": "string"
}
```

### Response — `200 OK`

```json
{
  "response": "string",
  "escalated": "boolean"
}
```

### Realistic Example

**Request**:
```http
POST /api/chat/a1b2c3d4-e5f6-7890-abcd-ef1234567890/message HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "message": "I need a room in Cox's Bazar for 2 nights for 2 guests"
}
```

**Response** — `200 OK`:
```json
{
  "response": "I found some great options in Cox's Bazar for 2 guests (2 nights):\n\n1. Sea View Villa - 4,500 BDT/night (Total: 9,000 BDT)\n2. Beachfront Condo - 6,000 BDT/night (Total: 12,000 BDT)\n3. Inani Beach Cottage - 3,200 BDT/night (Total: 6,400 BDT)\n\nWould you like more details on any of these?",
  "escalated": false
}
```

### Error Responses

| Status Code | Body | When |
|-------------|------|------|
| `400 Bad Request` | `{"detail": "Field 'message' is required."}` | Missing or empty `message` field |
| `422 Unprocessable Entity` | `{"detail": [{"loc": ["body", "message"], "msg": "field required", "type": "value_error.missing"}]}` | Invalid request body format (FastAPI validation) |
| `500 Internal Server Error` | `{"detail": "Agent execution failed. Please try again."}` | LLM timeout or internal agent error |

---

## 2. Get Conversation History

```
GET /api/chat/{conversation_id}/history
```

Retrieves the full conversation history for a given chat session.

### Path Parameters

| Parameter         | Type   | Description                          |
|-------------------|--------|--------------------------------------|
| `conversation_id` | `UUID` | Unique identifier for the chat session |

### Request Headers

```
Accept: application/json
```

### Response — `200 OK`

```json
{
  "conversation_id": "string (UUID)",
  "messages": [
    {
      "role": "user | assistant",
      "content": "string",
      "timestamp": "string (ISO 8601)"
    }
  ]
}
```

### Realistic Example

**Request**:
```http
GET /api/chat/a1b2c3d4-e5f6-7890-abcd-ef1234567890/history HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**Response** — `200 OK`:
```json
{
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "messages": [
    {
      "role": "user",
      "content": "I need a room in Cox's Bazar for 2 nights for 2 guests",
      "timestamp": "2026-04-27T14:30:00Z"
    },
    {
      "role": "assistant",
      "content": "I found some great options in Cox's Bazar for 2 guests (2 nights):\n\n1. Sea View Villa - 4,500 BDT/night\n2. Beachfront Condo - 6,000 BDT/night\n3. Inani Beach Cottage - 3,200 BDT/night\n\nWould you like more details on any of these?",
      "timestamp": "2026-04-27T14:30:05Z"
    },
    {
      "role": "user",
      "content": "Tell me more about Sea View Villa",
      "timestamp": "2026-04-27T14:31:00Z"
    },
    {
      "role": "assistant",
      "content": "Here are the details for Sea View Villa:\n\nLocation: Kolatoli Beach Road, Cox's Bazar\nPrice: 4,500 BDT/night\nMax Guests: 4\nAmenities: WiFi, AC, Hot Water, Sea-facing Balcony, Free Parking\nHouse Rules: No smoking indoors, check-in after 2 PM\n\nWould you like to book this property?",
      "timestamp": "2026-04-27T14:31:08Z"
    }
  ]
}
```

### Error Responses

| Status Code | Body | When |
|-------------|------|------|
| `404 Not Found` | `{"detail": "Conversation not found."}` | No conversation exists with the given UUID |
| `422 Unprocessable Entity` | `{"detail": [{"loc": ["path", "conversation_id"], "msg": "value is not a valid uuid", "type": "type_error.uuid"}]}` | Invalid UUID format in path |
| `500 Internal Server Error` | `{"detail": "Database connection error."}` | PostgreSQL is unreachable |
