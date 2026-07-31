# Contributing to CodeAtlas AI

Thank you for your interest in contributing to CodeAtlas AI! As an enterprise engineering intelligence platform, we hold our code quality, documentation, testing, and security to the highest standards.

---

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct (detailed in [CODE_OF_CONDUCT.md](file:///d:/CodeAtlas%20AI/CODE_OF_CONDUCT.md)).

---

## Development Environment Setup

1. Fork and clone the repository.
2. Setup the backend virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Setup the frontend node modules:
   ```bash
   cd ../frontend
   npm install
   ```
4. Copy the environment variables:
   ```bash
   cp ../.env.example ../.env
   ```

---

## Branching & Pull Request Process

1. Create a branch from `main` using descriptive names:
   * `feature/your-feature-name`
   * `bugfix/issue-description`
   * `docs/documentation-update`
2. Write clean code adhering to our Coding Standards (Clean Architecture, SOLID, DRY).
3. Ensure unit tests are added in the `backend/tests/` or `frontend/src/__tests__/` directory.
4. Verify tests pass:
   ```bash
   # Backend tests
   pytest
   ```
5. Submit a Pull Request (PR) describing:
   * The purpose of the changes.
   * What was tested and how to manually verify the code.
   * Any configuration updates or migrations.

---

## Coding Standards

### Backend (Python)
* Follow **PEP 8** style guidelines.
* Run code formatters and checkers (`black`, `flake8`, `mypy`) before committing.
* Enforce Clean Architecture layouts: keep use cases isolated from framework APIs (FastAPI/SQLAlchemy).

### Frontend (React)
* Use modern functional components with hooks.
* Prefer Vanilla CSS classes in stylesheets rather than ad-hoc inline styles.
* Write reusable components and structure state management within designated Context layouts.

---

## Writing Parsing Plugins

CodeAtlas AI supports extensible parsing through the `BaseIngestPlugin` base class. If you are adding support for a new language:
1. Create your class in `backend/app/adapters/plugins/<language>_plugin.py`.
2. Inherit from `BaseIngestPlugin`.
3. Implement `detect_language()`, `parse_file()`, and `extract_relations()`.
4. Register your plugin in the Ingestion Plugin Manager.
5. Add unit tests for your parser under `backend/tests/plugins/`.

---

## Security Reporting

Do **not** report security vulnerabilities via public Github issues. Refer to [SECURITY.md](file:///d:/CodeAtlas%20AI/SECURITY.md) for instructions on private disclosures.
