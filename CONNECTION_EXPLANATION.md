# How Pi Backend and Server UI Connect

This document explains in detail how the Raspberry Pi backend and remote Server UI communicate.

## Quick Answer

**Yes, they work together perfectly!** Here's how:

```
Raspberry Pi (aj/pi-backend)  ◄──REST API + WebSocket──►  Remote Server (aj/server-ui)
     :5001                                                        :5000
   - Has Database                                            - No Database
   - Receives Sensors                                        - Web Interface
   - Processes Data                                          - Shows Results
   - Serves API                                              - Queries Pi
```

The **Server** is just a **client** that talks to the **Pi**.

---

## Detailed Connection Flow

### 1. **Initial Setup**

**Pi Backend starts first:**
```
Raspberry Pi (192.168.1.100)
├─ Generates SSL certificates
├─ Starts Flask app on port 5001
├─ Initializes SQLite database
├─ Starts background worker (processes payloads)
├─ Starts WebSocket server (broadcasts updates)
└─ Starts REST API endpoints (serves data)
```

**Server UI starts second:**
```
Remote Server (192.168.1.200)
├─ Reads config (Pi IP: 192.168.1.100, Port: 5001)
├─ Starts Flask app on port 5000
├─ Creates REST API client → Points to Pi
├─ Creates WebSocket client → Connects to Pi
└─ Initializes web interface (no database locally!)
```

### 2. **REST API Connection (Request/Response)**

**When user opens browser to Server:**
```
User Browser → Server:5000/office/batches
         ↓
Server (Flask app)
  - Receives request
  - Uses remote_db_client.py to ask Pi:
    GET https://192.168.1.100:5001/api/remote/batches
  - Includes X-API-Key header for authentication
         ↓
Raspberry Pi (remote_api.py)
  - Validates API key
  - Queries local SQLite database
  - Returns JSON: {"data": [list of batches]}
         ↓
Server receives response
  - Renders HTML template with batch data
  - Sends HTML to browser
         ↓
User sees batches in web interface
```

**Code Flow:**

```python
# Server: office_app/remote_db_client.py
client = RemoteDBClient('192.168.1.100', 5001)
batches = client.get_batches(limit=50)  # Makes REST API call
# Returns: [{'id': 1, 'batch_number': 'BATCH001', ...}, ...]

# Pi Backend: office_app/remote_api.py
@remote_api_bp.route('/batches', methods=['GET'])
@require_auth
def list_batches_api():
    batches = Batch.query.all()  # Query local SQLite
    return jsonify({'data': [b.to_dict() for b in batches]})
```

### 3. **WebSocket Connection (Real-time Updates)**

**When LoRa sensor sends data to Pi:**
```
LoRa Device → Raspberry Pi (UDP/Serial port)
         ↓
Pi buffers payload to SQLite
         ↓
Pi broadcasts via WebSocket:
  socket.emit('payload:received', {
    'payload_id': 1,
    'raw_payload': 'hxb:BATCH001:LF123:UHF456'
  })
         ↓
Server WebSocket Client (websocket_client.py) receives event
  - Connected to ws://192.168.1.100:5001
  - Listens for 'payload:received' events
  - Triggers callback function
         ↓
Server's Flask app updates in-memory state
         ↓
Server's JavaScript pushes update to browser
         ↓
User sees "New payload received!" in real-time
```

**Code Flow:**

```python
# Server: office_app/websocket_client.py
ws_client = RealtimeUpdatesClient('192.168.1.100', 5001)
ws_client.on('payload:received', on_payload_received_callback)
ws_client.subscribe_payloads()  # Subscribe to updates

def on_payload_received_callback(data):
    print(f"Received payload: {data['raw_payload']}")
    # Trigger UI update
    emit_to_browser('payload_received', data)  # Via Flask-SocketIO

# Pi Backend: office_app/remote_api.py
def broadcast_payload_received(payload_id, raw_payload):
    if socketio:
        socketio.emit('payload:received', {
            'payload_id': payload_id,
            'raw_payload': raw_payload,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)  # Send to ALL connected clients
```

---

## Complete Example: User Views Batches

### Step-by-Step

