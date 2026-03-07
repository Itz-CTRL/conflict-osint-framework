# Service Integration Guide

This guide shows how to refactor existing routes to use the new `PhoneIntelligenceService` and `GraphEngineService` classes.

---

## Phone Routes Integration

### Current Implementation (phone_routes.py)

The current routes contain inline phone lookup logic. To use the new service:

**Before** (Current Code):
```python
@phone_bp.route('/lookup', methods=['POST'])
def lookup_phone():
    try:
        data = request.get_json()
        phone_number = data.get('phone')
        
        # Inline phone parsing and validation
        parsed = phonenumbers.parse(phone_number, None)
        # ... lots of manual processing
```

**After** (Using Service):
```python
from services import PhoneIntelligenceService

phone_service = PhoneIntelligenceService()

@phone_bp.route('/lookup', methods=['POST'])
def lookup_phone():
    try:
        data = request.get_json()
        phone_number = data.get('phone')
        
        # Use service for lookup
        result = phone_service.lookup(phone_number)
        
        if not result['valid']:
            return APIResponse.error(result['error'], 400)
        
        # Optionally save to database
        phone_intel = PhoneIntelligence(
            phone_number=result['number'],
            country=result['country'],
            country_code=result['country_code'],
            region=result['region'],
            carrier=result['carrier'],
            carrier_type=result['carrier_type'],
            timezone=result['timezone'],
            social_presence=json.dumps(result['social_presence']),
            emails_found=json.dumps(result['emails_found']),
            risk_score=result['risk_score'],
            risk_level=result['risk_level'],
            confidence=result['confidence'],
            raw_data=json.dumps(result)
        )
        db.session.add(phone_intel)
        db.session.commit()
        
        return APIResponse.success(result)
        
    except Exception as e:
        return APIResponse.error(str(e), 500)
```

---

### Batch Lookup Endpoint

**Add new endpoint** to phone_routes.py:

```python
@phone_bp.route('/batch-lookup', methods=['POST'])
def batch_lookup():
    """Lookup multiple phone numbers at once"""
    try:
        data = request.get_json()
        phone_numbers = data.get('phone_numbers', [])
        
        if len(phone_numbers) > 100:
            return APIResponse.error('Maximum 100 phone numbers per request', 400)
        
        service = PhoneIntelligenceService()
        results = service.batch_lookup(phone_numbers)
        
        # Save all results to database
        for result in results:
            if result['valid']:
                phone_intel = PhoneIntelligence(
                    phone_number=result['number'],
                    country=result['country'],
                    carrier=result['carrier'],
                    risk_score=result['risk_score'],
                    raw_data=json.dumps(result)
                )
                db.session.add(phone_intel)
        
        db.session.commit()
        
        return APIResponse.success({
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return APIResponse.error(str(e), 500)
```

---

## Graph Routes Integration

### Current Implementation

**Before** (Current Code):
```python
@graph_bp.route('/<investigation_id>', methods=['GET'])
def get_graph(investigation_id):
    try:
        investigation = Investigation.query.get(investigation_id)
        findings = Finding.query.filter_by(investigation_id=investigation_id).all()
        
        # Inline graph building
        G = nx.Graph()
        nodes = []
        edges = []
        # ... manual graph construction
```

**After** (Using Service):
```python
from services import GraphEngineService

@graph_bp.route('/<investigation_id>', methods=['GET'])
def get_graph(investigation_id):
    try:
        investigation = Investigation.query.get(investigation_id)
        findings = Finding.query.filter_by(investigation_id=investigation_id).all()
        
        # Use service for graph building
        engine = GraphEngineService(case_id=investigation_id)
        
        findings_data = [f.to_dict() for f in findings]
        
        graph = engine.build_from_investigation(
            {
                'id': investigation.id,
                'username': investigation.username,
                'email': investigation.email or None,
                'phone': investigation.phone or None,
                'risk_score': investigation.risk_score
            },
            findings_data
        )
        
        return APIResponse.success(graph)
        
    except Exception as e:
        return APIResponse.error(str(e), 500)
```

---

### Graph Statistics Endpoint

**Add new endpoint** to graph_routes.py:

```python
@graph_bp.route('/<investigation_id>/statistics', methods=['GET'])
def get_graph_statistics(investigation_id):
    """Get detailed graph metrics"""
    try:
        investigation = Investigation.query.get(investigation_id)
        findings = Finding.query.filter_by(investigation_id=investigation_id).all()
        
        engine = GraphEngineService(case_id=investigation_id)
        findings_data = [f.to_dict() for f in findings]
        
        # Build graph (needed for statistics)
        engine.build_from_investigation(
            {
                'id': investigation.id,
                'username': investigation.username,
                'email': investigation.email or None,
                'phone': investigation.phone or None,
                'risk_score': investigation.risk_score
            },
            findings_data
        )
        
        # Get metrics
        stats = engine.get_statistics()
        
        return APIResponse.success({
            'investigation_id': investigation_id,
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return APIResponse.error(str(e), 500)
```

