# Software Design Document (SDD)
## OSINT Investigation Platform

**Project Name**: Conflict OSINT Framework  
**Version**: 1.0  
**Date**: March 4, 2026  
**Status**: Active Development  

---

## 1. System Overview

The OSINT Investigation Platform is a full-stack web application for open-source intelligence gathering and analysis. It consists of:

- **Backend**: Flask REST API (Python) with SQLAlchemy ORM
- **Frontend**: React SPA (JavaScript/JSX)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Infrastructure**: Docker containerization, optional Kubernetes deployment

The system performs rapid username validation (Light Scan) and comprehensive correlation across 25+ platforms (Deep Scan), constructs relationship networks, calculates risk scores, and generates reports.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer (React)                        │
│  ┌──────────────┬──────────────┬──────────────┬──────────────────┐ │
│  │  Dashboard   │  Case View   │ Graph Viewer │   Settings/Help  │ │
│  └──────────────┴──────────────┴──────────────┴──────────────────┘ │
│                              API Client                             │
└─────────────────────────────────────────────────────────────────────┘
                                   ↕ HTTPS/REST
┌─────────────────────────────────────────────────────────────────────┐
│                      API Layer (Flask Routes)                       │
│  ┌──────────────┬──────────────┬──────────┬──────────────────────┐ │
│  │ Investigation│    Phone     │  Graph   │      Report         │ │
│  │    Routes    │    Routes    │  Routes  │      Routes         │ │
│  └──────────────┴──────────────┴──────────┴──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    Service Layer (Business Logic)                   │
│  ┌──────────────┬──────────────┬──────────┬──────────────────────┐ │
│  │   Analyzer   │Phone Intel   │  Graph   │  Risk Engine        │ │
│  │   (OSINT)    │  Service     │ Engine   │  (Scoring)          │ │
│  └──────────────┴──────────────┴──────────┴──────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Utility Layer (Helpers, Validators)               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   ↕
┌─────────────────────────────────────────────────────────────────────┐
│                     Data Persistence Layer                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │          SQLAlchemy ORM (Database Abstraction)               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │    SQLite (Dev) / PostgreSQL (Prod) Database               │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Backend Architecture

### 3.1 Project Structure

```
backend/
├── app.py                      # Flask application factory & entry point
├── config.py                   # Configuration management (dev/prod)
├── database.py                 # SQLAlchemy & database initialization
├── models.py                   # ORM models (Investigation, Finding, etc.)
│
├── routes/                     # API endpoints (Flask Blueprints)
│   ├── __init__.py
│   ├── investigation_routes.py # /api/investigation/* endpoints
│   ├── phone_routes.py         # /api/phone/* endpoints
│   ├── graph_routes.py         # /api/graph/* endpoints
│   └── report_routes.py        # /api/report/* endpoints
│
├── services/                   # Business logic & orchestration
│   ├── __init__.py
│   ├── analyzer.py             # BehaviorAnalyzer - risk scoring
│   ├── network_builder.py      # NetworkGraphBuilder - Vis.js graphs
│   ├── scraper.py              # OSINTScraper - platform validation
│   ├── phone_intel.py          # PhoneIntelligenceService - phone lookups
│   └── graph_engine.py         # GraphEngineService - advanced analysis
│
├── utils/                      # Utilities & helpers
│   ├── __init__.py
│   ├── response.py             # APIResponse - consistent JSON responses
│   ├── validators.py           # InputValidator - input validation
│   └── helpers.py              # Helper functions
│
├── workers/                    # Background task processing
│   ├── __init__.py
│   └── task_manager.py         # ThreadPoolExecutor task queue
│
├── requirements.txt            # Python dependencies
├── Pipfile                     # Pipenv configuration
└── test_suite.py              # Comprehensive test suite
```

### 3.2 Core Database Models

