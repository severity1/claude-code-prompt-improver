# Test Prompts

Test cases for the prompt optimizer.

## Should Optimize (Vague Prompts)

### Very Short
- `fix it`
- `add tests`
- `broken`

### Generic References
- `fix the bug`
- `update the code`
- `improve performance`

### Missing Context
- `add authentication` (no method specified)
- `fix the error` (no error details)
- `refactor the app` (no scope)

### Ambiguous Scope
- `update the tests` (which tests?)
- `fix the map` (what's wrong?)
- `add dark mode` (where? how?)

## Should NOT Optimize (Clear Prompts)

### Specific Files + Clear Intent
- `Fix the TypeScript error in src/components/Map.tsx line 127`
- `Add a new amenity type 'cafe' to src/stores/configStore.ts with OSM tag leisure=cafe`
- `Refactor the fetchPOIs function in src/services/osmService.ts to use async/await`

### Detailed Requirements
- `Implement JWT authentication with login/signup UI, token refresh, and localStorage persistence`
- `Add unit tests for the DualRangeSlider component covering min/max validation and overlap prevention`

### Questions (Information Requests)
- `Explain how the Mapbox GL JS map instance is managed in Map.tsx`
- `What's the difference between configStore and local component state?`
- `How does the OSM service handle rate limiting?`

## Bypass Commands

### Explicit Bypass
- `! add dark mode` → Should skip optimization
- `! fix` → Should skip optimization (even though vague)

### Strict Mode
- `@strict implement authentication` → Should always optimize
- `@strict fix Map.tsx` → Should always optimize (even if clear)

## Expected Subagent Questions

### For "fix the map"
1. "What's wrong with the map?"
   - Not loading
   - Markers missing
   - Bounds incorrect
   - Other

2. If "Markers missing":
   "Which markers?"
   - User location
   - Amenities (POIs)
   - Both

### For "add authentication"
1. "Which authentication method?"
   - OAuth 2.0
   - JWT
   - Session cookies

2. "What should it include?" (multi-select)
   - Login UI
   - Signup UI
   - Protected routes
   - Token refresh
   - Logout functionality

### For "add tests"
1. "What type of tests?"
   - Unit tests
   - Integration tests
   - E2E tests
   - Component tests

2. "For which component/feature?"
   - (Subagent should Grep for testable components)

## Integration Tests

### Test Input Format
```json
{
  "session_id": "test-123",
  "transcript_path": "/tmp/test-transcript.jsonl",
  "cwd": "/home/user/project",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "fix the map"
}
```

### Expected Output Format
Wrapped prompt that instructs Claude to spawn subagent with specific evaluation criteria.
