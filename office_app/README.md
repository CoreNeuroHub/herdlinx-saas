# Office Herd Management Application

A separate Flask application for office use that provides the same functionality as the main feedlot app, but uses SQLite instead of MongoDB and is accessible only to admin users.

## Features

- Same look and feel as the main HerdLinx SaaS application
- Admin-only access control
- SQLite database backend
- Complete pen, batch, and cattle management functionality
- Dashboard with statistics

## Setup

1. Install dependencies:
   ```bash
   cd office_app
   pip install -r requirements.txt
   ```

2. Run the application:
   
   From the project root directory:
   ```bash
   python -m office_app.run
   ```
   
   Or run directly (from project root):
   ```bash
   python office_app/run.py
   ```
   
   The application will start on port 5001.

3. Access the application:
   - URL: http://localhost:5001
   - Default admin credentials:
     - Username: `admin`
     - Password: `admin`
     - **Change this password in production!**

## Database

The application uses SQLite and will automatically create the database file `office_app.db` in the `office_app` directory when first run.

## Project Structure

```
office_app/
├── __init__.py          # Flask app factory
├── config.py            # Configuration
├── run.py               # Entry point
├── models/              # SQLAlchemy models
│   ├── user.py
│   ├── pen.py
│   ├── batch.py
│   └── cattle.py
├── routes/              # Route handlers
│   ├── auth_routes.py
│   └── office_routes.py
├── templates/           # Jinja2 templates
│   ├── base.html
│   ├── auth/
│   └── office/
└── static/              # Static files
    └── img/
```

## Note

This is a completely separate application from the main HerdLinx SaaS app. It has its own database, authentication, and runs on a different port (5001).

