Review the specified file or module for Clean Code and Clean Architecture violations,
following the principles defined in CLAUDE.md.

## Instructions

1. Read the target file(s) thoroughly before commenting.
2. Identify the file's role in the architecture (entity, use case, adapter, or driver).
   If you can't tell, flag that as issue #1.
3. Check dependencies: what does this file import? Do those imports respect the dependency
   rule for its architectural layer?
4. Walk through each function and class applying Clean Code principles.
5. For each issue found:
   - State the specific principle violated
   - Explain WHY it matters in this context (not just the rule)
   - Suggest a concrete fix with code when helpful
   - Assign severity: CRITICAL / MAJOR / MINOR
6. Group findings by severity, criticals first.
7. End with a brief summary: what's the single most impactful refactoring this file needs?

If the file is clean, say so — don't invent issues.

Target: $ARGUMENTS
