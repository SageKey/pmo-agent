# sync-jira

Pull the latest % Complete and Health status from Jira and update the local SQLite database.

## Steps

1. Check that `JIRA_API_TOKEN` is set in the environment or `.env` file. If missing, tell the user:
   > Set `JIRA_API_TOKEN` in your `.env` file before running a Jira sync.
   Then stop.

2. Run the sync in dry-run mode first so the user can preview changes:
   ```bash
   python jira_sync.py --dry-run
   ```

3. Show the user a summary of what would change (projects updated, fields changed).

4. Ask the user if they want to apply the changes.

5. On confirmation, run the live sync:
   ```bash
   python jira_sync.py
   ```

6. Report how many projects were updated and flag any errors encountered during sync.
