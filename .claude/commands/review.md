# review

Perform a Clean Code & Clean Architecture review of a file or module in this codebase.

## Usage

```
/review <file_path>
```

Example: `/review capacity_engine.py`

## Steps

1. Read the target file specified by the user.

2. Apply the review framework defined in `CLAUDE.md`:
   - Check dependency rule violations first (architecture layer boundaries)
   - Then SRP violations
   - Then function-level issues (size, side effects, abstraction mixing)
   - Then error handling
   - Then naming and readability
   - Then minor style

3. For each issue found, report:
   - **File and line(s)**
   - **Principle** violated
   - **Severity**: CRITICAL / MAJOR / MINOR
   - **What's wrong** (specific, in context)
   - **Suggested fix** (show code when useful)

4. Stop reviewing at CRITICAL issues — don't nitpick naming on a file with broken architecture.

5. End with a prioritized list of the top 3 changes that would have the highest impact.

## Project context

Refer to the "Project-Specific Context" section in `CLAUDE.md` for known tech debt and
the intended layer boundaries before flagging violations.
