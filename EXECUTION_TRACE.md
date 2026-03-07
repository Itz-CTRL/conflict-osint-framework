# OSINT System: Complete Request Execution Trace

## Request Flow: Phone Lookup (`/api/phone/lookup`)

### STEP 1: Frontend Initiates Request
**File:** `frontend/src/components/PhoneLookup.jsx`  
**Component Method:** `handleLookup()` (line ~27)

```javascript
// User enters: "+233 24XXXX XXXX"
const num = phone.trim();
const res = await api.phoneLookup(num);
```

### STEP 2: API Layer Formats Request
**File:** `frontend/src/utils/api.js`  
**Function:** `api.phoneLookup()` (line ~64)

```javascript
phoneLookup: (phone, countryCode = null, scanType = 'light') =>
  apiFetch('/api/phone/lookup', {
    method: 'POST',
    body: JSON.stringify({ 
      phone_number: phone,           // ← Phone goes here
      country_code: countryCode,     // ← Optional
      scan_type: scanType            // ← Default: 'light'
    }),
  })
```

**JSON Payload Sent:**
```json
{
  "phone_number": "+233 24XXXX XXXX",
  "country_code": null,
  "scan_type": "light"
}
```

### STEP 3: HTTP Request Reaches Flask Backend
**URL:** `POST http://127.0.0.1:5000/api/phone/lookup`  
**Route Registration:** `app.py` lines 56-62

```python
# Blueprint registered with prefix
app.register_blueprint(phone_bp)  # Uses url_prefix='/api/phone'

# So route is: /api/phone/lookup
```

### STEP 4: Route Handler Processes Request
**File:** `backend/routes/phone_routes.py`  
**Function:** `lookup_phone()` (line 220)  
**Blueprint:** `phone_bp` with prefix `/api/phone`

```python
@phone_bp.route('/lookup', methods=['POST'])  # Full path: /api/phone/lookup
def lookup_phone():
    try:
        data = request.get_json()  # ← Reads: { phone_number, country_code, scan_type }
        
        original_phone = data.get('phone_number')   # "+233 24XXXX XXXX"
        country_input = data.get('country_code')    # None
        scan_type = data.get('scan_type', 'light')  # "light"
        
        logger.info(f"[PHONE_LOOKUP] Input: phone={original_phone}, country={country_input}, scan_type={scan_type}")
        
        # Validate phone provided
        if not original_phone:
            return jsonify(APIResponse.error(None, "Phone number is required")), 400
        
        # Validate scan type
        is_valid, error = Validator.validate_scan_type(scan_type)
        if not is_valid:
            return jsonify(APIResponse.error(None, error)), 400
```

### STEP 5: Phone Normalization
**File:** `backend/utils/validators.py`  
**Function:** `Validator.normalize_phone_number()` (line ~165)

```python
def normalize_phone_number(phone_number, country_code):
    """
    Normalize phone: "+233 24XXXX XXXX" → "+233 24XXXX XXXX" (international format)
    
    Tries 6 strategies:
    1. Direct parse with no region
    2. Parse with explicit country_code (if provided)
    3. Add + prefix if missing
    4. Try common regions (GH first if country_code provided)
    5. Clean to digits and retry regions
    6. Fallback (never returns None)
    """
    # Returns: "+233 24XXXX XXXX"
```

### STEP 6: Call Phone Intelligence Service
**File:** `backend/routes/phone_routes.py` (lines ~270)  
**Service:** `phone_intel.py`

```python
normalized_phone = Validator.normalize_phone_number(original_phone, country_input)
# Result: normalized_phone = "+233 24XXXX XXXX"

logger.info(f"[PHONE_LOOKUP] Normalized: {original_phone} → {normalized_phone}")

# Call service
try:
    result = phone_intel_service.lookup(normalized_phone, country_input, scan_type)
except Exception as e:
    logger.error(f"[PHONE_LOOKUP] Service error: {str(e)}")
    result = {safe_empty_result}  # Graceful fallback
```

### STEP 7: Phone Intelligence Service Execution
**File:** `backend/services/phone_intel.py`  
**Function:** `lookup(phone, country_code, scan_type)`

```python
def lookup(phone, country_code, scan_type):
    """
    Performs phone intelligence lookup with light or deep scan.
    Returns guaranteed structure: { 'status', 'findings', 'data', 'graph' }
    """
    try:
        # Phone parsing and validation
        parsed_phone = parse_phone(phone)  # Extracts country, (area code, etc.
        
        if scan_type == 'deep':
            # Calls scraper.py to find social profiles
            result = scraper.search_profiles(phone)
        else:
            # Light scan: basic lookup only
            result = extract_phone_metadata(phone)
        
        return {
            'status': 'success',
            'findings': result,
            'data': {'number': phone, 'carrier': ..., 'timezone': ...},
            'graph': {'nodes': [], 'edges': []}
        }
    except Exception as e:
        logger.error(f"Phone lookup error: {str(e)}")
        return {
            'status': 'failed',
            'findings': [],
            'data': {},
            'graph': {'nodes': [], 'edges': []}
        }
```

### STEP 8: Threat Scoring (if dark findings exist)
**File:** `backend/services/analyzer.py`  
**Function:** `analyze()`