---

### Graph Export Endpoints

**Add export endpoints** to graph_routes.py:

```python
@graph_bp.route('/<investigation_id>/export/json', methods=['GET'])
def export_graph_json(investigation_id):
    """Export graph as JSON"""
    try:
        investigation = Investigation.query.get(investigation_id)
        findings = Finding.query.filter_by(investigation_id=investigation_id).all()
        
        engine = GraphEngineService(case_id=investigation_id)
        findings_data = [f.to_dict() for f in findings]
        
        engine.build_from_investigation(
            {
                'id': investigation.id,
                'username': investigation.username,
                'email': investigation.email or None,
                'phone': investigation.phone or None,
                'risk_score': investigation.risk_score
            },
            findings_data
        )
        
        graph = engine.export_json()
        
        return send_file(
            io.BytesIO(json.dumps(graph).encode()),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'graph_{investigation_id}.json'
        )
        
    except Exception as e:
        return APIResponse.error(str(e), 500)


@graph_bp.route('/<investigation_id>/export/graphml', methods=['GET'])
def export_graph_graphml(investigation_id):
    """Export graph as GraphML (for Gephi/desktop tools)"""
    try:
        investigation = Investigation.query.get(investigation_id)
        findings = Finding.query.filter_by(investigation_id=investigation_id).all()
        
        engine = GraphEngineService(case_id=investigation_id)
        findings_data = [f.to_dict() for f in findings]
        
        engine.build_from_investigation(
            {
                'id': investigation.id,
                'username': investigation.username,
                'email': investigation.email or None,
                'phone': investigation.phone or None,
                'risk_score': investigation.risk_score
            },
            findings_data
        )
        
        graphml = engine.export_graphml()
        
        return send_file(
            io.BytesIO(graphml.encode()),
            mimetype='application/xml',
            as_attachment=True,
            download_name=f'graph_{investigation_id}.graphml'
        )
        
    except Exception as e:
        return APIResponse.error(str(e), 500)
```

---

## Investigation Routes Integration

### Enhanced Light Scan

```python
from services import PhoneIntelligenceService, GraphEngineService

@investigation_bp.route('/scan/<case_id>/light', methods=['POST'])
def start_light_scan(case_id):
    """Light scan with phone intelligence and graph"""
    try:
        investigation = Investigation.query.get(case_id)
        phone_service = PhoneIntelligenceService()
        
        # Scan phone if provided
        if investigation.phone:
            phone_intel = phone_service.lookup(investigation.phone)
            
            # Save to database
            phone_record = PhoneIntelligence(
                investigation_id=case_id,
                phone_number=phone_intel['number'],
                country=phone_intel['country'],
                carrier=phone_intel['carrier'],
                risk_score=phone_intel['risk_score'],
                confidence=phone_intel['confidence'],
                data=json.dumps(phone_intel)
            )
            db.session.add(phone_record)
        
        # Build initial graph
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        findings_data = [f.to_dict() for f in findings]
        
        graph_engine = GraphEngineService(case_id=case_id)
        graph = graph_engine.build_from_investigation(
            {
                'id': investigation.id,
                'username': investigation.username,
                'email': investigation.email,
                'phone': investigation.phone,
                'risk_score': investigation.risk_score
            },
            findings_data
        )
        
        investigation.status = 'completed'
        investigation.result = {
            'graph': graph,
            'phone_intel': phone_intel if investigation.phone else None,
            'statistics': graph_engine.get_statistics()
        }
        db.session.commit()
        
        return APIResponse.success({
            'case_id': case_id,
            'status': 'completed',
            'result': investigation.result
        })
        
    except Exception as e:
        investigation.status = 'failed'
        investigation.error = str(e)
        db.session.commit()
        return APIResponse.error(str(e), 500)
```

---

## Complete Integration Example

### Full phone_routes.py with Services

