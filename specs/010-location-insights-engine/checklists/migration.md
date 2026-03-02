# Migration Checklist: new_sample_ui → frontend (Full-Stack Fit & File Mapping)

**Purpose**: Migration gate — validate that the plan to replace the Remix/SSR frontend with the Vite/SPA `new_sample_ui` is complete, unambiguous, and safe to execute before any files are modified.
**Created**: 2026-03-01
**Feature**: [spec.md](../spec.md)
**Scope**: Full-stack (source + package.json + vite/tailwind configs + Docker/Compose/infra)

UI must be both mobile and laptop compatible
---

## Requirement Completeness — Framework Replacement

- [ ] CHK001 — Is there a documented decision to fully replace Remix SSR with a Vite SPA, or is the new UI intended to coexist with the Remix shell? [Completeness, Gap]
- [ ] CHK002 — Are the Remix-specific entry points (`entry.client.tsx`, `entry.server.tsx`) explicitly listed as files to be deleted in the migration plan? [Completeness, Gap]
- [ ] CHK003 — Is `root.tsx` (Remix root route with `<Links>`, `<Meta>`, `<Outlet>`) accounted for — either mapped to the new `App.tsx` or explicitly discarded? [Completeness, Gap]
- [ ] CHK004 — Is there a plan for every Remix route file (`_index.tsx`, `farm.$farmId.*.tsx`) — either explicitly deprecated or replaced by a tab/component equivalent in `Dashboard.tsx`? [Completeness, Gap]
- [ ] CHK005 — Is `index.html` (required SPA entry point for Vite, absent in current frontend root) listed as a file to add? [Completeness, Gap]

---

## Requirement Completeness — File Mapping

- [ ] CHK006 — Is a complete, explicit 1-to-1 or N-to-1 mapping defined from every `new_sample_ui/src/**` file to its destination in `frontend/`? [Completeness, Gap]
- [ ] CHK007 — Is the destination directory structure (`frontend/src/` vs the current `frontend/app/`) explicitly defined? [Completeness, Ambiguity]
- [ ] CHK008 — Is `src/store/useFarmStore.ts` mapped to a destination that won't conflict with the existing `app/contexts/auth.tsx` Supabase-backed session state? [Completeness, Conflict]
- [ ] CHK009 — Are `src/data/mockFarmData.ts` and `src/services/ai.ts` explicitly mapped rather than assumed to just copy into place? [Completeness]
- [ ] CHK010 — Is `src/lib/utils.ts` (`cn` helper) mapped to a shared utility location consistent with any existing `frontend/app/utils/` conventions? [Completeness, Consistency]

---

## Requirement Clarity — Dependency Changes

- [ ] CHK011 — Is the `package.json` replacement clearly specified, distinguishing which new dependencies are additive vs. which existing ones (`@remix-run/*`, `isbot`) must be removed? [Clarity, Spec §package.json]
- [ ] CHK012 — Is the Tailwind version upgrade (v3 → v4) explicitly documented? The new UI uses `@tailwindcss/vite` (a Vite plugin) and the CSS `@theme` directive — incompatible with the existing `tailwind.config.ts` and `postcss.config.js`. [Clarity, Conflict]
- [ ] CHK013 — Is the React version change (18 → 19) noted, and are incompatibilities with `@types/react` and other peer deps identified? [Clarity]
- [ ] CHK014 — Is the meaning of `"motion": "^12.x"` (Framer Motion v12 re-branded as `motion`) documented for the developer, given the current project has no animation dependency? [Clarity]
- [ ] CHK015 — Is retention or removal of the `playwright` test setup (`@playwright/test`, `playwright.config.ts`, `tests/`) explicitly addressed in the migration plan? [Completeness, Gap]

---

## Requirement Clarity — Configuration Files

- [ ] CHK016 — Is the new `vite.config.ts` clearly specified to either preserve or intentionally drop the `/api` reverse proxy (`target: "http://farmops-backend-dev:8000"`) present in the current config? [Clarity, Conflict]
- [ ] CHK017 — Is the `tsconfig.json` replacement specified, given the current one uses Remix types (`"types": ["@remix-run/node", "vite/client"]`) and path aliases (`"~/*": ["./app/*"]`) incompatible with the SPA structure? [Clarity]
- [ ] CHK018 — Is the `postcss.config.js` file's fate (deletion or retention) explicitly stated? It is required for Tailwind v3 but unnecessary and potentially conflicting with Tailwind v4's Vite plugin approach. [Clarity, Conflict]
- [ ] CHK019 — Is the `tailwind.config.ts` deletion explicitly required? The new UI's Tailwind v4 setup uses CSS `@theme` for all custom tokens (`--color-farm-green`, `--color-cream`, etc.) and does not use a JS config file. [Clarity, Conflict]
- [ ] CHK020 — Is the `wrangler.toml` (Cloudflare Workers config in the repo root) in scope or explicitly out of scope for this migration? [Clarity, Assumption]

---

## Requirement Consistency — Docker & Infra