```python
# Investigation (Case Record)
Investigation
├── id: UUID (Primary Key)
├── username: str (Required)
├── email: str (Optional)
├── phone: str (Optional)
├── status: str (created, running, completed, failed)
├── risk_score: float (0-100)
├── result: JSON (investigation results)
├── error: str (error message if failed)
├── created_at: datetime
└── updated_at: datetime
    └── Relationships: findings[], reports[]

# Finding (Platform Match)
Finding
├── id: UUID
├── investigation_id: UUID (Foreign Key)
├── platform: str (Facebook, Twitter, Instagram, etc.)
├── found: bool
├── username: str
├── profile_url: str
├── metadata: JSON (followers, bio, keywords, emails)
└── created_at: datetime

# Entity (Discovered Entities)
Entity
├── id: UUID
├── investigation_id: UUID
├── entity_type: str (username, email, phone, keyword, mention)
├── value: str
├── source_platform: str
├── confidence: float (0-1.0)
├── discovered_at: datetime
├── metadata: JSON
└── risk_contribution: float

# NetworkEdge (Relationships)
NetworkEdge
├── id: UUID
├── investigation_id: UUID
├── source_id: str (entity ID)
├── target_id: str (entity ID)
├── edge_type: str (MENTIONS, CONNECTED_TO, USES_EMAIL, etc.)
├── weight: float
├── metadata: JSON
└── discovered_at: datetime

# PhoneIntelligence (Cached Phone Data)
PhoneIntelligence
├── id: UUID
├── phone_number: str (unique key)
├── country: str
├── country_code: str
├── region: str
├── carrier: str
├── carrier_type: str (MOBILE, FIXED_LINE, VOIP)
├── timezone: str
├── social_presence: JSON []
├── emails_found: JSON []
├── risk_score: float
├── risk_level: str
├── confidence: float
├── data: JSON (full lookup result)
├── created_at: datetime
└── expires_at: datetime (for cache invalidation)

# Report (Generated Reports)
Report
├── id: UUID
├── investigation_id: UUID
├── report_type: str (pdf, json, text)
├── content: BLOB
├── metadata: JSON
├── generated_at: datetime
└── signed_by: str (optional, for chain-of-custody)

# TaskLog (Audit Trail)
TaskLog
├── id: UUID
├── investigation_id: UUID
├── task_type: str (light_scan, deep_scan, phone_lookup)
├── status: str (pending, running, completed, failed)
├── started_at: datetime
├── completed_at: datetime
└── logs: JSON []
```

### 3.3 API Response Format

**Consistent JSON structure for all endpoints:**

```json
{
  "status": "success|running|completed|error",
  "data": {},
  "meta": {
    "timestamp": "2026-03-04T12:34:56.789Z",
    "version": "1.0",
    "request_id": "uuid"
  },
  "error": null or {"code": "ERR_CODE", "message": "Description"}
}
```

---

## 4. Service Layer Design

### 4.1 PhoneIntelligenceService

**Purpose**: Phone number validation and intelligence extraction using phonenumbers library

**Methods**:

```python
class PhoneIntelligenceService:
    def __init__(self):
        """Initialize with phonenumbers library"""
    
    def lookup(phone_number: str) -> dict:
        """
        Parse and extract phone intelligence
        Input: Phone number in any format
        Output: {valid, number, country, carrier, timezone, 
                 social_presence[], emails[], risk_score, confidence}
        Time: ~200ms for cached, ~2s for fresh lookup
        """
    
    def batch_lookup(phone_numbers: list[str]) -> list[dict]:
        """
        Parallel phone lookups (max 100)
        Returns list of lookup results with same structure as lookup()
        Time: ~5-10s for 100 numbers
        """
    
    def validate_only(phone_number: str) -> dict:
        """
        Fast validation without intelligence extraction
        Output: {valid, formatted, country_code, region_code}
        Time: ~50ms
        """
```

**Risk Calculation Algorithm**:
```
Base Score = 20
If VoIP: +30
If Mobile: +10
If High-Risk Country (KP, IR, SY): +25
For each Social Media: +8 (max 24 for 3 platforms)
For each Associated Email: +5 (max 10 for 2 emails)
Final Score = Min(Total, 100)

Risk Levels:
- CRITICAL: 85-100
- HIGH: 60-84
- MEDIUM: 40-59
- LOW: 20-39
- MINIMAL: 0-19
```

### 4.2 GraphEngineService

**Purpose**: Network graph construction and analysis with Vis.js compatibility

**Methods**:

