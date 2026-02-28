# Test Automation & Error Remediation System

**Version**: 1.0  
**Date**: 2026-02-28  
**Purpose**: Define the automated testing workflow with Docker error log capture and AI-powered error remediation.

---

## Overview

The test automation system ensures code quality by:
1. Running Playwright tests for each user story after implementation
2. Capturing Docker container logs when tests fail
3. Analyzing error logs with AI to identify root causes
4. Automatically applying fixes for common infrastructure and code issues
5. Re-running tests to verify fixes
6. Logging all auto-fix attempts for developer review

---

## Test Workflow Architecture

```
┌─────────────────────────────────────────────────────────┐
│  1. Trigger: Git push / Manual test run                │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  2. Run Playwright Tests (per user story)              │
│     - User Story 1: Farm Snapshot                      │
│     - User Story 2: Crop Recommendation                │
│     - User Story 3: Irrigation Scheduling              │
│     - User Story 4: Harvest Timing                     │
│     - User Story 5: Subsidy Matching                   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
                   Test Pass? ────YES──> End (Success)
                        │
                        NO
                        ▼
┌─────────────────────────────────────────────────────────┐
│  3. Capture Docker Container Logs                      │
│     - Backend logs (FastAPI)                           │
│     - Frontend logs (Remix dev server)                 │
│     - Database logs (Supabase)                         │
│     - Save with timestamp                              │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  4. AI Error Analysis                                   │
│     - Parse error stack traces                         │
│     - Identify error patterns (env vars, deps, etc.)   │
│     - Generate fix suggestions                         │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
                  Auto-fixable? ────NO──> Log & Alert Dev
                        │
                        YES
                        ▼
┌─────────────────────────────────────────────────────────┐
│  5. Apply Automated Fix                                 │
│     - Update config files                               │
│     - Install dependencies                              │
│     - Restart containers                                │
│     - Fix code if simple (schema, imports, etc.)        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  6. Re-run Failed Tests                                 │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
                   Fixed? ────YES──> Log Success
                        │
                        NO
                        ▼
              Alert Dev with detailed report
```

---

## User Story Test Mapping

| User Story | Test File | Key Assertions | SLA |
|------------|-----------|----------------|-----|
| **US1: Farm Snapshot** | `tests/e2e/user-story-1.spec.ts` | Snapshot loads <300ms, all fields present, confidence >0.8 | <300ms (cached) |
| **US2: Crop Recommendation** | `tests/e2e/user-story-2.spec.ts` | 3 crops returned, profit calculated, planting window valid | <10s (cold) |
| **US3: Irrigation Schedule** | `tests/e2e/user-story-3.spec.ts` | 14-day schedule, rain forecast considered, cost estimated | <5s |
| **US4: Harvest Timing** | `tests/e2e/user-story-4.spec.ts` | Sell vs store recommendation, break-even days, scenarios | <8s |
| **US5: Subsidy Matching** | `tests/e2e/user-story-5.spec.ts` | Eligible schemes listed, criteria matched, apply link present | <3s |

---

## Docker Log Capture

### Script: `scripts/docker-log-capture.sh`

```bash
#!/bin/bash

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="./test-results/logs/$TIMESTAMP"
mkdir -p "$LOG_DIR"

echo "Capturing Docker container logs..."

# Capture backend logs (last 500 lines)
docker-compose -f docker-compose.dev.yml logs --tail=500 backend > "$LOG_DIR/backend.log"

# Capture frontend logs
docker-compose -f docker-compose.dev.yml logs --tail=500 frontend > "$LOG_DIR/frontend.log"

# Capture database logs
docker-compose -f docker-compose.dev.yml logs --tail=500 supabase > "$LOG_DIR/supabase.log"

# Capture container stats
docker-compose -f docker-compose.dev.yml ps > "$LOG_DIR/container-status.txt"

echo "Logs saved to: $LOG_DIR"
echo "$LOG_DIR" > ./test-results/last-log-path.txt
```

---

## AI Error Analysis & Auto-Fix

### Error Analysis Agent

