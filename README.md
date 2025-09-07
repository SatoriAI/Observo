# Observo

## Setup

### Prerequisites
- Python 3.12+
- Redis server running on localhost:6379 (default) or configure via `CELERY_BROKER_URL` environment variable

### Installation
1. Install dependencies:
```bash
pip install -e .
```

2. Set up your environment variables in `.env` file:
```bash
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
IP_SALT=your-ip-salt
CALENDLY_KEY=your-calendly-key
EMAIL_HOST_USER=your-email-user
EMAIL_HOST_PASSWORD=your-email-password
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Running the Application

### Development Server
```bash
python observo/manage.py runserver
```

### Celery Worker
To run the Celery worker for background tasks:

1. Make sure Redis is running on your system
2. Start the Celery worker:
```bash
cd observo
celery -A observo worker --loglevel=info
```

### Using Celery Tasks
The application includes an email notification task that can be called asynchronously:

```python
from analytics.tasks import notify_contact

# Call the task asynchronously
notify_contact.delay(contact_id=123)
```

### Production Deployment
For production, you might want to run Celery with multiple workers and use a process manager:

```bash
# Run multiple workers
celery -A observo worker --loglevel=info --concurrency=4

# Or use celery multi (recommended for production)
celery -A observo multi start w1 -l info --concurrency=4
```

### Railway Deployment
For Railway deployment, use the Railway service configuration in `.railway/celery.toml`:

1. **Environment Variables** for Railway:
   - Set `CELERY_BROKER_URL` to your Redis service URL
   - Set `CELERY_RESULT_BACKEND` to your Redis service URL
   - Ensure all other required environment variables are set

2. **Railway Service Setup**:
   - Create a separate Railway service for Celery
   - The service will automatically use `.railway/celery.toml` configuration
   - Connect it to the same Redis service as your Django app

3. **Service Configuration**:
   - Uses the same Dockerfile as the main Django app
   - Runs Celery worker with optimized settings for Railway
   - Includes conservative concurrency (2 workers) for Railway's containers
   - Single queue setup as configured

The Railway configuration automatically handles:
- Optimized concurrency settings for Railway
- Proper logging configuration
- Health check settings
- Container deployment

## Configuration

### Celery Settings
The following Celery settings can be configured via environment variables:

- `CELERY_BROKER_URL`: Redis broker URL (default: redis://localhost:6379/0)
- `CELERY_RESULT_BACKEND`: Result backend URL (default: redis://localhost:6379/0)

### Default Queue
The application uses a single default queue named "celery". All tasks will be routed to this queue.
