Audit naming quality across the specified directory following Clean Code naming principles.

## Instructions

1. Scan all Python files in the target directory recursively.

2. Check for these naming violations:

   **Misleading names:**
   - Variables named `list`, `dict`, `data`, `info`, `temp`, `tmp`, `val`, `result`
     without qualification
   - Names that lie: `account_list` that's actually a dict, `count` that's a boolean
   - Single-letter variables outside of comprehensions and trivial loops

   **Non-intention-revealing names:**
   - Abbreviations: `mgr`, `ctx`, `cfg`, `proc`, `stmt`, `txn` (flag these, suggest
     full words)
   - Numbered variables: `data1`, `data2`, `result2`
   - Generic names: `handle()`, `process()`, `do_thing()`, `run()` without context

   **Inconsistent vocabulary:**
   - Multiple verbs for the same concept across the codebase (e.g., `get_user`,
     `fetch_account`, `retrieve_order` all meaning "read from DB")
   - Inconsistent noun forms (e.g., `Order` vs `OrderData` vs `OrderInfo` vs `OrderDTO`
     when they mean the same thing)

   **Convention violations:**
   - Classes not named as nouns
   - Functions/methods not named as verbs (excluding properties and dunder methods)
   - Constants not in UPPER_SNAKE_CASE
   - Boolean variables/functions not using is_/has_/can_/should_ prefix

3. Produce a vocabulary map — what verbs/nouns are used for CRUD operations across the
   codebase? Highlight inconsistencies.

4. List the 10 worst-named identifiers and suggest better names.

5. End with a recommended naming convention cheat sheet specific to this project.

Target directory: $ARGUMENTS
