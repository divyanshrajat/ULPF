# ULPF V2 Testing Guide

## Backend Tests
The backend API is built with FastAPI and is fully tested using `pytest`.

To run the backend unit and integration tests:
```bash
cd backend
python -m pytest tests/ -v
```

## End-to-End Testing
We provide an End-to-End mock script to verify the entire lifecycle (Ingestion -> Fingerprinting -> Control Plane Mocking -> Data Plane Execution -> Normalization).

```bash
cd backend
python test_e2e.py
```
This script will mock several raw logs, pass them through the ingest router, invoke the rule factories, and assert that the parsed outputs contain the correct OCSF fields and vault hashes.
