# Comprehensive Examples of Prompt Improvement

This reference provides real-world examples showing the complete flow from vague prompts through research, question formulation, and execution.

## Table of Contents

- [Example Format](#example-format)
- [Vague Prompts (Research Required)](#vague-prompts-research-required)
- [Clear Prompts (Proceed Immediately)](#clear-prompts-proceed-immediately)
- [Bypass Prompts (Pass Through)](#bypass-prompts-pass-through)
- [Context-Dependent Prompts](#context-dependent-prompts)
- [Complex Multi-Question Scenarios](#complex-multi-question-scenarios)

## Example Format

Each example follows this structure:

1. **Original Prompt**: What the user said
2. **Evaluation**: Clarity assessment
3. **Research Plan** (if vague): What to investigate
4. **Research Findings** (if vague): What was discovered
5. **Questions Asked** (if vague): AskUserQuestion tool call
6. **User Answers** (if vague): What user selected
7. **Execution**: How the request was fulfilled

## Vague Prompts (Research Required)

### Example 1: Generic Bug Fix

**Original Prompt:**
```
fix the bug
```

**Evaluation:**
- Target: ❌ (no file, function, or bug specified)
- Action: ❌ (what needs fixing?)
- Criteria: ~ (bug fixed, but which bug?)
- Context: Check conversation history

**Conversation History Check:**
No recent error messages, no file viewing context.

**Decision:** RESEARCH REQUIRED

**Research Plan:**
```
1. Search for TODO/FIXME comments indicating known bugs
2. Check for failing tests
3. Look for recent git commits mentioning "fix" or "bug"
4. Search for try/catch blocks with console.error
```

**Research Execution:**
```bash
# Step 1
Grep: "TODO|FIXME|BUG"
Results: 3 TODOs, 1 FIXME in auth.ts:89

# Step 2
Glob: "**/*.test.ts"
Bash: npm test
Results: 2 tests failing in test_auth.test.ts

# Step 3
Bash: git log --grep="fix|bug" --oneline -10
Results: Recent commit "fix login redirect" 2 days ago

# Step 4
Grep: "console.error|console.warn"
Results: Error logged in auth.ts:145 "Invalid token"
```

**Research Findings:**
- FIXME in auth.ts:89: "FIXME: Token validation is broken"
- 2 failing tests related to token validation
- Recent fix attempt for login redirect
- Error logging at auth.ts:145 for invalid tokens

**Questions Asked:**
```json
{
  "questions": [
    {
      "question": "Which bug should be fixed?",
      "header": "Bug target",
      "multiSelect": false,
      "options": [
        {
          "label": "Token validation (auth.ts:89)",
          "description": "FIXME comment indicates broken token validation. 2 failing tests in test_auth.test.ts related to this. Likely high priority."
        },
        {
          "label": "Login redirect (recent commit)",
          "description": "Recent commit 2 days ago attempted to fix login redirect. May have residual issues."
        },
        {
          "label": "Invalid token logging (auth.ts:145)",
          "description": "Errors being logged for invalid tokens. May be symptom of validation bug or separate issue."
        }
      ]
    }
  ]
}
```

**User Answer:**
"Token validation (auth.ts:89)"

**Execution:**
Fix token validation in auth.ts:89, run tests to verify fix resolves the 2 failing tests.

---

### Example 2: Generic Refactoring Request

**Original Prompt:**
```
refactor the code to be better
```

**Evaluation:**
- Target: ❌ (what code?)
- Action: ❌ ("better" is subjective)
- Criteria: ❌ (what defines "better"?)
- Context: Check recent activity

**Context Check:**
User recently opened src/api/users.ts

**Research Plan:**
```
1. Read src/api/users.ts to understand current state
2. Search for code quality issues (long functions, duplication)
3. Check for established patterns in similar files
4. Research Node.js/TypeScript refactoring best practices
```

**Research Execution:**
```bash
# Step 1
Read: src/api/users.ts
Findings: 450 lines, single file with all user operations

# Step 2
Analysis of users.ts:
- getUserById: 45 lines
- createUser: 78 lines
- updateUser: 89 lines
- deleteUser: 34 lines
- validateUser: 56 lines
All in one file, mixed concerns

# Step 3
Glob: "src/api/*.ts"
Read: src/api/products.ts
Finding: Products API uses service layer pattern (ProductService class)

# Step 4
WebSearch: "Node.js API refactoring patterns"
Finding: Service layer pattern, repository pattern common
```

**Research Findings:**
- users.ts is 450 lines, all logic in one file
- Other APIs (products) use service layer separation
- Industry pattern: Controller → Service → Repository
- Current code mixes validation, business logic, data access

**Questions Asked:**
```json
{
  "questions": [
    {
      "question": "What aspect of the code should be improved?",
      "header": "Improvement",
      "multiSelect": false,
      "options": [
        {
          "label": "Extract service layer",
          "description": "Create UserService class for business logic, matching ProductService pattern already used in products.ts. Separates concerns and improves testability."
        },
        {
          "label": "Split into multiple files",
          "description": "Break 450-line file into smaller modules (validation.ts, service.ts, controller.ts). Easier to navigate and maintain."
        },
        {
          "label": "Reduce function complexity",
          "description": "Refactor long functions (updateUser at 89 lines, createUser at 78 lines) into smaller, focused functions. Improves readability."
        }
      ]
    },
    {
      "question": "Should this follow the existing ProductService pattern?",
      "header": "Pattern",
      "multiSelect": false,
      "options": [
        {
          "label": "Yes, match ProductService",
          "description": "Maintain consistency with existing codebase. Same architecture makes it easier for team to navigate."
        },
        {
          "label": "No, use different approach",
          "description": "Opportunity to establish new pattern if ProductService approach has issues."
        }
      ]
    }
  ]
}
```

**User Answers:**
1. "Extract service layer"
2. "Yes, match ProductService"

**Execution:**
Extract UserService class following ProductService pattern, move business logic from users.ts to service/UserService.ts, keep controller thin.

---

### Example 3: Ambiguous Feature Request

**Original Prompt:**
```
add authentication
```

**Evaluation:**
- Target: ~ (app-wide feature)
- Action: ✅ (add authentication)
- Criteria: ❌ (what type? what approach?)
- Context: Check project state

**Research Plan:**
```
1. Check if any auth exists currently
2. Review package.json for auth libraries
3. Explore project architecture
4. Research authentication best practices for stack
5. Check for any auth requirements in docs
```

**Research Execution:**
```bash
# Step 1
Grep: "auth|login|session|jwt"
Results: No existing auth code

# Step 2
Read: package.json
Findings: Express 4.18.2, no auth libraries installed

# Step 3
Task/Explore: Map application architecture
Results: Express REST API, MongoDB database, microservices planned

# Step 4
WebSearch: "Express authentication best practices 2024"
WebSearch: "JWT vs session authentication microservices"
Findings: JWT recommended for microservices, session for monoliths

# Step 5
Read: README.md, docs/requirements.md
Findings: "Must support mobile app" mentioned
```

**Research Findings:**
- No existing authentication
- Express.js backend with REST API
- MongoDB database available
- Microservices architecture planned
- Must support mobile app (stateless preferred)
- JWT is industry standard for this stack

**Questions Asked:**
```json
{
  "questions": [
    {
      "question": "Which authentication method should be implemented?",
      "header": "Auth method",
      "multiSelect": false,
      "options": [
        {
          "label": "JWT with refresh tokens",
          "description": "Stateless authentication. Access token (short-lived) + refresh token (long-lived). Best for microservices and mobile apps. Industry standard for this use case."
        },
        {
          "label": "Session-based with MongoDB",
          "description": "Server-side sessions stored in MongoDB (connect-mongo). Simpler to implement, easier to invalidate. Works but less ideal for mobile/microservices."
        },
        {
          "label": "OAuth 2.0 integration",
          "description": "Delegate to third-party providers (Google, GitHub). Good user experience, but requires provider setup and internet connectivity."
        }
      ]
    },
    {
      "question": "Where should JWT tokens be stored on the client?",
      "header": "Token store",
      "multiSelect": false,
      "options": [
        {
          "label": "HttpOnly cookies",
          "description": "Server sets cookie with HttpOnly flag. Protected from XSS attacks. Requires CSRF protection. Best for web apps."
        },
        {
          "label": "Authorization header",
          "description": "Client stores in memory, sends via Bearer token. Required for mobile apps. Client handles storage and sending."
        },
        {
          "label": "Both (web and mobile)",
          "description": "Support cookies for web, Authorization header for mobile. Maximum flexibility but adds complexity."
        }
      ]
    },
    {
      "question": "What should be included in the authentication scope?",
      "header": "Scope",
      "multiSelect": true,
      "options": [
        {
          "label": "Login/register endpoints",
          "description": "POST /auth/register and POST /auth/login. Basic authentication flow."
        },
        {
          "label": "Password reset flow",
          "description": "Forgot password email workflow. Important for production but adds complexity."
        },
        {
          "label": "Role-based access control",
          "description": "User roles (admin, user, guest) with permission checking. Essential for most apps."
        },
        {
          "label": "Email verification",
          "description": "Verify email on registration. Prevents fake accounts but requires email service."
        }
      ]
    }
  ]
}
```

**User Answers:**
1. "JWT with refresh tokens"
2. "Both (web and mobile)"
3. ["Login/register endpoints", "Role-based access control"]

**Execution:**
Implement JWT authentication with refresh tokens, support both HttpOnly cookies (web) and Authorization header (mobile), create login/register endpoints with role-based access control.

---

## Clear Prompts (Proceed Immediately)

### Example 4: Specific File and Action

**Original Prompt:**
```
Refactor the getUserById function in src/api/users.ts to use async/await instead of promise chains
```

**Evaluation:**
- Target: ✅ (getUserById in src/api/users.ts)
- Action: ✅ (refactor to async/await)
- Criteria: ✅ (no promise chains, use async/await)
- Context: Not needed

**Decision:** PROCEED IMMEDIATELY (no research or questions)

**Execution:**
```javascript
// Before
function getUserById(id) {
  return db.users.findOne({id})
    .then(user => {
      if (!user) throw new Error('User not found');
      return user;
    })
    .then(user => validateUser(user))
    .then(validatedUser => formatResponse(validatedUser))
    .catch(error => handleError(error));
}

// After
async function getUserById(id) {
  try {
    const user = await db.users.findOne({id});
    if (!user) throw new Error('User not found');
    const validatedUser = await validateUser(user);
    return formatResponse(validatedUser);
  } catch (error) {
    return handleError(error);
  }
}
```

---

### Example 5: Specific Bug with Context

**Original Prompt:**
```
Fix the TypeError at line 145 in src/auth/login.ts where user.profile.name is undefined
```

**Evaluation:**
- Target: ✅ (login.ts:145)
- Action: ✅ (fix TypeError for user.profile.name)
- Criteria: ✅ (no TypeError, safe access)
- Context: Error description provided

**Decision:** PROCEED IMMEDIATELY

**Execution:**
```typescript
// Before (line 145)
const displayName = user.profile.name;

// After (line 145)
const displayName = user?.profile?.name ?? 'Anonymous';
```

---

### Example 6: Clear Feature with Details

**Original Prompt:**
```
Add input validation to the registration form using Joi schema. Validate:
- Email (required, valid format)
- Password (required, min 8 characters, must include number and special char)
- Username (required, 3-20 characters, alphanumeric only)
```

**Evaluation:**
- Target: ✅ (registration form)
- Action: ✅ (add Joi validation)
- Criteria: ✅ (specific validation rules listed)
- Context: Joi specified, all requirements clear

**Decision:** PROCEED IMMEDIATELY

**Execution:**
```javascript
const Joi = require('joi');

const registrationSchema = Joi.object({
  email: Joi.string()
    .email()
    .required()
    .messages({
      'string.email': 'Email must be valid',
      'any.required': 'Email is required'
    }),

  password: Joi.string()
    .min(8)
    .pattern(/^(?=.*[0-9])(?=.*[!@#$%^&*])/)
    .required()
    .messages({
      'string.min': 'Password must be at least 8 characters',
      'string.pattern.base': 'Password must include number and special character',
      'any.required': 'Password is required'
    }),

  username: Joi.string()
    .alphanum()
    .min(3)
    .max(20)
    .required()
    .messages({
      'string.alphanum': 'Username must be alphanumeric',
      'string.min': 'Username must be at least 3 characters',
      'string.max': 'Username must not exceed 20 characters',
      'any.required': 'Username is required'
    })
});
```

---

## Bypass Prompts (Pass Through)

### Example 7: Asterisk Bypass

**Original Prompt:**
```
* just add a quick comment explaining this function
```

**Detection:**
Bypass prefix `*` detected

**Action:**
Strip `*`, pass through as: "just add a quick comment explaining this function"

**Execution:**
Add comment without any evaluation or questions.

---

### Example 8: Slash Command

**Original Prompt:**
```
/commit
```

**Detection:**
Slash command format detected

**Action:**
Pass through to slash command system unchanged

**Execution:**
Slash command system handles the request.

---

### Example 9: Hash Prefix (Memory)

**Original Prompt:**
```
# remember to use TypeScript strict mode for all new files
```

**Detection:**
Hash prefix `#` detected (memorize/note feature)

**Action:**
Pass through to memory system unchanged

**Execution:**
Memory system stores the note.

---

## Context-Dependent Prompts

### Example 10: File Viewing Context Makes Clear

**Context:**
```
[System: User opened src/components/LoginForm.tsx]
```

**Prompt:**
```
refactor this to use hooks
```

**Evaluation:**
- Target: ✅ (LoginForm.tsx from file view context)
- Action: ✅ (refactor to hooks)
- Criteria: ✅ (convert class component to hooks)
- Context: ✅ (file viewing provides target)

**Decision:** PROCEED IMMEDIATELY

**Execution:**
Refactor LoginForm.tsx from class component to functional component with hooks.

---

### Example 11: Recent Error Provides Context

**Previous Message:**
```
Error: ECONNREFUSED: Connection refused at 127.0.0.1:5432
  at TCPConnectWrap.afterConnect [as oncomplete] (net.js:1148:16)
```

**Current Prompt:**
```
fix this connection error
```

**Evaluation:**
- Target: ✅ (database connection from error)
- Action: ✅ (fix connection refused)
- Criteria: ✅ (successful connection to localhost:5432)
- Context: ✅ (error message provides all details)

**Decision:** PROCEED IMMEDIATELY

**Research (quick check):**
- Port 5432 is PostgreSQL standard port
- ECONNREFUSED means service not running or wrong config

**Execution:**
Check if PostgreSQL is running, verify connection config, start service if needed.

---

### Example 12: Ongoing Discussion Provides Context

**Message History:**
```
User: "Should I use Prisma or TypeORM for the database?"
Assistant: "Prisma has better TypeScript support and migration tooling..."
User: "ok let's go with Prisma"
```

**Current Prompt:**
```
set it up
```

**Evaluation:**
- Target: ~ (Prisma setup)
- Action: ✅ (set up Prisma)
- Criteria: ~ (working Prisma configuration)
- Context: ✅ (decision made in conversation)

**Decision:** PROCEED (context makes this clear)

**Execution:**
Install Prisma, initialize, configure database connection, create initial schema.

---

## Complex Multi-Question Scenarios

### Example 13: Major Feature with Multiple Unknowns

**Original Prompt:**
```
implement caching
```

**Evaluation:**
- Target: ❌ (cache what?)
- Action: ❌ (how to cache?)
- Criteria: ❌ (what performance target?)
- Context: Check project

**Research Plan:**
```
1. Explore current performance bottlenecks
2. Check for existing caching
3. Review caching libraries available
4. Research caching strategies for this stack
5. Identify cache candidates in codebase
```

**Research Findings:**
- No current caching
- Slow endpoints: /api/products (500ms avg), /api/users (200ms avg)
- Redis installed but not configured
- Product catalog rarely changes (good cache candidate)
- User data changes frequently (poor cache candidate)

**Questions Asked:**
```json
{
  "questions": [
    {
      "question": "What should be cached?",
      "header": "Cache target",
      "multiSelect": true,
      "options": [
        {
          "label": "Product catalog (/api/products)",
          "description": "Currently 500ms response time. Products change infrequently (good cache candidate). High traffic endpoint."
        },
        {
          "label": "User profiles (/api/users/:id)",
          "description": "Currently 200ms response time. Profile data changes occasionally. Moderate traffic."
        },
        {
          "label": "Database queries",
          "description": "Cache at ORM level for all database queries. Broadest impact but requires careful invalidation."
        }
      ]
    },
    {
      "question": "Which caching strategy should be used?",
      "header": "Strategy",
      "multiSelect": false,
      "options": [
        {
          "label": "Redis with TTL",
          "description": "External cache with time-to-live expiration. Redis already installed. Best for distributed systems. Standard approach."
        },
        {
          "label": "In-memory with node-cache",
          "description": "Simple in-process caching. Fast but not shared across instances. Good for single-server deployments."
        },
        {
          "label": "Redis with cache invalidation",
          "description": "Active invalidation on data changes. Most complex but most accurate. Requires event hooks on updates."
        }
      ]
    },
    {
      "question": "What should the cache TTL (time-to-live) be?",
      "header": "TTL",
      "multiSelect": false,
      "options": [
        {
          "label": "5 minutes",
          "description": "Aggressive caching. Data can be stale up to 5 minutes. Best for very static data."
        },
        {
          "label": "1 minute",
          "description": "Balanced approach. Reduces load while keeping data relatively fresh. Good default."
        },
        {
          "label": "30 seconds",
          "description": "Conservative caching. Minimal staleness but less performance benefit. Use for semi-dynamic data."
        }
      ]
    }
  ]
}
```

**User Answers:**
1. ["Product catalog (/api/products)", "User profiles (/api/users/:id)"]
2. "Redis with TTL"
3. "1 minute"

**Execution:**
Implement Redis caching for product catalog and user profiles with 1-minute TTL, configure Redis connection, add cache middleware to those endpoints.

---

## Summary: Decision Patterns

### Proceed Immediately If:
- Specific file and function mentioned with clear action
- Error message provides full context
- File viewing context clarifies ambiguous "this"
- Recent conversation establishes clear decisions
- All 4 evaluation criteria pass

### Research and Ask If:
- Generic action verbs ("fix", "improve", "refactor") without target
- No file or component mentioned
- Multiple valid approaches
- Architectural decisions needed
- Configuration choices required

### Pass Through If:
- Bypass prefix detected (`*`, `/`, `#`)
- User explicitly opted out of evaluation

These examples demonstrate the spectrum from clear to vague and show how research findings directly inform specific, actionable questions.
