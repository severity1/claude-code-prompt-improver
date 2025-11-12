# Research Strategies for Context Gathering

This reference provides systematic approaches for researching codebase context, best practices, and patterns before formulating clarifying questions.

## Table of Contents

- [Research Planning Framework](#research-planning-framework)
- [Codebase Exploration Strategies](#codebase-exploration-strategies)
- [Documentation Research](#documentation-research)
- [Web Research for Best Practices](#web-research-for-best-practices)
- [Conversation History Mining](#conversation-history-mining)
- [Tool Selection Guide](#tool-selection-guide)
- [Research Execution Patterns](#research-execution-patterns)

## Research Planning Framework

### Phase 1: Identify What's Unclear

Before researching, explicitly identify gaps:

**Target Gap:**
- "Which file/function needs modification?"
- "What component is involved?"

**Approach Gap:**
- "How should this be implemented?"
- "What pattern should be used?"

**Scope Gap:**
- "How much should be changed?"
- "What's included in this request?"

**Context Gap:**
- "What's the current state?"
- "What patterns exist already?"

### Phase 2: Create Research Plan with TodoWrite

Use TodoWrite to create a research plan before executing. This ensures systematic investigation.

**Template:**
```
Research Plan for [Prompt Type]:
1. [What to research] - [Tool/approach]
2. [What to research] - [Tool/approach]
3. [What to research] - [Tool/approach]
```

**Example:**
```
Research Plan for "fix the bug":
1. Check conversation history for error messages - Review recent messages
2. Search for failing tests - Grep for "failing", "error", "TODO"
3. Explore recent commits - Git log for problem areas
4. Identify patterns in similar code - Read related files
```

### Phase 3: Execute Research

Systematically execute each research step, documenting findings.

### Phase 4: Document Findings

Summarize what you learned:
- Key files involved
- Existing patterns found
- Common approaches in the codebase
- Relevant best practices
- Constraints or requirements discovered

## Codebase Exploration Strategies

### Strategy 1: Pattern Discovery (Task/Explore Agent)

**When to use:** Need to understand architecture, find similar implementations, or explore unknown territory

**Approach:**
```
Use Task tool with subagent_type=Explore to:
- Map codebase structure
- Find similar implementations
- Understand architectural patterns
- Identify relevant components
```

**Example:**
```
Prompt: "find the bug"

Research:
1. Launch Explore agent: "Find error handling patterns in authentication code"
2. Results: Discover auth.ts, middleware.ts, session.ts with different error patterns
3. Finding: Inconsistent error handling across auth files
```

### Strategy 2: Targeted File Search (Glob)

**When to use:** Know what you're looking for (file type, name pattern)

**Common patterns:**
```bash
# Find all authentication-related files
**/*auth*.ts

# Find test files
**/*.test.ts
**/*.spec.ts

# Find configuration files
**/*config*.{json,yaml,yml}
**/.*rc

# Find documentation
**/*.md
**/README*
```

**Example:**
```
Prompt: "add tests"

Research:
1. Glob: "**/*.test.ts" → Find existing test files
2. Identify pattern: Tests colocated with source files
3. Finding: Use Jest, tests in __tests__/ directories
```

### Strategy 3: Content Search (Grep)

**When to use:** Looking for specific code patterns, function calls, or keywords

**Effective searches:**
```bash
# Find authentication implementations
pattern: "authenticate|login|auth"

# Find TODOs and FIXMEs
pattern: "TODO|FIXME|XXX|HACK"

# Find error handling
pattern: "try.*catch|throw new|Error\\("

# Find specific function calls
pattern: "validateUser\\(|checkAuth\\("

# Find configuration usage
pattern: "process\.env|config\.|getConfig"
```

**Example:**
```
Prompt: "improve error handling"

Research:
1. Grep: "try.*catch" with multiline mode
2. Grep: "throw new Error"
3. Finding: 15 try/catch blocks, 8 throw different error types
4. Pattern: Some use custom errors (AuthError, ValidationError), some use generic Error
```

### Strategy 4: Architecture Understanding (Read + Explore)

**When to use:** Need to understand how systems connect

**Approach:**
1. Start with entry points (index.ts, main.ts, app.ts)
2. Read key configuration files (package.json, tsconfig.json)
3. Explore directory structure
4. Read README.md and architecture docs

**Example:**
```
Prompt: "refactor the API"

Research:
1. Read: package.json → Express.js backend
2. Read: src/index.ts → Entry point, middleware setup
3. Explore: src/routes/ → Route organization pattern
4. Finding: RESTful API with route/controller/service layers
```

### Strategy 5: Historical Context (Git Commands)

**When to use:** Understanding evolution, finding related changes

**Useful git commands via Bash:**
```bash
# Recent commits
git log --oneline -20

# Commits affecting specific file
git log --oneline path/to/file

# Search commit messages
git log --grep="authentication" --oneline

# Find when function was added
git log -S "functionName" --oneline

# See recent changes
git diff HEAD~5..HEAD --stat
```

**Example:**
```
Prompt: "fix the recent regression"

Research:
1. Git log: Last 10 commits
2. Git log --grep="fix|bug": Recent bug fixes
3. Finding: Commit 3 days ago changed auth flow
4. Pattern: Regression likely in authentication changes
```

## Documentation Research

### Strategy 1: Local Documentation (Read)

**Priority order:**
1. README.md at project root
2. docs/ directory
3. Package-specific READMEs (packages/*/README.md)
4. CONTRIBUTING.md
5. Architecture docs (.architecture/, docs/architecture/)
6. API documentation (docs/api/)

**Example:**
```
Prompt: "implement caching"

Research:
1. Read: README.md → Check if caching mentioned
2. Read: docs/architecture.md → Current caching strategy?
3. Finding: Redis already used for session caching
4. Pattern: Use Redis for new caching needs (consistency)
```

### Strategy 2: Package Documentation (Read + WebFetch)

**When to use:** Understanding third-party library usage

**Approach:**
1. Read package.json for library versions
2. Check local docs or examples
3. WebFetch official documentation if needed

**Example:**
```
Prompt: "update the validation"

Research:
1. Read: package.json → Using Joi@17.6.0
2. Grep: "Joi\." → Find current usage patterns
3. WebFetch: "https://joi.dev/api/" → Current best practices
4. Finding: Using outdated Joi patterns, v17 has simpler syntax
```

### Strategy 3: Code Comments (Grep)

**When to use:** Finding design decisions, warnings, constraints

**Patterns:**
```bash
# Find important comments
pattern: "NOTE:|WARNING:|IMPORTANT:|FIXME:"

# Find documentation comments
pattern: "/\\*\\*|@param|@returns"

# Find constraint notes
pattern: "must|require|cannot|constraint"
```

**Example:**
```
Prompt: "modify the database schema"

Research:
1. Grep: "NOTE:|WARNING:" in migrations/
2. Finding: "NOTE: Cannot modify user_id - foreign keys depend on it"
3. Constraint: Must preserve user_id column
```

## Web Research for Best Practices

### Strategy 1: Current Best Practices (WebSearch)

**When to use:** Need current approaches, recent changes, industry standards

**Effective queries:**
```
# Framework-specific patterns
"React authentication best practices 2024"
"Express.js error handling patterns 2024"

# Library comparisons
"JWT vs session authentication comparison"
"Joi vs Zod validation library comparison"

# Implementation approaches
"implement rate limiting Node.js"
"database transaction patterns TypeScript"

# Common problems
"fix N+1 query problem TypeScript"
"prevent SQL injection Node.js"
```

**Example:**
```
Prompt: "add authentication"

Research:
1. WebSearch: "Node.js authentication best practices 2024"
2. Finding: Passport.js is mature, NextAuth.js is newer, JWT is standard
3. WebSearch: "JWT vs session authentication comparison"
4. Finding: JWT for stateless, sessions for simplicity
5. Pattern: Choose based on project architecture (microservices → JWT)
```

### Strategy 2: Framework Documentation (WebFetch)

**When to use:** Need official guidance for frameworks in use

**Common documentation sites:**
```
# JavaScript/TypeScript
https://developer.mozilla.org/docs/
https://nodejs.org/docs/
https://www.typescriptlang.org/docs/

# Frameworks
https://reactjs.org/docs/
https://expressjs.com/
https://nextjs.org/docs/

# Tools
https://jestjs.io/docs/
https://prettier.io/docs/
```

**Example:**
```
Prompt: "update the middleware"

Research:
1. Read: package.json → Express.js 4.18.2
2. WebFetch: "https://expressjs.com/en/guide/using-middleware.html"
3. Finding: Express 4.x supports async middleware
4. Pattern: Can use async/await instead of callbacks
```

### Strategy 3: Common Architectures (WebSearch + WebFetch)

**When to use:** Implementing well-known patterns

**Queries:**
```
"repository pattern TypeScript example"
"MVC architecture Node.js best practices"
"clean architecture Node.js implementation"
"microservices patterns"
```

**Example:**
```
Prompt: "refactor data access"

Research:
1. WebSearch: "repository pattern TypeScript"
2. Finding: Separate data access from business logic
3. WebSearch: "repository pattern with dependency injection"
4. Finding: Use interfaces for testability
5. Pattern: UserRepository interface + implementation
```

## Conversation History Mining

### Strategy 1: Recent Context Review

**When to use:** Always (first step in research)

**Check for:**
- Error messages in recent messages
- File names mentioned
- Features discussed
- Decisions made
- Code shown or referenced

**Example:**
```
Recent messages:
User: "I'm getting TypeError: Cannot read property 'id' of undefined"
User: "It happens when I click the login button"
User: "fix it"

Research:
1. Error from history: undefined property access
2. Context: Login button click event
3. Implied target: Login button handler
4. Decision: Clear from context, no additional research needed
```

### Strategy 2: Topic Tracking

**When to use:** Understanding what user is working on

**Pattern:**
- Last 5-10 messages establish working context
- File views indicate focus area
- Previous questions show user intent

**Example:**
```
Message history:
5 messages ago: "How do I implement caching in Express?"
3 messages ago: "Should I use Redis or in-memory cache?"
1 message ago: "ok let's use Redis"
Current: "implement it"

Research:
1. Topic: Caching implementation with Redis
2. Decision made: Use Redis (not in-memory)
3. Context: Express.js project
4. Clear: Implement Redis caching in Express
```

### Strategy 3: File View Context

**When to use:** User viewing specific file

**System messages indicate:**
```
[System: User opened src/api/auth.ts]
```

**Example:**
```
[System: User opened src/components/LoginForm.tsx]
User: "refactor this to use hooks"

Research:
1. File context: LoginForm.tsx (React component)
2. User viewing: Specific component
3. Request: Convert to hooks
4. Clear: Refactor LoginForm.tsx from class to hooks
```

## Tool Selection Guide

### Choosing the Right Tool

**Task/Explore Agent:**
- Broad exploration needed
- Understanding architecture
- Finding similar patterns
- Complex multi-step research

**Glob:**
- Finding files by name pattern
- Known file types
- Specific naming conventions

**Grep:**
- Searching code content
- Finding function calls
- Pattern matching
- TODO/FIXME discovery

**Read:**
- Reading specific files
- Documentation review
- Configuration inspection
- Package.json analysis

**Bash (git commands):**
- Historical context
- Recent changes
- Commit messages
- File history

**WebSearch:**
- Current best practices
- Industry standards
- Library comparisons
- Common solutions

**WebFetch:**
- Official documentation
- Specific documentation pages
- API references
- Tutorial content

### Multi-Tool Research Patterns

**Pattern 1: Architecture Discovery**
```
1. Read: package.json (understand stack)
2. Read: README.md (understand project)
3. Task/Explore: Map architecture
4. Glob: Find similar files
5. Read: Representative files
```

**Pattern 2: Implementation Approach**
```
1. Grep: Search for existing pattern
2. Read: Example implementation
3. WebSearch: Best practices
4. WebFetch: Official docs
5. Synthesize: Combine findings
```

**Pattern 3: Bug Investigation**
```
1. Review: Conversation history for errors
2. Grep: Search for error patterns
3. Bash: Git log for recent changes
4. Read: Affected files
5. Task/Explore: Find related code
```

## Research Execution Patterns

### Pattern 1: Quick Research (1-2 tools)

**When:** Simple ambiguity, limited scope

**Example:**
```
Prompt: "add tests"

Research:
1. Glob: "**/*.test.ts" → Find test pattern
2. Read: "src/__tests__/example.test.ts" → See structure

Findings:
- Jest framework
- Tests in __tests__/ directories
- Pattern established
```

### Pattern 2: Moderate Research (3-4 tools)

**When:** Multiple unknowns, need pattern understanding

**Example:**
```
Prompt: "improve error handling"

Research:
1. Grep: "try.*catch|throw new Error" → Find current patterns
2. Read: Key files with error handling
3. WebSearch: "Node.js error handling best practices 2024"
4. Task/Explore: Map error flow through app

Findings:
- Inconsistent error types
- Some use custom errors, some generic
- Best practice: Centralized error handler
- Pattern: Implement custom error classes
```

### Pattern 3: Comprehensive Research (5+ tools)

**When:** Major feature, architectural decision, complex implementation

**Example:**
```
Prompt: "add authentication"

Research:
1. Read: package.json → Current dependencies
2. Task/Explore: Map current auth (if any)
3. Grep: "auth|login|session" → Find existing code
4. WebSearch: "Node.js authentication best practices 2024"
5. WebSearch: "JWT vs session comparison"
6. WebFetch: "https://expressjs.com/en/advanced/best-practice-security.html"
7. Bash: git log --grep="auth" → Historical attempts

Findings:
- No existing auth system
- Express.js backend with REST API
- Microservices architecture (suggests JWT)
- Security requirements in docs
- Industry standard: JWT with refresh tokens
```

### Research Documentation Template

After research, document findings:

```
## Research Findings for "[Prompt]"

**What was unclear:**
- [List ambiguities]

**Research executed:**
1. [Tool] - [What searched] - [Key finding]
2. [Tool] - [What searched] - [Key finding]

**Key discoveries:**
- [Important finding 1]
- [Important finding 2]
- [Pattern identified]
- [Constraint discovered]

**Options identified:**
1. [Option A] - [From research source]
2. [Option B] - [From research source]
3. [Option C] - [From research source]

**Questions to ask:**
- [Question 1 based on findings]
- [Question 2 based on findings]
```

## Summary Checklist

Before asking questions:

- [ ] Created research plan with TodoWrite
- [ ] Checked conversation history for context
- [ ] Explored codebase for existing patterns
- [ ] Searched for similar implementations
- [ ] Reviewed relevant documentation
- [ ] Researched best practices (if needed)
- [ ] Documented findings
- [ ] Generated specific options from research
- [ ] Verified each option is grounded in findings
- [ ] Marked research phase complete in todo list

**Critical Rules:**
1. NEVER skip research phase
2. ALWAYS ground questions in findings
3. NEVER assume based on general knowledge
4. ALWAYS use conversation history first
5. DOCUMENT research findings before asking

Research is the foundation of effective clarification. The quality of your questions depends entirely on the thoroughness of your research.
