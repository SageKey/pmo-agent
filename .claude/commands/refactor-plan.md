Analyze the specified file or module and produce a prioritized refactoring plan following
Clean Code and Clean Architecture principles.

## Instructions

1. Read and understand what the code does before suggesting changes. Don't refactor what
   you don't understand.

2. Identify the current state:
   - What architectural layer does this code belong to?
   - What are its responsibilities? (List them — if more than 2-3, that's a finding)
   - What are its dependencies? (Imports, globals, side effects)
   - What's the current test coverage situation? (Check for corresponding test files)

3. Propose refactorings in this priority order:
   a. **Extract class/module** — if SRP is violated, show how to split
   b. **Introduce abstraction boundary** — if the dependency rule is violated, show
      where to add a Protocol and what moves where
   c. **Extract function** — for long or multi-responsibility functions, show the
      decomposition
   d. **Rename** — for unclear names, suggest better ones
   e. **Simplify** — remove dead code, flatten nesting, replace cleverness with clarity

4. For each refactoring, provide:
   - What to do (specific, actionable)
   - Why it matters (the cost of NOT doing it)
   - Risk level: LOW (rename, extract small function), MEDIUM (extract class, add
     abstraction), HIGH (restructure module boundaries)

5. Show a before/after sketch for the highest-impact refactoring. Not full code — just
   enough to show the structural change (class signatures, function signatures, import
   changes).

6. End with a suggested order of operations: what to refactor first so that subsequent
   refactorings are easier.

Target: $ARGUMENTS
