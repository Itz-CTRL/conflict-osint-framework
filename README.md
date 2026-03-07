# OSINT Investigation Platform

A **military-grade, production-style** OSINT intelligence gathering and analysis system built with Flask (backend) and React (frontend).

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Server: `http://localhost:5000`

### Frontend
```bash
cd frontend
npm install
npm start
```
App: `http://localhost:3000`

## Features

- 🔍 **Light & Deep Scans** - Quick validation or comprehensive investigation
- 📊 **Network Graphs** - Visualize entity relationships and connections
- 📞 **Phone Intelligence** - Advanced phone number analysis (GhostTR.py integration)
- ⚠️ **Risk Scoring** - Compute 0-100 risk scores
- 📄 **PDF Reports** - Structured investigation reports
- 🔗 **Entity Correlation** - Automatic relationship discovery

## Requirements

- Python 3.9+ (backend)
- Node.js 18+ (frontend)

## Documentation

- [Software Requirements Document (SRD)](docs/SRD.md)
- [Software Design Document (SDD)](docs/SDD.md)
- [Backend API Reference](BACKEND_API.md)
- [Services Documentation](backend/SERVICES_DOCUMENTATION.md)
- [Current Status](CURRENT_STATUS.md)

## Security & Ethics

Use this project only with public data and for lawful, ethical research. Do not attempt to access private accounts, bypass authentication, or violate platform terms of service.

For more information, see the documentation files.