```python
class GraphEngineService:
    def __init__(self, case_id: str):
        """Initialize graph with case ID"""
    
    def build_from_investigation(investigation: dict, findings: list) -> dict:
        """
        Construct network graph from investigation data
        Input: investigation metadata, list of platform findings
        Output: Vis.js-compatible JSON {nodes[], edges[], metadata, statistics}
        Time: <500ms for 100 nodes
        """
    
    def add_node(node_id: str, node_type: str, label: str, 
                 metadata: dict, risk_score: float) -> None:
        """Add node to graph with auto-coloring and sizing"""
    
    def add_edge(source_id: str, target_id: str, edge_type: str, 
                 metadata: dict, strength: float) -> None:
        """Add relationship edge between nodes"""
    
    def get_statistics() -> dict:
        """
        Compute network metrics
        Output: {node_count, edge_count, density, diameter, avg_degree, is_connected}
        """
    
    def get_connected_nodes(node_id: str, depth: int = 1) -> list:
        """Find nodes within N hops using BFS"""
    
    def get_node_details(node_id: str) -> dict:
        """Get full node info including edges"""
    
    def export_json() -> dict:
        """Export complete graph as JSON"""
    
    def export_graphml() -> str:
        """Export graph in GraphML format for Gephi"""
```

**Node Structure**:
```json
{
  "id": "unique_id",
  "label": "Display Label",
  "type": "profile|platform|email|phone|keyword|mention",
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "size": 38,
  "color": "#FF6B6B",
  "title": "Tooltip text",
  "centrality": 0.65,
  "metadata": {}
}
```

**Edge Structure**:
```json
{
  "from": "source_id",
  "to": "target_id",
  "type": "CONNECTED_TO",
  "label": "Human readable label",
  "color": "#4ECDC4",
  "weight": 5,
  "width": 3.5,
  "metadata": {}
}
```

### 4.3 BehaviorAnalyzer Service

**Purpose**: Risk scoring based on profile behavior and indicators

**Methods**:

```python
class BehaviorAnalyzer:
    def get_risk_score(username: str, profile_data: dict) -> float:
        """
        Calculate risk 0-100 based on keyword indicators
        Factors:
        - Scam keywords (lottery, prize, verify): +25 points
        - Spam reports: +20 points per report
        - Multi-platform presence: +20 points
        - Dangerous keywords (exploit, malware): +25 points
        - Account age: +10 points if recent
        """
    
    def get_risk_category(risk_score: float) -> str:
        """Return CRITICAL|HIGH|MEDIUM|LOW|MINIMAL based on score"""
```

---

## 5. Route Design

### 5.1 Investigation Routes (`/api/investigation/*`)

```python
POST /api/investigation/create
  Input: {username, email?, phone?}
  Output: {status, case_id, investigation}
  Logic: Create case, generate UUID, store in DB

POST /api/investigation/scan/{id}/light
  Input: {case_id}
  Output: {status, findings}
  Logic: Parallel platform checking, non-blocking via ThreadPoolExecutor

POST /api/investigation/scan/{id}/deep
  Input: {case_id, options?}
  Output: {status, findings, graph, risk_score}
  Logic: Sequential scanning phases, background task execution

GET /api/investigation/{id}
  Output: {investigation, status, progress, findings_count}
  Logic: Retrieve from DB, populate metadata

GET /api/investigation/{id}/result
  Output: {investigation, findings[], graph, risk_breakdown, reports[]}
  Logic: Return complete investigation with all data

GET /api/investigation/list
  Output: [{investigation}]
  Logic: Return paginated list of all cases

DELETE /api/investigation/{id}
  Logic: Soft delete with audit log
```

### 5.2 Phone Routes (`/api/phone/*`)

```python
POST /api/phone/lookup
  Input: {phone}
  Output: {valid, number, country, carrier, timezone, risk_score, confidence}
  Logic: Use PhoneIntelligenceService.lookup()

POST /api/phone/batch-lookup
  Input: {phone_numbers: []}
  Output: {count, results: []}
  Logic: Use PhoneIntelligenceService.batch_lookup()

GET /api/phone/validate/{phone}
  Output: {valid, formatted, country_code}
  Logic: Use PhoneIntelligenceService.validate_only()
```