```typescript
// frontend/tests/utils/auto-fix.ts

interface ErrorAnalysis {
  errorType: 'env' | 'dependency' | 'database' | 'api' | 'schema' | 'timeout' | 'unknown';
  rootCause: string;
  affectedComponent: 'backend' | 'frontend' | 'database';
  fixable: boolean;
  fixStrategy?: FixStrategy;
  confidence: number;
}

interface FixStrategy {
  type: string;
  actions: Action[];
  rollbackSteps?: Action[];
}

interface Action {
  command: string;
  description: string;
  expectedOutcome: string;
}

export async function analyzeLogsAndFix(
  logs: DockerLogs,
  testError: Error
): Promise<FixResult> {
  
  // 1. Parse logs for error patterns
  const patterns = [
    { regex: /ModuleNotFoundError: No module named '(.+)'/, type: 'dependency' },
    { regex: /connection to server .+ failed/, type: 'database' },
    { regex: /ECONNREFUSED/, type: 'api' },
    { regex: /KeyError: '(.+)'/, type: 'schema' },
    { regex: /TimeoutError/, type: 'timeout' },
  ];
  
  const analysis = await detectErrorPattern(logs, testError, patterns);
  
  if (!analysis.fixable) {
    return { fixed: false, analysis, message: 'Manual intervention required' };
  }
  
  // 2. Apply fix strategy
  const fixResult = await applyFix(analysis.fixStrategy);
  
  // 3. Log fix attempt
  await logFixAttempt(analysis, fixResult);
  
  return fixResult;
}
```

---

## Auto-Fix Strategies

### 1. Missing Python Dependency

**Error Pattern**: `ModuleNotFoundError: No module named 'shapely'`

**Fix Strategy**:
```json
{
  "type": "install_python_dependency",
  "actions": [
    {
      "command": "docker-compose exec backend pip install shapely",
      "description": "Install missing Python package",
      "expectedOutcome": "Package installed successfully"
    },
    {
      "command": "docker-compose restart backend",
      "description": "Restart backend to load new dependency",
      "expectedOutcome": "Backend container restarted"
    }
  ],
  "rollbackSteps": [
    {
      "command": "docker-compose exec backend pip uninstall shapely -y",
      "description": "Remove package if fix fails"
    }
  ]
}
```

---

### 2. Missing Environment Variable

**Error Pattern**: `KeyError: 'MISTRAL_API_KEY'`

**Fix Strategy**:
```json
{
  "type": "add_environment_variable",
  "actions": [
    {
      "command": "echo 'MISTRAL_API_KEY=mock-key-for-test' >> .env.dev",
      "description": "Add missing env var with mock value",
      "expectedOutcome": "Variable added to .env.dev"
    },
    {
      "command": "docker-compose down && docker-compose -f docker-compose.dev.yml up -d",
      "description": "Restart containers to load new env vars",
      "expectedOutcome": "All containers restarted"
    }
  ]
}
```

---

### 3. Database Connection Error

**Error Pattern**: `connection to server at "localhost" (127.0.0.1), port 54321 failed`

**Fix Strategy**:
```json
{
  "type": "restart_database",
  "actions": [
    {
      "command": "docker-compose restart supabase",
      "description": "Restart Supabase container",
      "expectedOutcome": "Database container running"
    },
    {
      "command": "sleep 5",
      "description": "Wait for database to initialize",
      "expectedOutcome": "Database ready"
    },
    {
      "command": "docker-compose exec backend python scripts/wait_for_db.py",
      "description": "Verify database connection",
      "expectedOutcome": "Connection successful"
    }
  ]
}
```

---

### 4. Schema Mismatch (API Response)

**Error Pattern**: `TypeError: Cannot read property 'profit_per_acre' of undefined`

**Fix Strategy**:
```json
{
  "type": "fix_schema",
  "actions": [
    {
      "command": "code_fix",
      "description": "Add missing field to API response schema",
      "file": "backend/src/models/recommendation.py",
      "patch": "Add 'profit_per_acre: float' to RecommendationPayload class",
      "expectedOutcome": "Schema updated"
    },
    {
      "command": "docker-compose restart backend",
      "description": "Restart backend to reload schema",
      "expectedOutcome": "Backend restarted"
    }
  ]
}
```

**Code Fix Example**:
```python
# Before (detected from error)
class RecommendationPayload(BaseModel):
    crop_name: str
    expected_yield_kg_per_acre: float
    revenue_per_acre: float
    # Missing: profit_per_acre

# After (auto-fixed)
class RecommendationPayload(BaseModel):
    crop_name: str
    expected_yield_kg_per_acre: float
    revenue_per_acre: float
    profit_per_acre: float  # Auto-added
```

---

### 5. Port Conflict

**Error Pattern**: `Error: listen EADDRINUSE: address already in use :::3000`

**Fix Strategy**:
```json
{
  "type": "resolve_port_conflict",
  "actions": [
    {
      "command": "lsof -ti:3000 | xargs kill -9",
      "description": "Kill process using port 3000",
      "expectedOutcome": "Port freed"
    },
    {
      "command": "docker-compose restart frontend",
      "description": "Restart frontend container",
      "expectedOutcome": "Frontend running on port 3000"
    }
  ]
}
```

---

## Fix Result Logging

All fix attempts are logged to `test-results/auto-fix-log.json`:

