# anonymize

Anonymize a real PMO database and generate a new `seed_data.sql` demo file.

## Usage

Run this when you have a real `pmo_data.real.db` and want to regenerate the demo seed
with anonymized data (fictional names, jittered numbers, fake vendors).

## Steps

1. Check that `pmo_data.real.db` exists in the project root. If not, tell the user:
   > Copy your real database to `pmo_data.real.db` first.
   Then stop.

2. Run the anonymizer:
   ```bash
   python3 scripts/anonymize_data.py \
     --source pmo_data.real.db \
     --dest pmo_data.demo.db
   ```

3. Dump the anonymized DB to the seed file:
   ```bash
   sqlite3 pmo_data.demo.db .dump > seed_data.sql
   ```

4. Report the file size of `seed_data.sql` and a row count summary:
   ```bash
   sqlite3 pmo_data.demo.db "SELECT 'projects', COUNT(*) FROM projects UNION ALL SELECT 'team_members', COUNT(*) FROM team_members;"
   ```

5. Remind the user: **never commit `pmo_data.real.db`** — it is gitignored for a reason.
   Only `seed_data.sql` should be committed.
