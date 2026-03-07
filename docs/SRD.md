# Software Requirements Document (SRD)
## OSINT Investigation Platform

**Project Name**: Conflict OSINT Framework  
**Version**: 1.0  
**Date**: March 4, 2026  
**Status**: Active Development  

---

## 1. Executive Summary

The **OSINT Investigation Platform** is a military-grade intelligence gathering and analysis system designed for comprehensive open-source intelligence operations. It enables investigators to:

- Perform rapid username validations (Light Scan - ~10 seconds)
- Execute comprehensive investigations (Deep Scan - 2-5 minutes)
- Correlate entities across multiple platforms
- Visualize relationship networks
- Calculate risk scores based on aggregated indicators
- Generate structured investigation reports

The system integrates Flask backend APIs with a React frontend, supporting both automated batch processing and interactive investigation workflows.

---

## 2. Functional Requirements

### 2.1 Investigation Management

#### FR-1: Create Investigation Case
- **Description**: Users must be able to create a new investigation case with initial parameters
- **Input**: Username, email (optional), phone number (optional)
- **Output**: Unique case ID, initial metadata, status
- **Acceptance Criteria**:
  - Case stored in database with UUID identifier
  - Status set to 'created'
  - Timestamp recorded
  - Users can reference case by ID

#### FR-2: Light Scan Operation
- **Description**: Execute quick validation of username across platforms (≤10 seconds)
- **Input**: Case ID, optional platform filter
- **Output**: List of found platforms with basic metadata
- **Acceptance Criteria**:
  - Completes within 10 seconds
  - Checks minimum 10 platforms (Facebook, Twitter, Instagram, LinkedIn, GitHub, TikTok, YouTube, Twitch, Reddit, Telegram)
  - Returns platform name, URL, and status (found/not found)
  - Non-blocking execution

#### FR-3: Deep Scan Operation
- **Description**: Execute comprehensive investigation with full correlation (2-5 minutes)
- **Input**: Case ID, scan options (threading level, depth)
- **Output**: Complete entity graph, risk score, findings list
- **Acceptance Criteria**:
  - Completes within 5 minutes for standard case
  - Discovers usernames, emails, phone numbers
  - Extracts keywords and mentions
  - Builds correlation graph
  - Calculates aggregate risk score
  - Generates intermediate reports

#### FR-4: Investigation Status Tracking
- **Description**: Monitor investigation progress and retrieve real-time status
- **Input**: Case ID
- **Output**: Current status, progress percentage, findings count, error logs
- **Acceptance Criteria**:
  - Updates every 5 seconds during active scan
  - Maintains audit log of all phases
  - Reports errors with context
  - Handles cancellation requests

#### FR-5: Investigation Retrieval
- **Description**: Retrieve completed investigation results
- **Input**: Case ID
- **Output**: Full results including findings, graph, risk score, metadata
- **Acceptance Criteria**:
  - Returns within 1 second
  - Includes all discovered entities
  - Contains graph structure with edges and metadata
  - Provides risk breakdown by category

### 2.2 Phone Intelligence

#### FR-6: Single Phone Lookup
- **Description**: Extract comprehensive intelligence from single phone number
- **Input**: Phone number in any format (+1234567890, (202) 555-1234, etc)
- **Output**: Country, carrier, timezone, risk score, social presence (if found)
- **Acceptance Criteria**:
  - Supports international formats (E.164, national, local)
  - Validates phone number format and region
  - Returns in <200ms for cached results
  - Handles 10 fallback regions (US, GB, ID, IN, BR, RU, DE, FR, IT, ES)
  - Identifies carrier and network type (MOBILE, FIXED_LINE, VOIP, UNKNOWN)
  - Filters high-risk providers (known VoIP masking services)

