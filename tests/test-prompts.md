# Test Prompts

Test cases for the prompt optimizer focusing on context-aware suggestions.

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
- `! add dark mode` → Should skip evaluation entirely (pass through as-is)
- `! fix` → Should skip evaluation (even though vague)

Note: All other prompts (without `!`) will spawn a subagent for evaluation. The subagent uses its judgment to decide if optimization is needed.

## Expected Subagent Behavior (Context-Aware)

The key principle: **Questions must include specific options discovered from the actual codebase.**

### For "fix the map"

**Subagent should:**
1. Glob for map-related files: `**/*map*.{ts,tsx,js,jsx}`
2. Grep for map components and state
3. Check recent git changes to map files
4. Ask with DISCOVERED options:

```
Question: "Which map component needs fixing?"
Options (based on what it found):
  - src/components/Map.tsx (main map component, 342 lines)
  - src/components/MapMarkers.tsx (marker rendering, 89 lines)
  - src/stores/mapStore.ts (map state management, 156 lines)
  - src/hooks/useMapBounds.ts (bounds calculation hook, 45 lines)
```

**NOT generic options like:**
```
❌ Bad: [Component A | Component B | Component C]
```

5. After synthesizing, show the optimized prompt and confirm:
```
"I've optimized your prompt to:

'Fix the Map component in src/components/Map.tsx: investigate why markers
are not rendering after the recent Mapbox GL update. Check the marker
layer initialization in the useEffect hook at line 127.'

Happy with this?"
Options:
  - Yes, use this
  - Needs adjustment
  - Use original instead
```

### For "add authentication"

**Subagent should:**
1. Check package.json for existing auth libraries
2. Grep for existing auth patterns
3. Read CLAUDE.md for auth conventions
4. Glob for auth-related files
5. Ask with CONTEXT:

```
Question: "I don't see any existing auth implementation. Which method?"
Options:
  - OAuth 2.0 (requires provider like Google/GitHub)
  - JWT (stateless, token-based)
  - Session cookies (server-side sessions)
```

Then if JWT selected:
```
Question: "What should the auth system include?" (multi-select)
Options based on typical patterns + project structure:
  - Login/signup UI (add to src/components/auth/)
  - Protected route wrapper (integrate with existing router in src/App.tsx)
  - Auth context/store (follow Zustand pattern from src/stores/)
  - Token refresh logic
  - localStorage persistence
```

### For "add tests"

**Subagent should:**
1. Glob for existing test files to understand test patterns
2. Glob for testable components
3. Check test framework in package.json
4. Ask with ACTUAL components:

```
Question: "Which component should I add tests for?"
Options (discovered from src/components/):
  - DualRangeSlider.tsx (complex logic, no tests yet)
  - MapMarkers.tsx (rendering logic, has partial tests)
  - SearchBar.tsx (user input, no tests)
  - FilterPanel.tsx (state management, no tests)
```

Then:
```
Question: "What type of tests? (Project uses Jest + React Testing Library)"
Options:
  - Unit tests (component logic)
  - Integration tests (component interactions)
  - Snapshot tests (UI regression)
```

### For "fix the error"

**Subagent should:**
1. Check recent git changes for modified files
2. Grep for error handling patterns (try/catch, .catch, etc.)
3. Look for console.error or logging
4. Ask:

```
Question: "Which error? (Found these in recently modified files)"
Options:
  - TypeError in src/components/Map.tsx (modified 2 hours ago)
  - Network error in src/services/osmService.ts (has .catch handlers)
  - [Other - I'll paste the error message]
```

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
Wrapped prompt that instructs Claude to:
1. Spawn subagent for evaluation
2. Subagent explores codebase (using its judgment on how)
3. Subagent asks context-aware questions if needed
4. Subagent shows optimized prompt and asks for user confirmation
5. Returns approved prompt or original

### Validation Criteria

**Good subagent behavior:**
- ✅ Uses Glob/Grep to discover actual files before asking
- ✅ Provides specific file paths and descriptions as options
- ✅ Tailors questions to the specific project architecture
- ✅ Uses multi-select when multiple items might be relevant
- ✅ Shows optimized prompt and asks for user confirmation
- ✅ Offers "Use original instead" option during confirmation
- ✅ Returns unchanged if already clear

**Bad subagent behavior:**
- ❌ Asks generic questions without exploring first
- ❌ Provides placeholder options like [Option 1 | Option 2]
- ❌ Doesn't use available tools to gather context
- ❌ Over-optimizes simple, clear requests
- ❌ Asks for information already in the prompt
