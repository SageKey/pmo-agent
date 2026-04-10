# seed-db

Reset the SQLite database and reseed it from `seed_data.sql`.

## Steps

1. Warn the user: this will **wipe all data** in `pmo_data.db` and replace it with the demo seed. Ask for confirmation before proceeding.

2. On confirmation, run:
   ```bash
   sqlite3 pmo_data.db < seed_data.sql
   ```

3. Verify the seed worked by running a quick row count:
   ```bash
   sqlite3 pmo_data.db "SELECT 'projects', COUNT(*) FROM projects UNION ALL SELECT 'team_members', COUNT(*) FROM team_members;"
   ```

4. Report the row counts to confirm the seed completed successfully.

If `seed_data.sql` is not found in the project root, tell the user and stop.
