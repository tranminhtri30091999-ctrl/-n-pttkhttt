# AGENTS.md

- Project root is this directory (git repo).
- The parent `milktea/` folder is just a container; the leading `-` in this directory name requires quoting or a `./` prefix in shell commands.
- Implemented auth: Flask sessions, SQLite users, role-based route protection.
- App entrypoint: `app.py`; templates served by Flask routes under `/client`, `/admin`, `/staff`.
- Module ownership (from README):
  - `modules/admin` — TV1
  - `modules/products` — TV2
  - `modules/client` — TV3
  - `modules/order` — TV4
  - `modules/report` — TV5
- Keep template/static filenames aligned with the README structure.
- Database: `database/` contains `schema.sql`, `seed_data.sql`, `db_helper.py`. `database.db` is generated and gitignored. Do not recreate a file named `database`.
- Run app: `python app.py` (http://127.0.0.1:5000). Auth endpoints under `/admin`.
- Dev logins: admin/admin123, staff/staff123, customer/customer123.
- Backend role checks protect `/admin/users.html` and `/staff/*.html`; frontend redirect is not the security boundary.
- Git note: replacing the tracked `database` file with a directory appears as a deletion; stage changes with `git add -A`.
