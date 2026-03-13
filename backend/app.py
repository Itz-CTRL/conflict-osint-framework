"""
app.py

Main FastAPI server for OSINT Investigation Platform.
Case-based investigation workflow with phone intelligence support.

Endpoints:
  POST /api/investigation/create       - Create investigation case
  POST /api/investigation/scan/{caseId}/{scanType}  - Run scan
  GET  /api/investigation/result/{caseId}         - Get results
  POST /api/phone/lookup               - Phone intelligence
  POST /api/phone/scan                 - Phone scan shortcut
  GET  /api/health                     - Health check
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import uuid
from dotenv import load_dotenv
import logging

from sherlock_scan import light_scan
from deep_scan_service import deep_scan_service
from phone_intel import validate_and_analyze_phone
from database import db


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OSINT Investigation Platform",
    description="Minimal, stable OSINT backend",
    version="1.0.0"
)

# ── CORS Configuration ──
# Allow frontend to connect from localhost and Render
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ──
class CreateInvestigationRequest(BaseModel):
    """Create investigation request"""
    username: str = Field(..., min_length=2, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    filters: Optional[dict] = None


class PhoneAnalysisRequest(BaseModel):
    """Phone analysis request"""
    phone_number: str = Field(..., min_length=7, max_length=20)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    scan_type: Optional[str] = Field("light", pattern="^(light|deep)$")


# ── Health Check ──
@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "OSINT Investigation Platform",
        "version": "1.0.0"
    }


# ── Debug Endpoints (for testing) ──
@app.get("/api/test/light-scan/{username}")
async def test_light_scan(username: str):
    """
    Simple test endpoint for light scan.
    Returns raw light scan results without investigation case.
    Use this to verify light_scan is working.
    
    Example: GET /api/test/light-scan/torvalds
    """
    try:
        logger.info(f"TEST: Running light scan for {username}")
        result = light_scan(username)
        
        logger.info(f"TEST: Light scan result: {result}")
        
        return {
            "status": "success",
            "endpoint": "test_light_scan",
            "username": username,
            "data": result.get("data"),
            "raw_result": result
        }
    except Exception as e:
        logger.error(f"TEST: Light scan error: {str(e)}")
        return {
            "status": "error",
            "endpoint": "test_light_scan",
            "error": str(e)
        }


# ── Utility Endpoints ──
@app.get("/api/username_suggestions")
async def username_suggestions(q: Optional[str] = None):
    """
    Username suggestions endpoint for autocomplete.
    Returns empty list for MVP (safe default).
    """
    if not q or len(q.strip()) < 2:
        return {
            "status": "success",
            "suggestions": []
        }
    return {
        "status": "success",
        "suggestions": []
    }


@app.get("/api/investigation/list")
async def list_investigations(page: int = 1, limit: int = 10):
    """
    List investigation cases.
    
    Response:
      {
        "status": "success",
        "data": [...],
        "pagination": {
          "page": 1,
          "limit": 10,
          "total": N
        }
      }
    """
    try:
        case_list = db.list_cases()
        total = len(case_list)
        
        # Paginate
        start = (page - 1) * limit
        end = start + limit
        paginated = case_list[start:end]
        
        return {
            "status": "success",
            "data": paginated,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total
            }
        }
    except Exception as e:
        logger.error(f"Error listing investigations: {str(e)}")
        return {
            "status": "error",
            "error": "Failed to list investigations"
        }


# ── Investigation Endpoints ──
@app.post("/api/investigation/create")
async def create_investigation(request: CreateInvestigationRequest):
    """
    Create a new investigation case with optional filters.
    
    Request:
      {
        "username": "target_username",
        "email": "optional@email.com",
        "phone": "+1234567890",
        "filters": {
          "platforms": ["twitter", "github"],
          "exclude_age": true,
          "scan_depth": "deep"
        }
      }
    
    Response:
      {
        "status": "success",
        "case_id": "uuid-string",
        "data": {
          "username": "target_username",
          ...
        }
      }
    """
    try:
        username = request.username.strip()
        
        if not username or len(username) < 2:
            return {
                "status": "error",
                "error": "Username must be at least 2 characters"
            }
        
        # Create case ID
        case_id = str(uuid.uuid4())
        
        # Store case data in database
        filters = request.filters or {}
        case = db.create_case(
            case_id=case_id,
            username=username,
            email=request.email,
            phone=request.phone,
            filters=filters
        )
        
        logger.info(f"Investigation case created: {case_id} for {username} with filters: {filters}")
        
        return {
            "status": "success",
            "case_id": case_id,
            "data": {
                "case_id": case_id,
                "username": username,
                "status": "created",
                "filters": filters
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating investigation: {str(e)}")
        return {
            "status": "error",
            "error": "Failed to create investigation case"
        }


@app.post("/api/investigation/scan/{case_id}/{scan_type}")
async def start_scan(case_id: str, scan_type: str):
    """
    Run a scan on investigation case.
    Scan types: 'light' or 'deep'
    
    Response:
      {
        "status": "success",
        "case_id": "uuid",
        "data": {...scan results...},
        "graph": null
      }
    """
    try:
        case = db.get_case(case_id)
        if not case:
            return {
                "status": "error",
                "error": "Case not found"
            }
        
        username = case["username"]
        email = case.get("email")
        
        if scan_type not in ["light", "deep"]:
            return {
                "status": "error",
                "error": "Invalid scan type. Must be 'light' or 'deep'."
            }
        
        logger.info(f"Starting {scan_type} scan for case {case_id}")
        
        # Run appropriate scan
        if scan_type == "light":
            result = light_scan(username)
        else:  # deep
            # Use enhanced deep scan service
            result = deep_scan_service.deep_scan(username, email)
        
        if not result.get("success"):
            return {
                "status": "error",
                "error": result.get("error", "Scan failed"),
                "case_id": case_id
            }
        
        # Store result in database
        scan_data = result["data"]
        if scan_type == "light":
            db.set_light_scan_result(case_id, scan_data)
        else:
            db.set_deep_scan_result(case_id, scan_data)
        
        logger.info(f"Scan result for {case_id}: {scan_data}")
        
        return {
            "status": "success",
            "case_id": case_id,
            "data": scan_data,
            "graph": None  # Frontend expects this key
        }
    
    except Exception as e:
        logger.error(f"Scan error: {str(e)}")
        return {
            "status": "error",
            "error": "Scan failed. Please try again.",
            "case_id": case_id
        }


@app.get("/api/investigation/result/{case_id}")
async def get_investigation_result(case_id: str):
    """
    Get investigation result for a case.
    
    Response:
      {
        "status": "success",
        "case_id": "uuid",
        "data": {...},
        "graph": {...}
      }
    """
    try:
        case = db.get_case(case_id)
        if not case:
            return {
                "status": "error",
                "error": "Case not found"
            }
        
        # Return most recent scan result
        scan_result = case.get("deep_scan_result") or case.get("light_scan_result")
        
        if not scan_result:
            return {
                "status": "error",
                "error": "No scan results found for this case"
            }
        
        return {
            "status": "success",
            "case_id": case_id,
            "data": scan_result,
            "graph": None  # Frontend expects this
        }
    
    except Exception as e:
        logger.error(f"Error getting result: {str(e)}")
        return {
            "status": "error",
            "error": "Failed to retrieve result"
        }


@app.get("/api/investigation/status/{case_id}")
async def get_investigation_status(case_id: str):
    """
    Get investigation status for a case.
    
    Response:
      {
        "status": "success",
        "case_id": "uuid",
        "data": {
          "status": "created|light_complete|deep_complete",
          "scan_type": "light|deep",
          "username": "...",
          "profile_count": 5,
          "risk_score": 10,
          "risk_level": "low"
        }
      }
    """
    try:
        case = db.get_case(case_id)
        if not case:
            return {
                "status": "error",
                "error": "Case not found"
            }
        
        current_status = case.get("status", "created")
        
        # Get scan result if available
        scan_result = case.get("deep_scan_result") or case.get("light_scan_result")
        profile_count = scan_result.get("count", 0) if scan_result else 0
        risk_score = scan_result.get("threat_score", 10) if scan_result else 10
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Extract scan type from status
        scan_type = "deep" if "deep" in current_status else "light"
        
        return {
            "status": "success",
            "case_id": case_id,
            "data": {
                "status": current_status,
                "scan_type": scan_type,
                "username": case.get("username"),
                "profile_count": profile_count,
                "risk_score": risk_score,
                "risk_level": risk_level
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {
            "status": "error",
            "error": "Failed to retrieve status"
        }


@app.delete("/api/investigation/delete/{case_id}")
async def delete_investigation(case_id: str):
    """
    Delete an investigation case.
    
    Response:
      {
        "status": "success",
        "message": "Investigation deleted"
      }
    """
    try:
        case = db.get_case(case_id)
        if not case:
            return {
                "status": "error",
                "error": "Case not found"
            }
        
        db.delete_case(case_id)
        
        return {
            "status": "success",
            "message": "Investigation deleted"
        }
    
    except Exception as e:
        logger.error(f"Error deleting investigation: {str(e)}")
        return {
            "status": "error",
            "error": "Failed to delete investigation"
        }


# ── Graph Endpoints ──
@app.get("/api/graph/{case_id}")
async def get_graph(case_id: str):
    """
    Get graph data (nodes and edges) for a case.
    Constructs network graph from findings, emails, devices, and mentions.
    
    Response:
      {
        "status": "success",
        "graph": {
          "nodes": [...],
          "edges": [...],
          "statistics": {...}
        }
      }
    """
    try:
        case = db.get_case(case_id)
        if not case:
            return {
                "status": "error",
                "error": "Case not found",
                "graph": None
            }
        
        scan_result = case.get("deep_scan_result") or case.get("light_scan_result")
        
        if not scan_result:
            return {
                "status": "error",
                "error": "No scan results found",
                "graph": None
            }
        
        username = case.get("username", "unknown")
        nodes = []
        edges = []
        node_ids = set()
        
        # 1. Add target username as central node
        target_node_id = f"user_{username}"
        nodes.append({
            "id": target_node_id,
            "label": f"@{username}",
            "type": "profile",
            "size": 30,
            "title": f"Target: {username}",
            "color": "#ef4444"
        })
        node_ids.add(target_node_id)
        
        # 2. Add platform nodes from findings
        findings = scan_result.get("findings", [])
        for finding in findings:
            if finding.get("found"):
                platform = finding.get("platform", "unknown")
                platform_node_id = f"platform_{platform.lower()}"
                
                if platform_node_id not in node_ids:
                    nodes.append({
                        "id": platform_node_id,
                        "label": platform,
                        "type": "platform",
                        "size": 20,
                        "title": f"{platform}",
                        "color": "#06b6d4"
                    })
                    node_ids.add(platform_node_id)
                
                # Add edge from user to platform
                edges.append({
                    "from": target_node_id,
                    "to": platform_node_id,
                    "label": "found_on",
                    "type": "CONNECTED_TO",
                    "title": f"Profile found on {platform}",
                    "color": "#06b6d4"
                })
        
        # 3. Add email nodes
        emails = scan_result.get("emails", [])
        for email in emails:
            email_str = email if isinstance(email, str) else email.get("email", "")
            if email_str:
                email_node_id = f"email_{email_str.replace('@', '_').replace('.', '_')}"
                
                if email_node_id not in node_ids:
                    nodes.append({
                        "id": email_node_id,
                        "label": email_str,
                        "type": "email",
                        "size": 16,
                        "title": f"Email: {email_str}",
                        "color": "#f59e0b"
                    })
                    node_ids.add(email_node_id)
                
                # Add edge from user to email
                edges.append({
                    "from": target_node_id,
                    "to": email_node_id,
                    "label": "uses",
                    "type": "USES_EMAIL",
                    "title": f"Associated email",
                    "color": "#f59e0b"
                })
        
        # 4. Add device nodes (from Shodan/intelligence)
        devices = scan_result.get("devices", [])
        for device in devices:
            ip = device.get("ip_str", "unknown")
            port = device.get("port", "unknown")
            service = device.get("service", "unknown")
            
            device_node_id = f"device_{ip}_{port}"
            
            if device_node_id not in node_ids:
                nodes.append({
                    "id": device_node_id,
                    "label": f"{ip}:{port}",
                    "type": "server",
                    "size": 14,
                    "title": f"{service} on {ip}:{port}",
                    "color": "#a855f7"
                })
                node_ids.add(device_node_id)
            
            # Add edge from user to device
            edges.append({
                "from": target_node_id,
                "to": device_node_id,
                "label": "connected_to",
                "type": "CONNECTED_TO",
                "title": f"Device: {service}",
                "color": "#a855f7"
            })
        
        # 5. Add mention nodes (only if they have threat keywords)
        mentions = scan_result.get("mentions", [])
        mention_count = 0
        for i, mention in enumerate(mentions):
            if isinstance(mention, dict) and mention.get("keywords"):  # Only add if has threat keywords
                mention_text = mention.get("text", "mention")[:30]
                mention_node_id = f"mention_{i}"
                
                nodes.append({
                    "id": mention_node_id,
                    "label": mention_text,
                    "type": "mention",
                    "size": 14,
                    "title": mention.get("text", ""),
                    "color": "#3b82f6"
                })
                
                # Add edge from user to mention
                edges.append({
                    "from": target_node_id,
                    "to": mention_node_id,
                    "label": "mentioned_in",
                    "type": "MENTIONS",
                    "title": f"Found in: {mention.get('source', 'web')}",
                    "color": "#3b82f6"
                })
                mention_count += 1
        
        # 6. Add breach nodes if any
        breaches = scan_result.get("breaches", [])
        for i, breach in enumerate(breaches):
            breach_name = breach.get("Name", f"Breach_{i}")
            breach_node_id = f"breach_{breach_name.lower().replace(' ', '_')}"
            
            if breach_node_id not in node_ids:
                nodes.append({
                    "id": breach_node_id,
                    "label": breach_name,
                    "type": "breach",
                    "size": 14,
                    "title": f"Data Breach: {breach.get('Title', breach_name)}",
                    "color": "#dc2626"
                })
                node_ids.add(breach_node_id)
            
            # Add edge from user to breach
            edges.append({
                "from": target_node_id,
                "to": breach_node_id,
                "label": "breached_in",
                "type": "REPORTED_AS",
                "title": f"Involved in {breach_name}",
                "color": "#dc2626"
            })
        
        graph = {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {},
                "edge_types": {},
            }
        }
        
        # Count node and edge types
        for node in nodes:
            node_type = node.get("type", "unknown")
            graph["statistics"]["node_types"][node_type] = graph["statistics"]["node_types"].get(node_type, 0) + 1
        
        for edge in edges:
            edge_type = edge.get("type", "unknown")
            graph["statistics"]["edge_types"][edge_type] = graph["statistics"]["edge_types"].get(edge_type, 0) + 1
        
        return {
            "status": "success",
            "graph": graph
        }
    
    except Exception as e:
        logger.error(f"Error getting graph: {str(e)}")
        return {
            "status": "error",
            "error": "Failed to retrieve graph data",
            "graph": None
        }


@app.get("/api/graph/{case_id}/statistics")
async def get_graph_statistics(case_id: str):
    """
    Get graph statistics for a case.
    
    Response:
      {
        "status": "success",
        "statistics": {
          "total_nodes": N,
          "total_edges": M,
          "node_types": {...},
          "edge_types": {...},
          "density": float,
          "avg_degree": float
        }
      }
    """
    try:
        graph_response = await get_graph(case_id)
        
        if not graph_response.get("graph"):
            return {
                "status": "error",
                "error": "No graph data available",
                "statistics": None
            }
        
        graph = graph_response["graph"]
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        total_nodes = len(nodes)
        total_edges = len(edges)
        
        # Calculate density (edges / max_possible_edges)
        max_edges = total_nodes * (total_nodes - 1) / 2 if total_nodes > 1 else 1
        density = total_edges / max_edges if max_edges > 0 else 0
        
        # Calculate average degree
        node_degrees = {}
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            node_degrees[from_id] = node_degrees.get(from_id, 0) + 1
            node_degrees[to_id] = node_degrees.get(to_id, 0) + 1
        
        avg_degree = sum(node_degrees.values()) / total_nodes if total_nodes > 0 else 0
        
        statistics = {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "density": round(density, 4),
            "average_degree": round(avg_degree, 2),
            "node_types": graph.get("statistics", {}).get("node_types", {}),
            "edge_types": graph.get("statistics", {}).get("edge_types", {})
        }
        
        return {
            "status": "success",
            "statistics": statistics
        }
    
    except Exception as e:
        logger.error(f"Error getting graph statistics: {str(e)}")
        return {
            "status": "error",
            "error": "Failed to retrieve graph statistics",
            "statistics": None
        }


# ── Phone Intelligence Endpoints ──
@app.post("/api/phone/lookup")
async def phone_lookup(request: PhoneAnalysisRequest):
    """
    Phone intelligence lookup.
    
    Request:
      {
        "phone_number": "+233XXXXXXXXX",
        "country_code": "GH",
        "scan_type": "light"
      }
    
    Response:
      {
        "status": "success",
        "data": {
          "number": "+233XXXXXXXXX",
          "country": "Ghana",
          "carrier": "MTN",
          ...
        }
      }
    """
    try:
        phone = request.phone_number.strip()
        country_code = request.country_code.upper() if request.country_code else None
        
        if not phone or len(phone) < 7:
            return {
                "status": "error",
                "error": "Invalid phone number format"
            }
        
        logger.info(f"Phone lookup: {phone}")
        result = validate_and_analyze_phone(phone, country_code)
        
        if "error" in result:
            return {
                "status": "error",
                "error": result.get("error", "Phone analysis failed")
            }
        
        return {
            "status": "success",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Phone lookup error: {str(e)}")
        return {
            "status": "error",
            "error": "Phone analysis failed. Please verify the number and try again."
        }


@app.post("/api/phone/scan")
async def phone_scan(request: PhoneAnalysisRequest):
    """
    Simplified phone scan endpoint (same as lookup).
    """
    return await phone_lookup(request)


# ── Root ──
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OSINT Investigation Platform API",
        "endpoints": [
            "POST /api/investigation/create",
            "POST /api/investigation/scan/{caseId}/{scanType}",
            "GET /api/investigation/result/{caseId}",
            "POST /api/phone/lookup",
            "POST /api/phone/scan",
            "GET /api/health"
        ]
    }


# ── Error Handlers ──
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return {
        "status": "error",
        "error": exc.detail
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions without exposing stack traces"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "status": "error",
        "error": "An error occurred. Please try again."
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
