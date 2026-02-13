# Repository Guidelines

## Project Structure & Modules
- `pdf_translator_project/` – Django project (settings, URLs, WSGI/ASGI).
- `translator/` – App with core logic: `pdf_layout.py` (layout‑preserving translation), `views.py`, `models.py`, `forms.py`, `urls.py`, templates and static assets.
- `translator/templates/translator/upload.html` – Upload UI.
- `translator/static/translator/` – CSS/JS.
- `manage.py` – Django entrypoint.
- `requirements.txt`, `setup.py`, `instalar_modelo_en_es.py` – Setup and model install.
- Ad‑hoc test scripts: `test_quick.py`, `test_analysis.py`, `test_redaction.py`.
- Media (runtime): `media/pdfs/`, `media/translated/` (created by setup).

## Build, Test, and Dev Commands
- Create venv: `python -m venv .venv && .venv\Scripts\activate` (Windows)
- Quick install: `python setup.py` (deps, model, migrate, media dirs)
- Manual install: `pip install -r requirements.txt && python instalar_modelo_en_es.py`
- DB migrations: `python manage.py migrate`
- Run server: `python manage.py runserver` → http://127.0.0.1:8000/
- Test scripts:
  - `python test_quick.py` – fast single‑page translate
  - `python test_analysis.py` – structure metrics compare
  - `python test_redaction.py` – redaction algorithm check

## Coding Style & Naming
- Python 3.8+; PEP8, 4‑space indent, `snake_case` for functions/vars, `PascalCase` for classes, Django apps/modules in `snake_case`.
- Keep `translator/pdf_layout.py` pure and layout‑preserving; do not change `replace_text_in_page(...)`/`translate_pdf_document(...)` signatures without updating callers.
- Use `os.path`/`pathlib` (avoid hardcoded absolute paths).

## Testing Guidelines
- Ensure Argos models are installed and sample PDFs exist under `media/pdfs/` before running scripts.
- Prefer small, reproducible inputs; commit only test code, not PDFs.
- If adding tests, follow `test_*.py` naming; place under project root or a `tests/` folder.

## Commit & Pull Request Guidelines
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`; scope optional (e.g., `feat(translator): ...`).
- PRs must include: concise description, rationale, manual test steps, screenshots for UI changes, and migrations when models change (`makemigrations` + `migrate`). Link related issues.

## Security & Configuration Tips
- Do not commit files under `media/` or large PDFs; keep inputs local.
- Validate file uploads and assume untrusted content. Avoid logging PII.
- If changing setup commands, update `QUICKSTART.md` accordingly.

