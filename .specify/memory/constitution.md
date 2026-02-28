# FarmOS Constitution

## Core Principles

### I. Farmer-First Reliability (NON-NEGOTIABLE)

Every system decision must prioritize reliability, correctness, and trustworthiness for farmers.

* Financial predictions, crop analysis, and recommendations must be deterministic, explainable, and traceable.
* No feature may be deployed without validated correctness under real-world scenarios.
* All AI-generated outputs must be auditable, reproducible, and linked to source inputs and tool calls.
* System failures must degrade gracefully without data loss or misleading outputs.
* Incorrect financial or crop recommendations are considered critical system failures.

---

### II. Testing (MANDATORY)

All functionality must follow strict test-first principles.

* All UI screen implementations must be tested using playright server
* Include logs in most of the places, this will help github copilot coding agent

### III. Deterministic and Observable AI Systems

All AI-driven functionality must be observable, deterministic, and debuggable.

* Every AI request must log:

  * input
  * output
  * tool calls
  * execution time
  * errors
* AI decisions must never silently fail.
* All AI outputs must include confidence and trace metadata.
* Tool-based architecture is mandatory. LLMs must not directly hallucinate financial or crop values without tool verification.

All AI workflows must be reproducible.

---

### IV. Consistent and Accessible User Experience

The user experience must remain consistent, predictable, and optimized for farmers with limited technical experience.

* Interfaces must be simple, minimal, and action-oriented.
* Every screen must answer at least one of:

  * What is happening?
  * What should the farmer do?
  * How does this affect profit or risk?
* UI must support localization and language independence.
* UI response latency must remain below 300ms for interactive elements.
* No breaking UX changes without migration strategy.

Remix components must follow shared design system standards.

---

### V. Modular and Maintainable Architecture

All code must be modular, testable, and independently maintainable.

Required architectural separation:

* Remix: UI layer only
* Python backend: business logic and AI orchestration
* Supabase: persistence layer only
* AI tools: mistral ai package

Every module must:

* have a single responsibility
* be independently testable
* avoid tight coupling

No hidden dependencies allowed.

---

### VII. Data Integrity and Safety

Farmer data is critical and must be protected.

* No silent data corruption allowed
* All writes must be validated
* All financial data must be versioned
* All destructive actions must be reversible

Supabase schemas must enforce integrity constraints.

---

## Technical Standards and Constraints

### Required Stack

- The app must be locally runable using docker compose, mainly docker-compose.dev, so reload happens.
- The app must readily deployable to clouflare

Frontend:

* Remix
* UI must be mobile and desktop compatible
* TypeScript mandatory
* No untyped code

Backend:

* Python 3.11+
* uv package manager
* FastAPI recommended
* Fully typed

Database:

* Supabase PostgreSQL

Deployment:

* Cloudflare Workers / Containers

AI:

* Mistral via OpenAI-compatible client
* Tool-based architecture required

---

### Logging and Observability

All systems must include:

* structured logging
* error tracking
* trace IDs
* AI tool call traces

Failures must be diagnosable within minutes.

---

This constitution ensures FarmOS remains reliable, scalable, and trusted by farmers.

---

**Version**: 1.0.0
**Ratified**: 2026-02-28
**Last Amended**: 2026-02-28