- [ ] CHK021 — Is `Dockerfile.frontend` updated to reflect that the new UI is a static SPA? The current Dockerfile uses `remix-serve ./build/server/index.js` for production — there is no server bundle in a Vite SPA. [Consistency, Conflict]
- [ ] CHK022 — Are `docker-compose.dev.yml` and `docker-compose.prod.yml` reviewed for any Remix-specific startup commands or mount paths that must change? [Consistency]
- [ ] CHK023 — Is a static file server (e.g., `vite preview`, `serve`, or nginx) specified for the production Docker stage, replacing `remix-serve`? [Completeness, Gap]

---

## Requirement Consistency — Backend Contract

- [ ] CHK024 — Is it documented that the new UI entirely replaces Supabase-backed API calls with mock data (`mockFarmData.ts` + Zustand store)? If so, is this intentional for the current migration scope or do live API calls need to be wired up? [Completeness, Assumption]
- [ ] CHK025 — Are the existing backend API route contracts (`/api/farms`, `/api/snapshot`, etc. defined in `backend/src/api/routes/`) validated against the data shapes assumed by `useFarmStore.ts` and `types.ts`? [Consistency, Gap]
- [ ] CHK026 — Does `app/contexts/auth.tsx` (Supabase session/JWT management) have an equivalent in the new UI? If silent removal is intended, is that decision documented? [Completeness, Conflict]
- [ ] CHK027 — Is the `FarmLocation` type in the new `types.ts` (`{ lat, lng, address?, city?, country? }`) consistent with how location data is stored and returned by the backend `location_profile` model? [Consistency, Gap]

---

## Security & Environment Requirements

- [ ] CHK028 — Is it specified where `GEMINI_API_KEY` will be sourced (`.env`, Docker secret, CI/CD variable) given the new `vite.config.ts` inlines it as `process.env.GEMINI_API_KEY` into the client bundle? [Completeness, Gap]
- [ ] CHK029 — Is the security implication of calling Gemini API directly from the browser (key exposed in client bundle) acknowledged and accepted or mitigated with a proxy? [Clarity, Assumption]
- [ ] CHK030 — Is the `.env.example` from `new_sample_ui/` mapped to `frontend/.env.example` and committed? [Completeness, Gap]

---

## Acceptance Criteria Quality

- [ ] CHK031 — Are acceptance criteria for the migration itself defined (e.g., "app renders correctly in Docker dev environment", "all existing Playwright smoke tests pass or are replaced")? [Acceptance Criteria, Gap]
- [ ] CHK032 — Is a rollback strategy documented in case the migration breaks the Docker dev stack mid-way? [Gap, Exception Flow]
- [ ] CHK033 — Is the SLA requirement from the spec (`<3s cached, <8s cold AI call`) still measurable with the new SPA approach, and is there a plan to verify it? [Acceptance Criteria, Spec §US1]

---

## Scenario Coverage — Edge Cases

- [ ] CHK034 — Is the behavior defined when `GEMINI_API_KEY` is missing or invalid? `FarmSketch` and `ai.ts` will call Gemini — is a graceful fallback specified? [Coverage, Edge Case]
- [ ] CHK035 — Is the behavior defined for a cold-start (no farm data in Zustand store) given the store is initialized with `DEFAULT_FARM` mock data — is this intentional for production? [Coverage, Assumption]
- [ ] CHK036 — Are the `react-day-picker` CSS import (`import 'react-day-picker/dist/style.css'`) and `recharts` rendering requirements validated against the Tailwind v4 CSS reset? Direct CSS imports can conflict with Tailwind's base layer. [Coverage, Gap]

---

## Ambiguities & Conflicts

- [ ] CHK037 — The new `App.tsx` defaults to `step = 'dashboard'` (skips onboarding), but `Onboarding` and `FarmSketch` still exist. Is there a requirement for when onboarding should trigger (first launch, new farm)? [Ambiguity]
- [ ] CHK038 — `CropPlanning.tsx` imports `addCrop` and `updateCrop` from `useFarmStore`, but the spec (§US2) calls for a backend-powered recommendation pipeline. Is the Zustand-only implementation a temporary mock or the final intended approach? [Ambiguity, Spec §US2]
- [ ] CHK039 — The `InventoryTab.tsx` feature has no corresponding user story in `spec.md`. Is it in scope for this feature branch or should it be excluded to keep the PR focused? [Ambiguity, Gap]
- [ ] CHK040 — `MOCK_SCHEMES` hardcodes eligible schemes (PM-KISAN, TNAU subsidy). Is this the accepted placeholder for the subsidy eligibility engine, or does it need to be derived from the backend? [Ambiguity, Spec §Subsidies]

---

## Notes

- Mark items `[x]` as confirmed/resolved before starting migration.
- Items marked `[Gap]` indicate missing documentation that should be written before touching files.
- Items marked `[Conflict]` indicate cases where the new UI directly contradicts an existing assumption — resolve before migrating.
- Each `/speckit.checklist` run creates a new file; this file is `migration.md`.