### 5.3 Graph Routes (`/api/graph/*`)

```python
GET /api/graph/{id}
  Output: {nodes[], edges[], metadata, statistics}
  Logic: Use GraphEngineService.build_from_investigation()

GET /api/graph/{id}/statistics
  Output: {node_count, edge_count, density, diameter, avg_degree}

GET /api/graph/{id}/connected/{node_id}
  Query: ?depth=1|2
  Output: [node_ids]
  Logic: Use GraphEngineService.get_connected_nodes()

GET /api/graph/{id}/node/{node_id}
  Output: {node, connected_edges[]}

GET /api/graph/{id}/export/json
  Output: File download (graph.json)

GET /api/graph/{id}/export/graphml
  Output: File download (graph.graphml)
```

### 5.4 Report Routes (`/api/report/*`)

```python
POST /api/report/{id}/generate
  Input: {format: pdf|json|text}
  Output: {status, report_id}
  Logic: Use ReportLab for PDF, json.dumps for JSON

GET /api/report/{id}/pdf
  Output: File download (report.pdf)

GET /api/report/{id}/json
  Output: JSON response

GET /api/report/{id}/text
  Output: Plain text response
```

---

## 6. Frontend Architecture

### 6.1 React Component Hierarchy

```
App.jsx (Root)
├── Header
│   ├── Logo
│   ├── Navigation
│   └── ThemeButton (Dark/Light)
│
├── Sidebar
│   ├── CaseList
│   ├── NewInvestigation
│   └── SearchBar
│
├── Main Content
│   ├── Dashboard (Home)
│   │   ├── Statistics
│   │   ├── RecentCases
│   │   └── QuickActions
│   │
│   ├── CasePage (Individual Case)
│   │   ├── CaseHeader
│   │   ├── FindingsList
│   │   ├── GraphView
│   │   └── ReportSection
│   │
│   ├── NewInvestigation (Case Creation)
│   │   ├── InputForm
│   │   └── ScanOptions
│   │
│   ├── GraphView (Network Visualization)
│   │   ├── Vis.js Network
│   │   ├── LegendPanel
│   │   ├── ControlPanel
│   │   └── ExportButtons
│   │
│   ├── PhoneLookup
│   │   ├── PhoneInput
│   │   ├── ResultsTable
│   │   └── BatchUpload
│   │
│   └── ReportViewer
│       ├── ReportHeader
│       ├── ReportContent
│       └── DownloadButtons
│
└── Footer
    └── Links/Info
```

### 6.2 Component Responsibilities

| Component | Purpose | State |
|-----------|---------|-------|
| **Dashboard** | Home/overview view | Recent cases, statistics |
| **CasePage** | Individual investigation viewer | Investigation data, active tab |
| **GraphView** | Interactive network visualization | Graph data, selected nodes |
| **NewInvestigation** | Case creation wizard | Form inputs, validation |
| **PhoneLookup** | Phone intelligence lookup | Phone input, results |
| **ReportViewer** | Generated report display | Report data, format |
| **Sidebar** | Case navigation | Case list, filters |
| **Header** | Top navigation | Current page, theme |
| **NetworkGraph** | Vis.js graph rendering | Graph structure, options |

### 6.3 State Management

**Using React Context API** (CaseContext):

```javascript
CaseContext {
  cases: [Investigation],
  currentCase: Investigation,
  selectedNode: Node,
  graphData: GraphData,
  loading: boolean,
  error: string,
  
  setCases(),
  setCurrentCase(),
  updateCase(),
  deleteCase(),
  selectNode()
}
```

### 6.4 API Client (`utils/api.js`)

```javascript
// Configuration
const API_BASE = 'http://localhost:5000/api'

// Endpoints
createInvestigation(username, email, phone)
startLightScan(caseId)
startDeepScan(caseId)
getInvestigation(caseId)
getInvestigationResult(caseId)
phoneUniqueLookup(phoneNumber)
phoneBatchLookup(phoneNumbers)
getGraph(caseId)
getGraphStatistics(caseId)
getGraphConnectedNodes(caseId, nodeId, depth)
generateReport(caseId, format)
exportGraph(caseId, format)
```

---

## 7. Data Flow Diagrams