```
1. User opens browser to http://192.168.1.200:5000
   └─ Types admin/admin

2. Server authenticates user (local session)

3. User clicks "View Batches"
   └─ Browser requests: GET /office/batches

4. Server receives request in office_routes.py
   ├─ Checks if user is authenticated (yes)
   ├─ Calls: remote_db_client.get_batches()
   │         ↓
   │    Makes HTTPS request to Pi:
   │    GET https://192.168.1.100:5001/api/remote/batches
   │    Headers: X-API-Key: hxb_xxxxx
   │         ↓
   └─ Pi remote_api.py receives request
      ├─ Validates API key (✓ matches)
      ├─ Queries SQLite: SELECT * FROM batches
      ├─ Returns JSON: {"data": [...]}
      └─ Server receives response

5. Server renders HTML template
   ├─ Inserts batch data into <table>
   └─ Sends HTML to browser

6. Browser displays batch table

7. Meanwhile... Pi's background_worker processes new payload
   ├─ Creates new batch in SQLite
   ├─ Broadcasts via WebSocket: 'batch:created'
   │  └─ Server's websocket_client receives event
   │     ├─ Triggers callback
   │     ├─ Emits to browser via Flask-SocketIO
   │     └─ JavaScript adds row to table

8. User sees NEW batch appear INSTANTLY
   └─ No page refresh needed! (Real-time)
```

---

## Configuration & Authentication

### On Raspberry Pi

**File: `.env` or environment variables**
```bash
# Enable Pi backend mode
IS_PI_BACKEND=True

# API Key (shared secret)
PI_API_KEY=hxb_6f8a9c2d1e5b4a3f7g8h9i0j

# Database location
SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db
```

**What it does:**
- Enables background worker for payload processing
- Enables REST API endpoints
- Enables WebSocket server
- Expects all requests to include API key

### On Remote Server

**File: `.env` or environment variables**
```bash
# Enable Server UI mode
IS_SERVER_UI=True

# Pi connection details
REMOTE_PI_HOST=192.168.1.100  # or hostname
REMOTE_PI_PORT=5001
PI_API_KEY=hxb_6f8a9c2d1e5b4a3f7g8h9i0j  # MUST MATCH Pi!

# SSL/TLS settings
USE_SSL_FOR_PI=True
USE_SELF_SIGNED_CERT=True  # For self-signed certificates
```

**What it does:**
- Disables local background worker (Pi handles it)
- Disables local database initialization (connects remotely)
- Initializes remote_db_client with Pi address
- Initializes websocket_client and connects to Pi
- When user requests data, queries Pi instead of local DB

---

## Network Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Local Network                             │
│                     (192.168.1.0/24)                             │
│                                                                   │
│  ┌──────────────────────────┐        ┌──────────────────────┐   │
│  │   Raspberry Pi           │        │   Remote Server      │   │
│  │   192.168.1.100:5001     │        │   192.168.1.200:5000 │   │
│  │                          │        │                      │   │
│  │  LoRa Receiver           │        │  Web Interface       │   │
│  │      ↓                   │        │  (Flask + Templates) │   │
│  │  SQLite Database         │        │      ↓               │   │
│  │      ↓                   │        │  remote_db_client    │   │
│  │  Background Worker       │        │  websocket_client    │   │
│  │      ↓                   │        │                      │   │
│  │  REST API Server─────────┼────────┼─→ REST Requests     │   │
│  │  WebSocket Server────────┼────────┼─→ WebSocket Events  │   │
│  │                          │        │                      │   │
│  └──────────────────────────┘        └──────────────────────┘   │
│                                              ↑                   │
│                                          Browser                 │
│                                    (User Interface)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Storage

### Raspberry Pi (Has Database)

```
SQLite: office_app/office_app.db
├── users          (admin credentials)
├── batches        (batch records)
├── cattle         (individual animals)
├── pens           (pen locations)
├── lora_payload_buffer (incoming payloads)
└── cattle_weight_history (weight records)
```

**All data is stored here!**

### Remote Server (No Database)

```
Memory/Session Cache:
├── User sessions (Django/Flask)
├── Cached batch list (from Pi)
└── WebSocket subscriptions (real-time listeners)
```

**No permanent storage!** Just displays what Pi has.

---

## Communication Sequence Diagram