#### FR-7: Batch Phone Lookup
- **Description**: Process multiple phone numbers in single request
- **Input**: List of phone numbers (max 100)
- **Output**: Array of individual lookup results
- **Acceptance Criteria**:
  - Processes up to 100 numbers per request
  - Completes within 5-10 seconds for 100 numbers
  - Returns consistent structure for each number
  - Partial failure handling (one failure doesn't block others)

#### FR-8: Phone Validation Only
- **Description**: Fast validation without full intelligence extraction
- **Input**: Phone number string
- **Output**: Validity, formatted number, country code, region code
- **Acceptance Criteria**:
  - Completes within 50ms
  - Uses phonenumbers library validation
  - Returns no carrier/timezone/social data
  - Lightweight for pre-filtering

#### FR-9: Risk Score Calculation
- **Description**: Compute numerical risk (0-100) based on phone attributes
- **Input**: Phone number metadata (carrier, country, social presence, email associations)
- **Output**: Risk score (0-100), risk level (CRITICAL/HIGH/MEDIUM/LOW/MINIMAL), confidence (0-1.0)
- **Acceptance Criteria**:
  - Base score: 20 (5% countries have legitimate presence)
  - +30 if VoIP (highest risk category)
  - +10 if mobile network (potential burner/temporary)
  - +25 if high-risk country (KP, IR, SY, etc)
  - +8 per social media platform (max 24 points for 3 platforms)
  - +5 per associated email (max 10 points for 2 emails)
  - Final score capped at 100
  - Confidence: 0.2 base + 0.25×social_presence + 0.3×emails_found + 0.25×carrier_confidence

### 2.3 Network Graph Analysis

#### FR-10: Graph Construction
- **Description**: Build relationship network from investigation findings
- **Input**: Investigation data (central entity, findings from platforms)
- **Output**: Vis.js-compatible JSON with nodes, edges, metadata, statistics
- **Acceptance Criteria**:
  - Central node represents primary entity
  - Separate node type for each platform
  - Additional nodes for extracted emails, phones, keywords
  - Creates edges based on relationship type
  - Assigns colors and sizes based on type and risk
  - Calculates centrality metrics

#### FR-11: Edge Type System
- **Description**: Support multiple relationship types with semantic meaning
- **Relationship Types**:
  - `MENTIONS`: Username mentioned, tagged, or quoted (weight: 1)
  - `CONNECTED_TO`: Direct follow/connection (weight: 5)
  - `USES_EMAIL`: Account uses same email address (weight: 3)
  - `USES_PHONE`: Account uses same phone number (weight: 4)
  - `POSTED_KEYWORD`: Posted specific keyword/phrase (weight: 2)
  - `REPORTED_AS`: Reported as spam, fake, or compromised (weight: 6)
  - `SIMILAR_USERNAME`: Username pattern similarities (weight: 2)
- **Acceptance Criteria**:
  - Each edge has type, weight, color, and description
  - Color coding: MENTIONS=#FF6B6B, CONNECTED_TO=#4ECDC4, USES_EMAIL=#95E1D3, etc.
  - Weights influence graph layout and visualization

#### FR-12: Graph Statistics
- **Description**: Compute network analysis metrics
- **Metrics**:
  - Node count (total entities)
  - Edge count (total relationships)
  - Density (connectivity ratio, 0-1)
  - Average clustering coefficient (how grouped)
  - Average degree (connections per node)
  - Diameter (longest shortest path)
  - Connected components (subnetworks)
- **Acceptance Criteria**:
  - Computed using NetworkX library
  - Return within 500ms for graphs <500 nodes
  - Handle disconnected graphs gracefully

#### FR-13: Graph Export
- **Description**: Export graph in multiple formats
- **Formats**:
  - JSON (Vis.js format for frontend rendering)
  - GraphML (for Gephi, Cytoscape, desktop tools)
  - GML (Graph Modelling Language)
- **Acceptance Criteria**:
  - JSON export preserves all node/edge/metadata
  - GraphML export valid for all desktop tools
  - File size <5MB for standard investigations
  - Complete in <2 seconds

### 2.4 Risk Scoring

#### FR-14: Aggregate Risk Calculation
- **Description**: Compute overall investigation risk (0-100)
- **Input**: All findings, phone data, graph metrics, entity counts
- **Scoring Factors**:
  - Scam keywords in profiles (25% weight): Keywords like "lottery", "prize", "verify account"
  - Spam/abuse reports (20% weight): Number of platforms reporting
  - Multi-platform presence (20% weight): More platforms = higher score
  - Dangerous keywords (25% weight): "exploit", "malware", "ransomware", etc.
  - Account age (10% weight): Newer accounts = higher score
- **Acceptance Criteria**:
  - Final score between 0-100
  - Weighted average of factors
  - Risk level assigned: CRITICAL (85-100), HIGH (60-84), MEDIUM (40-59), LOW (20-39), MINIMAL (0-19)
  - Detailed breakdown provided per category

#### FR-15: Risk Category Breakdown
- **Description**: Provide itemized risk by category
- **Output**: 
  ```json
  {
    "overall_score": 55,
    "overall_level": "MEDIUM",
    "breakdown": {
      "scam_keywords": {"score": 20, "weight": 0.25, "weighted": 5},
      "spam_reports": {"score": 0, "weight": 0.20, "weighted": 0},
      "multi_platform": {"score": 50, "weight": 0.20, "weighted": 10},
      "dangerous_keywords": {"score": 30, "weight": 0.25, "weighted": 7.5},
      "account_age": {"score": 80, "weight": 0.10, "weighted": 8}
    }
  }
  ```
- **Acceptance Criteria**:
  - All categories detailed in response
  - Calculations transparent and verifiable
  - Includes explanation per category

### 2.5 Report Generation

#### FR-16: PDF Report Generation
- **Description**: Generate formatted PDF investigation report
- **Content**:
  - Investigation header (case ID, date, duration)
  - Executive summary with risk assessment
  - Entities discovered (usernames, emails, phones)
  - Network graph visualization
  - Risk scoring breakdown
  - Timeline of discovery
  - Chain-of-custody log
- **Acceptance Criteria**:
  - Generates within 5 seconds
  - PDF valid and viewable in standard readers
  - File size <2MB
  - Includes all key findings

#### FR-17: JSON Report Export
- **Description**: Export investigation as JSON for programmatic access
- **Content**: Complete investigation data, all findings, graphs, metrics
- **Acceptance Criteria**:
  - Valid JSON format
  - Includes metadata (creation time, version, format)
  - Suitable for re-import or processing

#### FR-18: Text Report Generation
- **Description**: Generate plain-text summary report
- **Content**: Summary of findings, key entities, risk score
- **Acceptance Criteria**:
  - Readable without special software
  - All critical findings included
  - ~1-2 page summary

---

## 3. Non-Functional Requirements

### 3.1 Performance

#### NFR-1: Response Time
- **Light scan**: Completes within 10 seconds
- **Deep scan**: Completes within 5 minutes
- **Phone lookup**: Returns within 200ms (cached) or 2 seconds (fresh)
- **Graph construction**: <500ms for 100 nodes
- **API response**: <1 second at 50th percentile, <2 seconds at 95th percentile
- **Report generation**: <5 seconds

#### NFR-2: Throughput
- **Concurrent investigations**: Support 10+ simultaneous active scans
- **Phone lookups**: Handle 100+ batch operations concurrently
- **API requests**: Process 50+ requests/second without degradation

#### NFR-3: Scalability
- **Database**: Support 100,000+ investigation records
- **Graphs**: Handle networks up to 10,000 nodes
- **Horizontal scaling**: Backend services deployable across multiple instances

### 3.2 Reliability

#### NFR-4: Availability
- **Target uptime**: 99.5% (SLA)
- **MTBF**: 720+ hours between failures
- **MTTR**: <30 minutes for service recovery

#### NFR-5: Error Handling
- **Graceful degradation**: Partial failures don't block workflow
- **Fallback logic**: Default regions for phone parsing, timeout defaults
- **Retry logic**: Exponential backoff for external API calls
- **Error reporting**: Clear error codes and messages

#### NFR-6: Data Integrity
- **Transaction support**: Database operations ACID-compliant
- **Audit logging**: All modifications logged with timestamp and user
- **Backup strategy**: Daily automated backups

### 3.3 Security

#### NFR-7: Input Validation
- **All external inputs**: Validated against whitelist / format patterns
- **SQL injection prevention**: Parameterized queries via SQLAlchemy ORM
- **XSS prevention**: Output encoding in JSON responses
- **Path traversal**: No user-controlled path construction

#### NFR-8: Access Control
- **API authentication**: Bearer token or API key required
- **Authorization**: Role-based access to investigation resources
- **Rate limiting**: User and IP-based request throttling
- **CORS**: Restricted to known frontend origins

#### NFR-9: Data Privacy
- **Sensitive data**: Phone numbers masked in logs (except last 4 digits)
- **PII handling**: Compliance with data protection principles
- **Audit trail**: All access logged with timestamp and actor

#### NFR-10: Encryption
- **Transport**: HTTPS/TLS 1.2+ required
- **At rest**: Database and file storage encryption (AES-256)
- **Secrets management**: API keys and credentials in environment variables

### 3.4 Usability

#### NFR-11: User Interface
- **Responsive design**: Works on desktop, tablet, mobile
- **Dark/light mode**: Theme toggle per user preference
- **Intuitive navigation**: Clear menu hierarchy
- **Progress indication**: Real-time status during scans

#### NFR-12: Documentation
- **API documentation**: OpenAPI/Swagger specs
- **Code documentation**: Docstrings on all public functions
- **User guide**: Step-by-step investigation workflow
- **Video tutorials**: Key features demonstrated

### 3.5 Maintainability

#### NFR-13: Code Quality
- **Linting**: flake8 and black formatting
- **Type hints**: Type annotations on function signatures
- **Test coverage**: Minimum 70% coverage
- **Code review**: All changes reviewed before merge

#### NFR-14: Deployment
- **Containerization**: Docker support for all components
- **Infrastructure as Code**: Deployment scripts/configs
- **CI/CD**: Automated testing and deployment
- **Version management**: Semantic versioning

---

## 4. System Requirements

### 4.1 Hardware

**Minimum**:
- CPU: 2 cores (2.0 GHz)
- RAM: 4 GB
- Storage: 20 GB
- Network: 10 Mbps connection

**Recommended**:
- CPU: 4+ cores (2.5+ GHz)
- RAM: 8-16 GB
- Storage: 100 GB SSD
- Network: 100+ Mbps connection

### 4.2 Software

**Backend**:
- Python 3.9+
- Flask 2.3.0+
- SQLAlchemy 3.0.0+
- PostgreSQL 12+ or SQLite 3.35+

**Frontend**:
- Node.js 18.0+
- React 18.0+
- npm 9.0+ or yarn 1.22+

**External Services**:
- phonenumbers library (phone parsing)
- NetworkX (graph analysis)
- Requests library (HTTP client)
- BeautifulSoup4 (HTML parsing)
- ReportLab (PDF generation)

### 4.3 Deployment Platforms

**Supported**:
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- macOS (10.15+)
- Windows Server 2019+
- Docker/Kubernetes environments
- AWS, GCP, Azure cloud platforms

---

## 5. Constraints and Assumptions

### 5.1 Constraints

- **Investigation scope**: Focus on public data only, no authenticated APIs
- **Platform support**: ~25 major platforms (extensible list)
- **Scan duration**: Deep scans limited to 5 minutes max
- **Graph complexity**: Limit to 10,000 node graphs for performance
- **Report size**: PDF reports limited to 100 pages
- **API rate limits**: Must respect platform rate limits (backoff strategy)

### 5.2 Assumptions

- **Public data**: All investigated data is publicly available
- **User authorization**: Users authorized to investigate target entities
- **Platforms stable**: Social media APIs and HTML structure stable during operation
- **Network connectivity**: Reliable internet connection available
- **Legal compliance**: Users responsible for compliance with applicable laws
- **Database availability**: Database accessible during operation

---

## 6. Use Cases

### UC-1: Username Investigation
1. User enters username and initiates Light Scan
2. System checks 25 platforms for existence
3. Results displayed to user showing found/not found per platform
4. User can upgrade to Deep Scan for full investigation

### UC-2: Suspect Profile Creation
1. User creates new investigation with email and phone
2. System performs phone intelligence lookup
3. Phone data integrated with initial risk calculation
4. User launches Deep Scan

### UC-3: Batch Phone Lookup
1. User uploads CSV with 100 phone numbers
2. System parallelizes batch lookup
3. Results returned showing carrier, timezone, risk per number
4. User exports results as CSV or PDF report

### UC-4: Network Analysis
1. After investigation, user views network graph
2. System displays interactive graph with nodes and edges
3. User can highlight paths, calculate centrality, filter by edge type
4. User exports graph as GraphML for Gephi analysis

### UC-5: Report Generation
1. After investigation, user requests PDF report
2. System generates formatted report with findings, graph, risk breakdown
3. User downloads PDF or shares investigation JSON link
4. Report includes chain-of-custody for legal admissibility

---

## 7. Acceptance Criteria

### Functional Verification
- [ ] Light scan completes within target time (10 seconds)
- [ ] Deep scan discovers expected entities and relationships
- [ ] Phone lookup returns accurate carrier and timezone data
- [ ] Risk scores consistent across multiple runs with same input
- [ ] Graphs valid in Vis.js and visualize correctly
- [ ] PDF reports generate without errors and contain all fields
- [ ] Batch operations complete with partial failure handling

### Non-Functional Verification
- [ ] Load testing: 10 concurrent investigations without degradation
- [ ] Response time: 95th percentile <2 seconds for API calls
- [ ] Error handling: 100% of expected exceptions handled gracefully
- [ ] Security: SQL injection, XSS, path traversal tests pass
- [ ] Data integrity: Transaction consistency verified
- [ ] Code coverage: Minimum 70% unit test coverage

---

## 8. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial SRD creation |

---

## 9. Approval

- **Client**: ___________________ Date: _____
- **Project Lead**: ___________________ Date: _____
- **Technical Lead**: ___________________ Date: _____

---

**Document Version**: 1.0  
**Last Updated**: March 4, 2026  
**Status**: Complete