### 7.1 Light Scan Workflow

```
User Input
    ↓
[POST] /api/investigation/create
    ↓
Create Investigation DB Record
    ↓
[POST] /api/investigation/scan/{id}/light
    ↓
OSINTScraper.check_platforms() → ThreadPoolExecutor
    ├─→ Check Facebook
    ├─→ Check Twitter
    ├─→ Check Instagram
    ├─→ ... (10 platforms parallel)
    ↓
Aggregate results → Finding records in DB
    ↓
[GET] /api/investigation/{id}/result
    ↓
Return findings to user
```

### 7.2 Deep Scan Workflow

```
[POST] /api/investigation/scan/{id}/deep
    ↓
TaskManager.submit_task(deep_scan_job)
    ↓
Phase 1: Platform Scanning (Parallel)
    ├─→ OSINTScraper.check_platforms()
    
Phase 2: Data Extraction (Sequential)
    ├─→ Extract usernames
    ├─→ Extract emails
    └─→ Extract keywords
    
Phase 3: Graph Building (Sequential)
    ├─→ GraphEngineService.build_from_investigation()
    └─→ Create network visualization
    
Phase 4: Risk Scoring (Sequential)
    ├─→ BehaviorAnalyzer.get_risk_score()
    └─→ Compute aggregate risk
    
Phase 5: Report Generation (Sequential)
    └─→ ReportLab PDF generation
    
    ↓
Store all findings in DB
    ↓
Update case status → "completed"
    ↓
User polls [GET] /api/investigation/{id}/result
    ↓
Return complete investigation data
```

### 7.3 Phone Intelligence Workflow

```
[POST] /api/phone/lookup
    ↓
PhoneIntelligenceService.lookup(phone_number)
    ↓
Check cache (PhoneIntelligence DB table)
    ╱─→ Cache hit: Return cached result
    
    ╲─→ Cache miss:
        ├─→ phonenumbers.parse(phone_number)
        ├─→ Extract country, carrier, timezone
        ├─→ Check social presence
        ├─→ Calculate risk_score
        ├─→ Calculate confidence
        ├─→ Cache result in DB
        └─→ Return result
    
    ↓
[JSON Response]
{
  valid: bool,
  number: formatted,
  country: str,
  carrier: str,
  timezone: str,
  risk_score: 0-100,
  confidence: 0-1.0
}
```

### 7.4 Graph Construction Workflow

```
[GET] /api/graph/{id}
    ↓
GraphEngineService.build_from_investigation(investigation, findings)
    ↓
Create central node (primary entity)
    ↓
For each finding:
    ├─→ Create platform node
    ├─→ Add edge (CONNECTED_TO)
    ├─→ Extract emails → Create email nodes
    ├─→ Extract keywords → Create keyword nodes
    ├─→ Create edges with metadata
    
    ↓
Calculate metrics (NetworkX):
    ├─→ Betweenness centrality
    ├─→ Degree centrality
    ├─→ Density
    └─→ Average clustering
    
    ↓
Assign colors/sizes based on risk
    
    ↓
Format as Vis.js JSON:
{
  nodes: [{id, label, type, size, color, ...}],
  edges: [{from, to, type, weight, color, ...}],
  metadata: {...},
  statistics: {...}
}
    
    ↓
Return to frontend
    
    ↓
React: Render via vis-react component
```

---

## 8. Security Architecture

### 8.1 Authentication & Authorization

```
Frontend
    ↓ sends request with Bearer token
    ↓
Flask Middleware (check_auth)
    ├─→ Extract token from Authorization header
    ├─→ Verify JWT signature
    ├─→ Check expiration
    └─→ Attach user context to request
    
    ├─ Valid: Allow through to route
    └─ Invalid: Return 401 Unauthorized
```

### 8.2 Input Validation Pipeline

```
HTTP Request
    ↓
Flask Route Handler
    ↓
Validator.validate_input(data, schema)
    ├─→ Check required fields present
    ├─→ Validate data types
    ├─→ Validate format (email, phone, uuid)
    ├─→ Check range/length constraints
    └─→ Reject if invalid → 400 Bad Request
    ↓
Service Layer (Business Logic)
    ↓
Database
```

### 8.3 SQL Injection Prevention