```
┌────────────┐              ┌──────────┐              ┌────────────┐
│   User     │              │ Server   │              │   Pi       │
│  Browser   │              │  (5000)  │              │  (5001)    │
└──────┬─────┘              └────┬─────┘              └────┬───────┘
       │                          │                        │
       │ 1. Login                 │                        │
       ├─────────────────────────→│                        │
       │                          │ (local auth)           │
       │                          │                        │
       │ 2. Click "View Batches"  │                        │
       ├─────────────────────────→│                        │
       │                          │ 3. GET /api/remote/batches
       │                          ├───────────────────────→│
       │                          │ X-API-Key: hxb_xxxxx   │
       │                          │                        │
       │                          │ 4. Query SQLite        │
       │                          │←────────────────────────│
       │                          │ Return JSON            │
       │ 5. Render HTML           │                        │
       │←─────────────────────────┤                        │
       │                          │                        │
       │ (meanwhile...)           │                        │
       │                          │                        │
       │                          │    (background)        │
       │                          │    New payload arrives  │
       │                          │ 6. Broadcast WebSocket ←─── LoRa
       │                          │←─────────────────────────    Sensor
       │ 7. Update table (JS)     │                        │
       │←─────────────────────────┤                        │
       │                          │                        │
```

---

## Example: Complete Data Flow

### Scenario: Farmer sends batch "BATCH001" from barn

```
Timeline:
0:00  LoRa Device → Pi: "hxb:BATCH001:LF123:UHF456"
         │
0:01  Pi buffers to SQLite (lora_payload_buffer)
      Pi broadcasts WebSocket: {'payload_id': 1, ...}
         │
0:02  Server WebSocket client receives event
      Server calls callback function
      Server emits to browser: 'payload_received'
         │
0:03  Browser JavaScript shows: "New Payload: BATCH001"
         │
0:05  Pi's background worker processes
      ├─ Parses: hxb:BATCH001:LF123:UHF456
      ├─ Creates batch in SQLite
      ├─ Broadcasts: 'batch:created'
         │
0:06  Server receives batch:created event
      Server emits to browser: 'batch_created'
         │
0:07  User sees new batch in table (real-time!)
         │
∞     Data persists on Pi's SQLite
      User can refresh browser, data still there
```

---

## What If Pi Crashes?

```
Scenario: Pi backend goes down

Server UI:
├─ REST API calls fail
│  └─ Shows cached data or "connection error"
├─ WebSocket disconnects
│  └─ Retries connection automatically
├─ No data is lost
│  └─ All data is on Pi (when it comes back up)
└─ User can still access old data

When Pi comes back up:
├─ Server automatically reconnects
├─ WebSocket resumes
├─ All data is available again
└─ No data loss!
```

---

## What If Server Crashes?

```
Scenario: Server UI goes down

Pi Backend:
├─ Continues receiving LoRa data
├─ Continues processing payloads
├─ Continues storing in SQLite
├─ All data is preserved
└─ No data is lost

When Server comes back up:
├─ Connects to Pi again
├─ Fetches all batches/payloads via REST API
├─ Resumes WebSocket listening
└─ All data is available (nothing was lost!)
```

---

## Summary

| Aspect | Pi Backend | Server UI |
|--------|-----------|-----------|
| **Database** | SQLite (Has it) | None (Queries Pi) |
| **Purpose** | Data collection & storage | User interface |
| **API Role** | Server (Provides API) | Client (Consumes API) |
| **WebSocket Role** | Broadcaster (Sends events) | Listener (Receives events) |
| **Port** | 5001 | 5000 |
| **Data Owner** | YES | NO (reads from Pi) |
| **Processes Payloads** | YES (background worker) | NO |
| **Runs on** | Raspberry Pi | Any server/PC |
| **Connection Required** | NO (works standalone) | YES (needs Pi) |

---

## Can I Run Both on Same Machine?

Yes! For testing/development:

```bash
# Terminal 1: Start Pi backend
export IS_PI_BACKEND=True
export PI_API_KEY=test123
python -m office_app.run  # Port 5001

# Terminal 2: Start Server UI
export IS_SERVER_UI=True
export REMOTE_PI_HOST=localhost
export REMOTE_PI_PORT=5001
export PI_API_KEY=test123
python -m office_app.run  # Port 5000
```

Both will work perfectly on localhost!

---

## Bottom Line

**Pi backend and Server UI are NOT separate applications.**

They are **two deployments of the same application** configured differently:
- One deployment (Pi) = Backend API provider
- One deployment (Server) = Frontend UI consumer

The Server is a **client** that talks to the Pi.
The Pi is a **server** that responds to the Server.

They communicate via:
1. **REST API** (request/response)
2. **WebSocket** (real-time events)
3. **Shared Secret** (API key for authentication)

Perfect match! ✅