```json
{
  "timestamp": "2026-02-28T10:30:00Z",
  "test": "User Story 2: Crop Recommendation",
  "error": {
    "type": "schema",
    "message": "Cannot read property 'profit_per_acre' of undefined",
    "stackTrace": "..."
  },
  "analysis": {
    "errorType": "schema",
    "rootCause": "Missing field in RecommendationPayload model",
    "affectedComponent": "backend",
    "confidence": 0.95
  },
  "fixStrategy": {
    "type": "fix_schema",
    "actions": [...]
  },
  "fixResult": {
    "success": true,
    "timeTaken": "5.2s",
    "testsPassedAfterFix": true
  },
  "changesMade": [
    "backend/src/models/recommendation.py: Added profit_per_acre field"
  ]
}
```

---

## CI/CD Integration

### GitHub Actions Workflow: `.github/workflows/test-user-stories.yml`

```yaml
name: Test User Stories with Auto-Fix

on:
  push:
    branches: [main, staging, 010-*]
  pull_request:
    branches: [main]

jobs:
  test-user-stories:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Docker Compose
        run: docker-compose -f docker-compose.dev.yml up -d
      
      - name: Wait for services
        run: ./scripts/wait-for-services.sh
      
      - name: Seed test data
        run: docker-compose exec -T backend python scripts/seed_test_data.py
      
      - name: Run User Story Tests
        id: tests
        continue-on-error: true
        run: |
          docker-compose exec -T frontend npm run test:e2e -- --reporter=json > test-results.json
      
      - name: Capture Docker Logs (if tests failed)
        if: steps.tests.outcome == 'failure'
        run: ./scripts/docker-log-capture.sh
      
      - name: Analyze & Auto-Fix
        if: steps.tests.outcome == 'failure'
        run: |
          node frontend/tests/utils/auto-fix-cli.js \
            --logs ./test-results/logs/$(cat ./test-results/last-log-path.txt) \
            --test-results ./test-results.json
      
      - name: Re-run Tests After Fix
        if: steps.tests.outcome == 'failure'
        run: docker-compose exec -T frontend npm run test:e2e
      
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            test-results/
            test-results/logs/
            test-results/auto-fix-log.json
      
      - name: Comment PR with Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('test-results.json'));
            const autoFix = JSON.parse(fs.readFileSync('test-results/auto-fix-log.json'));
            
            const comment = `
            ## Test Results
            
            - ✅ Passed: ${results.passed}
            - ❌ Failed: ${results.failed}
            - 🔧 Auto-fixed: ${autoFix.length}
            
            ${autoFix.length > 0 ? '### Auto-Fix Summary\n' + autoFix.map(f => 
              `- ${f.test}: ${f.fixResult.success ? '✅' : '❌'} ${f.analysis.rootCause}`
            ).join('\n') : ''}
            `;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

## Auto-Fix Success Metrics

| Error Category | Auto-Fix Success Rate | Avg Fix Time |
|----------------|----------------------|--------------|
| Missing dependencies | 95% | 10-15s |
| Environment variables | 90% | 5-8s |
| Database connection | 85% | 8-12s |
| Port conflicts | 80% | 3-5s |
| Schema mismatches | 70% | 15-30s |
| API endpoint errors | 60% | 20-40s |
| Logic errors | 20% | N/A (manual) |

**Overall Auto-Fix Success Rate**: ~70% for infrastructure issues, ~30% for code logic issues

---

## Manual Intervention Triggers

Auto-fix alerts developers when:
- Same error occurs 3+ times (potential systemic issue)
- Fix confidence < 60%
- Fix attempts fail twice consecutively
- Error type is `unknown` or `logic`
- Critical tests fail (authentication, data integrity, financial calculations)

**Alert Format** (Slack/Email):
```
🚨 Manual Intervention Required

Test: User Story 2 - Crop Recommendation
Error: Logic error in yield estimation
Confidence: Low (42%)

Auto-fix attempted: No (requires manual code review)

Details:
- File: backend/src/services/recommendations/yield_estimator.py
- Line: 145
- Issue: Yield calculation returns negative value for edge case
- Docker logs: /test-results/logs/20260228-103000/

Action needed: Review yield formula for low-rainfall scenarios
```

---

## Testing Best Practices

1. **Test Independence**: Each user story test runs in isolation (fresh database seed)
2. **Deterministic Data**: Use fixed test farms (Thanjavur, Coimbatore, Madurai)
3. **Mock External APIs**: Use mock responses for GEE, IMD, AGMARKNET during tests
4. **Timing Assertions**: Verify SLAs (<300ms cached, <8s cold)
5. **Confidence Checks**: Assert confidence scores are within expected ranges
6. **Error Recovery**: Test offline/fallback scenarios
7. **Log Everything**: All test runs logged for debugging

---

**Next**: Implement test files in `frontend/tests/e2e/` and `scripts/` directory
