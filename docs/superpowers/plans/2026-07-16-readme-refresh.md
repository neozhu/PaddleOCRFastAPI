# README Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the outdated bilingual README content with current, runnable usage documentation and a repository-owned API usage visual.

**Architecture:** The documentation reads directly from the existing FastAPI routers and deployment files; no application behavior changes. A single landscape PNG under `screenshots/` provides a shared use-oriented visual for both language versions.

**Tech Stack:** Markdown, FastAPI/OpenAPI routes, Docker Compose, built-in image generation.

## Global Constraints

- Preserve application source, dependencies, Docker configuration, and API behavior unchanged.
- Document the current PaddleOCR 3.7.x dependency family, `paddlex[ocr]==3.7.1`, and the Python 3.12 Docker image exactly as present in the repository.
- Use only implemented routes and parameter names: `/ocr`, `/table`, and `/pdf`.
- Store the generated PNG in `screenshots/` and use a repository-relative Markdown path.
- The visual must explain user input, API request, and result; it must not be a technical architecture diagram.

---

### Task 1: Generate the shared usage visual

**Files:**
- Create: `screenshots/api-usage-flow.png`
- Modify: none
- Test: manual image inspection

**Interfaces:**
- Consumes: The README visual direction from `docs/superpowers/specs/2026-07-16-readme-refresh-design.md`.
- Produces: A landscape PNG at `screenshots/api-usage-flow.png`, referenced by both README files.

- [ ] **Step 1: Generate one documentation illustration**

Use the built-in image generator with this prompt:

```text
Use case: infographic-diagram
Asset type: landscape README documentation illustration
Primary request: show an easy three-step workflow for an OCR REST API: an image and a PDF document as input, a simple HTTP API request in the middle, and structured text plus a table as results.
Style/medium: clean modern flat illustration, polished technical documentation visual.
Composition/framing: wide 16:9 layout with three large clearly separated panels flowing left to right; generous margins; no tiny text.
Lighting/mood: clear, friendly, practical, trustworthy.
Color palette: white background with navy, sky blue, and teal accents.
Text (verbatim): "Image / PDF"; "API request"; "Text / Table"
Constraints: depict usage only, keep the English labels large and legible, no logo, no watermark, no source-code texture, no servers, no technical architecture diagram.
Avoid: unreadable small text, Chinese characters, extra branding, dark background.
```

- [ ] **Step 2: Save the generated asset in the repository**

Copy the selected non-empty generated PNG to `screenshots/api-usage-flow.png`. Do not overwrite `screenshots/Swagger.png`.

- [ ] **Step 3: Inspect the asset**

Run: `Get-Item screenshots\api-usage-flow.png | Select-Object Length`

Expected: a non-zero file size, with an image showing input, request, and output steps.

### Task 2: Rewrite the English README

**Files:**
- Modify: `README.md`
- Test: Markdown path validation

**Interfaces:**
- Consumes: `screenshots/api-usage-flow.png` and route contracts in `routers/ocr.py`, `routers/table.py`, and `routers/pdf_ocr.py`.
- Produces: An English quick-start README that documents current features and actual curl requests.

- [ ] **Step 1: Replace obsolete overview and version-selection content**

Write an English overview that identifies the service as a FastAPI wrapper for PaddleOCR 3.7.x, powered by PP-OCRv6 small detection and recognition models. State the Docker image base is Python 3.12. Remove the PaddleOCR v2.5/v2.7 branch table and the old `OCR_LANGUAGE` customization instructions.

- [ ] **Step 2: Add quick-start instructions**

Document `python -m venv .venv`, activation, `pip install -r requirements.txt`, and `uvicorn main:app --host 0.0.0.0 --port 8000`. Document the first-request model download and `http://localhost:8000/docs`. Add Docker commands `docker compose up --build -d` and `docker compose logs -f`.

- [ ] **Step 3: Add verified API examples**

Document `POST /ocr/predict-by-file` with multipart field `file`; `GET /ocr/predict-by-url` with query parameter `imageUrl`; `POST /table/predict-by-file?format=json` with multipart field `file`; and `POST /pdf/predict-by-file` with multipart field `file`. Include a short OCR JSON shape (`resultcode`, `message`, `data`, `rec_texts`, `rec_boxes`) and table output options `json`, `html`, and `xlsx`.

- [ ] **Step 4: Insert the shared visual and current repository links**

Reference `screenshots/api-usage-flow.png` immediately after the opening overview. Retain a link to `README_CN.md`, the Swagger endpoint, and `LICENSE`. Do not reference stale `cgcel` URLs.

- [ ] **Step 5: Validate Markdown references**

Run: `rg -n "api-usage-flow|README_CN|/docs|LICENSE" README.md`

Expected: every required relative file and URL is present.

### Task 3: Rewrite the Chinese README and verify the final documentation set

**Files:**
- Modify: `README_CN.md`
- Test: Markdown path validation and diff inspection

**Interfaces:**
- Consumes: `README.md`, `screenshots/api-usage-flow.png`, and the verified route contracts.
- Produces: A Chinese README with the same operational coverage as the English README.

- [ ] **Step 1: Mirror the English structure in natural Chinese**

Use the sections `简介`, `功能`, `快速开始`, `API 示例`, `接口说明`, `常见说明`, and `许可证`. Keep executable commands and route names identical to the English README, while translating explanatory text.

- [ ] **Step 2: Use the shared visual**

Add `![PaddleOCRFastAPI 使用流程](./screenshots/api-usage-flow.png)` after the Chinese overview. Link back to `README.md`.

- [ ] **Step 3: Validate the two Markdown files and final diff**

Run:

```powershell
rg -n "paddleocr-v2|OCR_LANGUAGE|cgcel|api-usage-flow" README.md README_CN.md
Test-Path screenshots\api-usage-flow.png
git diff --check
git diff -- README.md README_CN.md screenshots\api-usage-flow.png
```

Expected: no obsolete v2-branch, `OCR_LANGUAGE`, or `cgcel` references; the image path exists; and `git diff --check` produces no output.

- [ ] **Step 4: Run the focused route tests**

Run: `pytest test_api.py test_table_api.py -q`

Expected: the existing route-level tests pass without modifying application code.

- [ ] **Step 5: Commit the documentation update**

Run:

```powershell
git add README.md README_CN.md screenshots/api-usage-flow.png docs/superpowers/plans/2026-07-16-readme-refresh.md
git commit -m "docs: refresh bilingual README"
```

Expected: one commit containing only the README files, generated image, and implementation plan.
