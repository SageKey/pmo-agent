Scan the specified directory for the worst function-level Clean Code violations.

## Instructions

1. Search all Python files in the target directory (recursively).

2. Find and rank the top offenders for each category:
   - **Long functions:** Functions exceeding 20 lines (list the top 10 longest)
   - **Too many arguments:** Functions with 4+ parameters (exclude self/cls)
   - **Deep nesting:** Functions with 3+ levels of indentation
   - **Mixed abstraction:** Functions that mix high-level orchestration with low-level
     detail (e.g., a function that calls a service AND formats a string)
   - **Side effects:** Functions whose name implies one thing but that also do something
     else (e.g., `validate_x` that also saves, `get_x` that also modifies state)
   - **Flag arguments:** Boolean parameters that switch function behavior
   - **God functions:** Functions doing multiple unrelated things

3. For each finding, provide:
   - File path and function name
   - Line count / arg count / nesting depth as applicable
   - A one-line description of what's wrong
   - Suggested decomposition strategy

4. Produce a summary table:

   | Category          | Count | Worst Offender           |
   |-------------------|-------|--------------------------|
   | Long functions    |       |                          |
   | Too many args     |       |                          |
   | Deep nesting      |       |                          |
   | Mixed abstraction |       |                          |
   | Side effects      |       |                          |
   | Flag arguments    |       |                          |

5. End with: "If you could only refactor 3 functions in this codebase, refactor these..."
   and explain why.

Target directory: $ARGUMENTS
