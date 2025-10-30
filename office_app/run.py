"""
Run the Office Herd Management application.

Run this from the project root directory:
    python -m office_app.run

Or set PYTHONPATH and run directly:
    cd ..
    python office_app/run.py
"""
import sys
import os

# Get the project root (parent of office_app directory)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
office_app_dir = os.path.dirname(os.path.abspath(__file__))

# Add project root to Python path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Change to office_app directory for relative paths in templates/static
os.chdir(office_app_dir)

from office_app import create_app

app = create_app()

if __name__ == '__main__':
    print(f"Starting Office Herd Management on http://0.0.0.0:5001")
    print(f"Default admin: username=admin, password=admin")
    app.run(debug=True, host='0.0.0.0', port=5001)
