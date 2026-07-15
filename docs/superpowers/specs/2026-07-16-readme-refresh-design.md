# README refresh design

## Goal

Rewrite `README.md` and `README_CN.md` so they accurately describe the current PaddleOCRFastAPI application and help a new user run and call it quickly.

## Scope

- Align both README files around the current project state: PaddleOCR 3.7.0 and the Python 3.12 Docker image.
- Remove obsolete PaddleOCR 2.x branch-selection guidance and outdated language-configuration instructions.
- Document the available OCR, table-recognition, and PDF OCR capabilities from the current FastAPI routes.
- Include concise local and Docker quick-start instructions, plus runnable request examples.
- Generate one repository-owned horizontal visual explaining the user flow: provide a document or image, call the API, receive extracted text or tables.
- Store the asset in `screenshots/` and reference it from both README files.

## Content structure

1. Project overview and current-version support.
2. User-flow image with no technical architecture diagram.
3. Features and supported inputs.
4. Local quick start and Docker quick start.
5. API reference with request and response examples based on actual routes.
6. Link to Swagger UI, repository tests, and license.

## Visual direction

Create a clean landscape documentation illustration. It should show three large steps with legible, minimal labels: image/PDF input, a simple API request, and text/table results. Use a blue and white palette inspired by API documentation, with no logo, watermark, decorative source-code background, or infrastructure diagram.

## Verification

- Cross-check every command, version, endpoint, request field, and response example against the repository.
- Confirm the generated image exists under `screenshots/` and Markdown links resolve from both README files.
- Inspect the final diff and run the narrowest relevant documentation checks available (Markdown link/path checks).

## Out of scope

- Application code, dependency upgrades, Docker/runtime behavior changes, API redesign, and unrelated documentation cleanup.