- **Method**: SQLAlchemy ORM parameterized queries
- **Never**: String concatenation in SQL
- **Always**: Use model methods and query API

```python
# Bad (VULNERABLE)
result = db.session.execute(f"SELECT * FROM investigation WHERE id = '{case_id}'")

# Good (SAFE)
result = Investigation.query.filter_by(id=case_id).first()
```

### 8.4 Data Encryption

**Transport**:
- HTTPS/TLS 1.2+ required in production

**At Rest**:
- Sensitive columns encrypted at database level (optional)
- Phone numbers: Mask in logs except last 4 digits

**Secrets**:
- API keys in environment variables
- Database credentials from .env
- Never commit secrets to repository

---

## 9. Deployment Architecture

### 9.1 Development Environment

```
Laptop/Workstation
├── Backend: Flask dev server (port 5000)
├── Frontend: npm dev server (port 3000)
└── Database: SQLite (file-based)
```

### 9.2 Production Environment

```
┌─────────────────────────────────────────────┐
│          Cloud Provider (AWS/GCP/Azure)     │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │      Reverse Proxy (nginx)           │  │
│  │      Port 443 (HTTPS)                │  │
│  └──────────────────────────────────────┘  │
│             ↓                                 │
│  ┌──────────────────────────────────────┐  │
│  │   Load Balancer (Kubernetes Service) │  │
│  └──────────────────────────────────────┘  │
│             ↓                                 │
│  ┌──────────────────────────────────────┐  │
│  │     Flask Pods (containerized)       │  │
│  │  Pod 1    Pod 2    Pod 3    Pod 4    │  │
│  └──────────────────────────────────────┘  │
│             ↓                                 │
│  ┌──────────────────────────────────────┐  │
│  │     PostgreSQL Database              │  │
│  │     (with automatic backups)         │  │
│  └──────────────────────────────────────┘  │
│             ↓                                 │
│  ┌──────────────────────────────────────┐  │
│  │    Cloud Storage (logs, reports)     │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘

Frontend: Served via CDN (CloudFront, Cloudflare)
```

### 9.3 Docker Configuration

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_ENV=production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "60", "app:app"]
```

### 9.4 Kubernetes Deployment

```yaml
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: osint-backend
spec:
  replicas: 4
  selector:
    matchLabels:
      app: osint-backend
  template:
    metadata:
      labels:
        app: osint-backend
    spec:
      containers:
      - name: flask
        image: osint-backend:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: postgres-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

---

## 10. Performance Optimization

### 10.1 Caching Strategy

**Level 1: Database Caching**
- PhoneIntelligence table caches lookups with 24-hour TTL
- Query: Check cache before external API call

**Level 2: Application Caching**
- Memoized graph statistics for 24 hours
- Risk score cache per username (invalidates on update)

**Level 3: Frontend Caching**
- React component state for current case
- LocalStorage for user preferences
- HTTP cache headers (ETag, Last-Modified)

### 10.2 Concurrent Processing

**Light Scans**:
```python
ThreadPoolExecutor(max_workers=10).map(
    check_platform,
    PLATFORMS_LIST
)
# Parallel platform checking, ~10 seconds for 25 platforms
```

**Deep Scans**:
```
Phase 1: Parallel (10 workers) → Platform checking
Phase 2: Sequential → Data extraction & correlation
Phase 3: Sequential → Graph building
Phase 4: Sequential → Risk scoring
Phase 5: Sequential → Report generation
```

### 10.3 Database Indexing

```sql
-- Investigation lookups
CREATE INDEX idx_investigation_username ON investigation(username);
CREATE INDEX idx_investigation_status ON investigation(status);

-- Finding lookups
CREATE INDEX idx_finding_investigation ON finding(investigation_id);
CREATE INDEX idx_finding_platform ON finding(platform);

-- Entity lookups
CREATE INDEX idx_entity_investigation ON entity(investigation_id);
CREATE INDEX idx_entity_type ON entity(entity_type);

-- Phone caching
CREATE INDEX idx_phone_number ON phone_intelligence(phone_number);
CREATE INDEX idx_phone_expires ON phone_intelligence(expires_at);
```

---

## 11. Error Handling Strategy