```python
from flask import Blueprint, request
from services import PhoneIntelligenceService
from database import db
from models import PhoneIntelligence
from utils.response import APIResponse
import json

phone_bp = Blueprint('phone', __name__, url_prefix='/api/phone')

# Initialize service at module level for reuse
_phone_service = PhoneIntelligenceService()


@phone_bp.route('/lookup', methods=['POST'])
def lookup_phone():
    """
    POST /api/phone/lookup
    Body: {"phone": "+1-202-555-1234"}
    Returns: Phone intelligence data
    """
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return APIResponse.error('Phone number required', 400)
        
        # Use service
        result = _phone_service.lookup(phone)
        
        if not result['valid']:
            return APIResponse.error(result['error'], 400)
        
        # Save to database
        phone_intel = PhoneIntelligence(
            phone_number=result['number'],
            country=result['country'],
            country_code=result['country_code'],
            region=result['region'],
            carrier=result['carrier'],
            carrier_type=result['carrier_type'],
            timezone=result['timezone'],
            social_presence=json.dumps(result['social_presence']),
            emails_found=json.dumps(result['emails_found']),
            risk_score=result['risk_score'],
            risk_level=result['risk_level'],
            confidence=result['confidence'],
            raw_data=json.dumps(result)
        )
        db.session.add(phone_intel)
        db.session.commit()
        
        return APIResponse.success(result)
        
    except Exception as e:
        return APIResponse.error(str(e), 500)


@phone_bp.route('/batch-lookup', methods=['POST'])
def batch_lookup_phones():
    """
    POST /api/phone/batch-lookup
    Body: {"phone_numbers": ["+1234567890", "+9876543210"]}
    Returns: List of phone intelligence data
    """
    try:
        data = request.get_json()
        phones = data.get('phone_numbers', [])
        
        if not phones or len(phones) > 100:
            return APIResponse.error('Provide 1-100 phone numbers', 400)
        
        # Use service
        results = _phone_service.batch_lookup(phones)
        
        # Save all valid results
        for result in results:
            if result['valid']:
                phone_intel = PhoneIntelligence(
                    phone_number=result['number'],
                    country=result['country'],
                    carrier=result['carrier'],
                    risk_score=result['risk_score'],
                    confidence=result['confidence'],
                    raw_data=json.dumps(result)
                )
                db.session.add(phone_intel)
        
        db.session.commit()
        
        return APIResponse.success({
            'count': len(results),
            'valid_count': sum(1 for r in results if r['valid']),
            'results': results
        })
        
    except Exception as e:
        return APIResponse.error(str(e), 500)


@phone_bp.route('/validate/<phone>', methods=['GET'])
def validate_phone(phone):
    """
    GET /api/phone/validate/+1-202-555-1234
    Returns: Validation result only (fast)
    """
    try:
        result = _phone_service.validate_only(phone)
        return APIResponse.success(result)
    except Exception as e:
        return APIResponse.error(str(e), 500)
```

---

## Testing Integration

### Unit Test Example

```python
import pytest
from services import PhoneIntelligenceService, GraphEngineService
from models import Investigation, Finding

def test_phone_service_integration():
    """Test phone service with database"""
    service = PhoneIntelligenceService()
    result = service.lookup("+1-202-555-1234")
    
    assert result['valid'] == True
    assert result['country_code'] == 'US'
    assert 'risk_score' in result
    assert 0 <= result['risk_score'] <= 100


def test_graph_service_integration():
    """Test graph service with investigation data"""
    service = GraphEngineService(case_id="test-123")
    
    investigation = {
        'id': 'test-123',
        'username': 'testuser',
        'email': 'test@example.com',
        'phone': None,
        'risk_score': 35
    }
    
    findings = [
        {
            'platform': 'Twitter',
            'found': True,
            'username': 'testuser123',
            'profile_url': 'https://twitter.com/testuser123',
            'metadata': {}
        }
    ]
    
    graph = service.build_from_investigation(investigation, findings)
    
    assert 'nodes' in graph
    assert 'edges' in graph
    assert len(graph['nodes']) > 0
    
    stats = service.get_statistics()
    assert stats['node_count'] > 0


def test_phone_batch_lookup():
    """Test batch phone lookup"""
    service = PhoneIntelligenceService()
    
    phones = [
        "+1-202-555-1234",
        "+44-20-7946-0958",
        "invalid_number"
    ]
    
    results = service.batch_lookup(phones)
    
    assert len(results) == 3
    assert results[0]['valid'] == True
    assert results[1]['valid'] == True
    assert results[2]['valid'] == False
```

---

## Benefits of Service Integration

1. **Code Reusability**: Services can be used from multiple routes
2. **Testability**: Easier to unit test service logic independently
3. **Maintainability**: Business logic separated from route handling
4. **Consistency**: All routes use same service implementations
5. **Documentation**: Service docstrings document behavior clearly
6. **Performance**: Service caching can improve repeated calls
7. **Error Handling**: Consistent error responses across services

---

## Migration Checklist

- [ ] Add `PhoneIntelligenceService` to phone_routes.py
- [ ] Update phone lookup endpoint to use service
- [ ] Add batch_lookup endpoint using service
- [ ] Add GraphEngineService to graph_routes.py
- [ ] Update graph building to use service
- [ ] Add graph statistics endpoint
- [ ] Add graph export endpoints (JSON and GraphML)
- [ ] Update investigation routes to use both services
- [ ] Test all endpoints with services
- [ ] Update documentation
- [ ] Deploy changes

---

**Last Updated**: 2024-03-04  
**Version**: 1.0
