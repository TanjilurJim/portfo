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
  - `tanjilurrahman21@gmail.com` / `123456`
  - `nazianuzhat90@gmail.com` / `123456`

Replace those starter passwords after your first login.