```python
def analyze(username, platform_results, detailed_data):
    """
    CRITICAL: Only assigns threat if real findings exist.
    If findings empty → risk_score = 0 ALWAYS.
    """
    try:
        # Check for real findings first
        has_real_findings = (
            len(report.get('platform_presence', {}).get('found_on', [])) > 0 or
            len(report.get('keyword_hits', [])) > 0 or
            len(report.get('behavior_flags', [])) > 0 or
            len(report.get('findings', [])) > 0
        )
        
        if not has_real_findings:
            logger.info(f"[THREAT_SCORING] No real findings, setting risk_score=0")
            report['risk_score'] = 0
            report['risk_level'] = 'LOW'
            report['findings'] = []
            return report  # ← Exit early with zero threat
        
        # Only continue if findings exist...
```

### STEP 9: Save to Database
**File:** `backend/routes/phone_routes.py` (lines ~280)

```python
try:
    # Save phone intelligence record
    phone_intel = PhoneIntelligence(
        phone_number=normalized_phone,
        country=country_iso,
        findings=findings_count,
        risk_score=threat_level
    )
    db.session.add(phone_intel)
    db.session.commit()
    logger.info(f"[PHONE_LOOKUP] Saved to DB: {normalized_phone}")
except Exception as e:
    logger.warning(f"[PHONE_LOOKUP] DB save failed (non-critical): {str(e)}")
    db.session.rollback()
```

### STEP 10: Return Response to Frontend
**File:** `backend/routes/phone_routes.py` (lines ~340)

```python
# Build standardized response
response = {
    'status': 'completed',
    'target': normalized_phone,
    'findings': findings_data,
    'threat_level': threat_score,
    'network_nodes': graph_nodes,
    'network_edges': graph_edges
}

logger.info(f"[PHONE_LOOKUP] Returning response: threat_level={response['threat_level']}")
return jsonify(response), 200  # ← Always 200, safe JSON
```

**JSON Response to Frontend:**
```json
{
  "status": "completed",
  "target": "+233 24XXXX XXXX",
  "findings": {
    "carrier": "Vodafone",
    "country": "Ghana",
    "number_type": "mobile",
    "platforms": []
  },
  "threat_level": 0,
  "network_nodes": [],
  "network_edges": []
}
```

### STEP 11: Frontend Receives Response
**File:** `frontend/src/components/PhoneLookup.jsx` (line ~32)

```javascript
const res = await api.phoneLookup(num);
setResult(res.data || {});  // ← Parse response
addPhoneLookup(res.data || {});
setLoading(false);
```

---

## Request Flow: Investigation Scan (`/api/investigation/scan/:caseId/:scanType`)

### Similar flow:
1. Frontend initiates: `api.startScan(case_id, 'light')`
2. POST to `/api/investigation/scan/{caseId}/light`
3. Route: `investigation_routes.py` → `start_scan(case_id, scan_type)`
4. Calls: `_light_scan(investigation)` or `_deep_scan(investigation)`
5. Services call: scraper, analyzer, network_builder
6. Returns: standardized JSON with threat_level ≥ 0
7. Frontend receives response

---

## Critical Integration Points

### ✅ Blueprint Registration (app.py)
```python
app.register_blueprint(investigation_bp)  # /api/investigation
app.register_blueprint(phone_bp)          # /api/phone
app.register_blueprint(graph_bp)          # /api/graph
app.register_blueprint(report_bp)         # /api/report
```

### ✅ API Contract (Frontend → Backend)
| Endpoint | Frontend Sends | Backend Reads |
|----------|---|---|
| `/api/phone/lookup` | `{ phone_number, country_code, scan_type }` | `data.get('phone_number')` |
| `/api/investigation/create` | `{ username, email, phone }` | `data.get('username')` |
| `/api/investigation/scan/:caseId/:scanType` | JSON body (optional) | URL parameters |

### ✅ Error Handling
- Route wraps service calls in try/except
- Always returns HTTP 200 with safe JSON body
- Never returns 500 unless absolute top-level failure
- Logging includes [PHONE_LOOKUP], [SCAN], [THREAT_SCORING] tags

### ✅ Data Validation
- Phone normalization: multi-strategy parser
- Threat scoring: zero when no findings
- Response structure: consistent across all endpoints

---

## Potential Issues to Verify

1. **Missing response data field**: Frontend expects `res.data` but backend returns flat structure
2. **Phone format rejection**: Multiple formats should work (024..., 233..., +233...)
3. **Threat scoring**: Should be 0 when no findings, not 10
4. **Scan failures**: Check if services return None or incomplete data
5. **Database transactions**: Rollback on error to prevent corrupted state

---

## Testing Commands

### Test 1: Health Check
```bash
curl -X GET http://127.0.0.1:5000/api/health
```

### Test 2: Phone Lookup (Minimal)
```bash
curl -X POST http://127.0.0.1:5000/api/phone/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+233 24 1111 1111",
    "scan_type": "light"
  }'
```

### Test 3: Phone Lookup (With Country)
```bash
curl -X POST http://127.0.0.1:5000/api/phone/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "024 1111 1111",
    "country_code": "GH",
    "scan_type": "light"
  }'
```

### Test 4: Create Investigation
```bash
curl -X POST http://127.0.0.1:5000/api/investigation/create \
  -H "Content-Type: application/json" \
  -d '{
    "username": "exampleuser",
    "email": "example@domain.com"
  }'
```

### Test 5: Start Scan
```bash
# First get case_id from create response, then:
curl -X POST http://127.0.0.1:5000/api/investigation/scan/{case_id}/light
```

---

## Expected Outcomes

✅ All endpoints return HTTP 200  
✅ All responses are valid JSON  
✅ Phone formats: 024..., 233..., +233... all work  
✅ Threat_level = 0 when no findings  
✅ Scan never returns 500 (even if service fails partially)  
✅ All debug logs appear with [PHONE_LOOKUP], [SCAN], [THREAT_SCORING] tags
