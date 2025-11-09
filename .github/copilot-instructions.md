# aiagent Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-09

## Active Technologies

- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (001-info-aggregation)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## API Usage & Provider Guidance

- Follow the project's API-First constitution: prefer authorized, documented API providers over scraping.
- See `docs/api-providers.md` for the canonical list of approved providers, credentials guidelines and
	cost/quotas. When adding a new provider, update `docs/api-providers.md` and add contract tests.
- For operational guidance and best practices, consult `BOCHA-GUIDE.md` (project-level engineering
	playbook) for monitoring, retries, and degradation strategies.

## Code Style

[e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]: Follow standard conventions

## Recent Changes

- 001-info-aggregation: Added [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