### 11.1 Error Classification

**Client Errors (4xx)**:
- 400: Bad Request (validation failed)
- 401: Unauthorized (missing/invalid auth)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (case/resource doesn't exist)

**Server Errors (5xx)**:
- 500: Internal Server Error (unexpected exception)
- 503: Service Unavailable (database down, etc.)

### 11.2 Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PHONE_FORMAT",
    "message": "Phone number failed validation",
    "details": {
      "input": "+1234",
      "reason": "Too short for any valid number"
    }
  },
  "meta": {
    "timestamp": "2026-03-04T12:34:56Z",
    "request_id": "uuid"
  }
}
```

### 11.3 Retry Logic

**For External API Calls**:
```python
@retry(max_attempts=3, backoff_factor=2, timeout=30)
def fetch_platform_data(platform_url):
    """
    Attempt 1: Immediate
    Attempt 2: After 2 seconds
    Attempt 3: After 4 seconds
    Fail: Gracefully return empty result
    """
```

---

## 12. Testing Strategy

### 12.1 Unit Tests

```python
# test_services.py
TestPhoneIntelligenceService: 11 test methods
├─ test_lookup_valid_us_number
├─ test_lookup_international_formats
├─ test_batch_lookup
├─ test_risk_scoring
└─ ...

TestGraphEngineService: 12 test methods
├─ test_build_from_investigation
├─ test_add_node
├─ test_statistics_calculation
└─ ...

TestValidators: Input validation tests
TestHelpers: Utility function tests
```

### 12.2 Integration Tests

```python
TestAPIIntegration
├─ test_create_investigation
├─ test_light_scan_workflow
├─ test_phone_lookup_and_save
├─ test_graph_generation
└─ test_report_generation
```

### 12.3 End-to-End Tests

```javascript
// frontend/cypress/integration/
describe('Investigation Workflow', () => {
  it('Should complete full light scan', () => {
    cy.visit('/')
    cy.createInvestigation('testuser')
    cy.startLightScan()
    cy.verifyResults()
  })
})
```

---

## 13. Monitoring & Logging

### 13.1 Application Logging

```python
import logging

logger = logging.getLogger(__name__)

# Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.info(f"Starting investigation: {case_id}")
logger.warning(f"Platform check timeout: {platform}")
logger.error(f"Database error: {exception}")
```

### 13.2 Metrics to Monitor

```
Performance:
- API response time (95th percentile)
- Investigation completion time
- Phone lookup latency
- Graph construction time

Reliability:
- Error rate (4xx, 5xx)
- Failed task attempts
- Database connection pool usage
- Background task queue depth

Capacity:
- Active concurrent investigations
- Database disk usage
- API request rate
- Memory usage per container
```

### 13.3 Alerting Thresholds

- Response time > 2 seconds: Warning
- Error rate > 1%: Alert
- Database connection pool > 80%: Warning
- Disk usage > 90%: Critical

---

## 14. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial SDD creation - System design documented |

---

## 15. Appendices

### A. Third-Party Dependencies

**Backend**:
- Flask (2.3.0+): Web framework
- SQLAlchemy (3.0.0+): ORM
- phonenumbers: Phone parsing
- networkx: Graph algorithms
- requests: HTTP client
- beautifulsoup4: HTML parsing
- reportlab: PDF generation
- gunicorn: Production WSGI server

**Frontend**:
- react (18.0+): UI framework
- vis-react: Graph visualization
- axios: HTTP client
- lucide-react: Icons

### B. Configuration Management

**Environment Variables**:
```bash
# Backend
FLASK_ENV=development|production
FLASK_DEBUG=True|False
DATABASE_URL=postgresql://user:pass@localhost/osint_db
SECRET_KEY=<generated-secret>
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# Frontend
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENV=development|production
```

### C. API Rate Limiting

```python
# Per IP: 100 requests per minute
# Per user: 1000 requests per hour
# Investigation creation: 10 per hour
# Phone lookup: 100 per hour
```

---

**Document Version**: 1.0  
**Last Updated**: March 4, 2026  
**Status**: Complete  

**Approval**:
- Technical Lead: ___________________ Date: _____
- Architecture Review: ___________________ Date: _____
