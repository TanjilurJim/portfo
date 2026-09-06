# portfo
Portfolio Project With Flask
# Visit from this link: 
tanjilurjdot.pythonanywhere.com/

## Storage

Form submissions are stored in `portfolio.db`, a local SQLite database created automatically when `server.py` starts.

### PythonAnywhere notes

1. Upload the project files.
2. Make sure `Flask` is installed in your PythonAnywhere virtualenv.
3. Point your WSGI file at `server:app`.
4. Keep `portfolio.db` in the project folder so the app can write to it.

### Database migrations

After pulling code that contains database changes, activate the virtualenv and
run the schema migration command:

```bash
workon my-virtualenv
cd ~/portfo
python migrate_schema.py
```

The command uses the schema definitions in `server.py`, creates a timestamped
backup in `db_backups/`, and then creates missing tables and columns. It is safe
to run again when the schema is already current. Reload the web app from the
PythonAnywhere **Web** tab after the migration succeeds.

To migrate a database at a different path:

```bash
python migrate_schema.py --database /path/to/portfolio.db
```

### SQLite tables

- `contacts` stores contact form submissions plus read and delivery status.
- `transactions` stores income and expense entries for the private tracker.
- `smtp_settings` stores one active SMTP configuration row for the app.
- `users` stores login accounts for the private area.

### Login

- Login page: `/login`
- Private page after login: `/dashboard`
- Contact inbox: `/dashboard/contacts`
- Contact detail: `/dashboard/contacts/<id>`
- Expense tracker: `/dashboard/expenses`
- SMTP settings page: `/dashboard/smtp-settings`
- Starter accounts:
  - `` / `123456`
  - `` / `123456`

Replace those starter passwords after your first login.
