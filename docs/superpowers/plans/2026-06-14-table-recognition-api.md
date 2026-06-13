# Table Recognition API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two isolated FastAPI endpoints for PaddleOCR TableRecognitionPipelineV2 that accept URL or uploaded image/PDF and return the first table as simple JSON, HTML text, or one downloaded XLSX file.

**Architecture:** Add a new `routers/table.py` module with a lazy singleton `TableRecognitionPipelineV2`. Keep table-specific helpers in the same module because this project currently keeps route logic in router modules and the feature is small. Existing `/ocr` and `/pdf` routes remain unchanged except for registering the new router in `main.py`.

**Tech Stack:** FastAPI, PaddleOCR 3.7 `TableRecognitionPipelineV2`, stdlib `tempfile`, `pathlib`, `html.parser`, `requests`, pytest/TestClient with fake pipeline objects.

---

### Task 1: Helper Behavior Tests

**Files:**
- Create: `test_table_api.py`
- Create: `routers/table.py`

- [ ] Write tests for HTML row extraction and unsupported format validation using fake inputs.
- [ ] Run `python -m pytest test_table_api.py -q`; expect failure because `routers.table` does not exist.
- [ ] Implement `rows_from_html` and `normalize_format` in `routers/table.py`.
- [ ] Run `python -m pytest test_table_api.py -q`; expect helper tests to pass.

### Task 2: Endpoint Tests With Fake Pipeline

**Files:**
- Modify: `test_table_api.py`
- Modify: `routers/table.py`

- [ ] Add TestClient tests for `format=html`, `format=json`, and `format=xlsx` using a fake pipeline result that writes HTML, JSON, and XLSX files.
- [ ] Run `python -m pytest test_table_api.py -q`; expect endpoint tests to fail because routes are not implemented.
- [ ] Implement `/table/predict-by-url` and `/table/predict-by-file`, temporary file download/upload handling, and export response logic.
- [ ] Run `python -m pytest test_table_api.py -q`; expect tests to pass.

### Task 3: App Wiring

**Files:**
- Modify: `main.py`
- Modify: `test_table_api.py`

- [ ] Add a test that a FastAPI app can include `routers.table.router` and expose `/table` routes.
- [ ] Run `python -m pytest test_table_api.py -q`; expect failure if router is not wired in `main.py`.
- [ ] Import and include `table.router` in `main.py`.
- [ ] Run `python -m pytest test_table_api.py -q`; expect all tests to pass.

### Self-Review

- Requirements covered: URL endpoint, upload endpoint, image/PDF temp file support, first table only, simple JSON, raw HTML text, single XLSX download, isolated from current OCR code.
- No zip output is planned.
- Real PaddleOCR integration follows the official documented `TableRecognitionPipelineV2().predict(...)` plus `save_to_xlsx`, `save_to_html`, and `save_to_json` export methods.
