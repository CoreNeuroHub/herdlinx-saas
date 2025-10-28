ven # HerdLinx SaaS - Cattle Tracking Application

A multi-tenant SaaS application for tracking cattle in feedlots, built with Flask, MongoDB, and Tailwind CSS.

## Features

- **Multi-tenant Architecture**: Separate top-level management with individual feedlot instances
- **Multi-level Authentication**: Separate user management for top-level and feedlot users
- **Feedlot Management**: Create and manage multiple feedlot instances
- **Pen Management**: Track pens with capacity monitoring
- **Batch Tracking**: Record cattle induction by batches
- **Individual Cattle Details**: Detailed tracking of each cattle's information
- **Responsive Design**: Mobile-first UI using Tailwind CSS
- **Security**: Password encryption, session management, and role-based access control

## Tech Stack

- **Backend**: Python 3.8+ with Flask
- **Frontend**: HTML5 with Tailwind CSS
- **Database**: MongoDB
- **Authentication**: bcrypt for password hashing

## Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB (local or cloud instance)
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd herdlinx-saas
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB=herdlinx_saas
   ```

5. **Start MongoDB**
   Make sure MongoDB is running on your system or update the `MONGODB_URI` in `.env` to point to your MongoDB instance.

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## First Time Setup

### Default Admin Account

The application comes with a pre-configured admin user that is automatically created on first startup:

- **Username**: `sft`
- **Password**: `sftcattle`
- **Type**: Top-Level User

This user has full access to:
- View and manage all feedlot instances
- Create new feedlots
- Create additional top-level users
- Create feedlot users for any feedlot

### User Types

The application supports two user types:

1. **Top-Level Users**: Access the main hub and all feedlots, can manage all aspects of the system
2. **Feedlot Users**: Access only their assigned feedlot, limited to feedlot-specific operations

### Creating Your First Feedlot

1. Login with the default admin credentials (sft / sftcattle)
2. Navigate to the dashboard
3. Click "Create New Feedlot"
4. Fill in feedlot details
5. Start managing pens, batches, and cattle

## Project Structure

```
herdlinx-saas/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models/              # Database models
│   │   ├── user.py          # User model
│   │   ├── feedlot.py       # Feedlot model
│   │   ├── pen.py           # Pen model
│   │   ├── batch.py         # Batch model
│   │   └── cattle.py        # Cattle model
│   ├── routes/              # Application routes
│   │   ├── auth_routes.py   # Authentication routes
│   │   ├── top_level_routes.py  # Top-level routes
│   │   └── feedlot_routes.py    # Feedlot routes
│   └── templates/           # HTML templates
│       ├── base.html        # Base template
│       ├── auth/            # Authentication templates
│       ├── top_level/       # Top-level templates
│       └── feedlot/         # Feedlot templates
├── config.py                # Configuration settings
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Database Schema

### Collections

1. **users**: User accounts (top-level and feedlot)
2. **feedlots**: Feedlot instances/tenants
3. **pens**: Physical pen locations within feedlots
4. **batches**: Groups of cattle inducted together
5. **cattle**: Individual cattle records

### Relationships

- Feedlots contain multiple pens and batches
- Batches contain multiple cattle
- Cattle are assigned to pens
- Users are associated with feedlots (for feedlot-level users)

## Usage Guide

### Top-Level Hub

- View all feedlot instances
- Create, edit, and manage feedlots
- Navigate to individual feedlot dashboards

### Feedlot Instance

- **Dashboard**: Overview of feedlot statistics
- **Pens**: Manage pens with capacity tracking
- **Batches**: Record cattle induction in groups
- **Cattle**: Individual cattle records and tracking

### Adding Cattle

1. Create a batch first
2. Add pens for cattle housing
3. Add cattle to the batch
4. Assign cattle to pens (optional)
5. Monitor capacity and health status

## Security Features

- Password hashing using bcrypt
- Session-based authentication
- Role-based access control
- Multi-level user isolation
- Input validation
- Secure password handling

## Responsive Design

The application is fully responsive and supports:
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

All features are accessible across all device sizes with optimized layouts.

## Development

### Running in Development Mode

```bash
python run.py
```

The application will run with debug mode enabled.

### Code Structure

- **Models**: Database operations using PyMongo
- **Routes**: Flask blueprints for different sections
- **Templates**: Jinja2 templates with Tailwind CSS
- **Authentication**: Decorators for access control

## Configuration

Edit `config.py` or environment variables in `.env` to configure:
- MongoDB connection
- Secret keys
- Session settings
- Application preferences

## Troubleshooting

### MongoDB Connection Issues

- Ensure MongoDB is running
- Check `MONGODB_URI` in `.env`
- Verify network connectivity

### Port Already in Use

Change the port in `run.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

## License

This project is for demonstration purposes.

## Support

For issues or questions, please contact the development team.

