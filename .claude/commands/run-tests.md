# run-tests

Run the full test suite for PMO Planner and report results.

## Steps

1. Run the foundation tests (unit-level validation of connector and capacity engine):
   ```bash
   python test_foundation.py
   ```

2. Run the end-to-end tests:
   ```bash
   python test_e2e.py
   ```

3. Report a summary: total PASS / FAIL counts for each suite, and list any failures with their labels so the user knows exactly what broke.

If the database file `pmo_data.db` doesn't exist, warn the user that the DB must be seeded first (`/seed-db`) before tests can run.
