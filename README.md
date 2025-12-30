# Todo App

A Django-based Todo application with API endpoints for managing tasks.

## Features

- User registration and authentication
- CRUD operations on tasks
- Web interface with HTML templates
- RESTful API endpoints
- SQLite database
- Comprehensive testing

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Run the server: `python manage.py runserver`

## Usage

### Web Interface

- Visit the home page to view and manage tasks
- Register or login to access task management
- Add, edit, and delete tasks through the web forms

### API Endpoints

All API endpoints require authentication.

#### GET /api/tasks/
Retrieve all tasks for the authenticated user.

Response:
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Task Title",
      "description": "Task Description",
      "due_date": "2023-12-31T23:59:00Z",
      "status": "pending",
      "created_at": "2023-12-01T00:00:00Z",
      "updated_at": "2023-12-01T00:00:00Z"
    }
  ]
}
```

#### POST /api/tasks/
Create a new task.

Request:
```json
{
  "title": "New Task",
  "description": "Description",
  "due_date": "2023-12-31T23:59:00Z",
  "status": "pending"
}
```

Response:
```json
{
  "id": 1,
  "message": "Task created"
}
```

#### GET /api/tasks/<id>/
Retrieve a specific task.

#### PUT /api/tasks/<id>/
Update a task.

Request: Same as POST

Response:
```json
{
  "message": "Task updated"
}
```

#### DELETE /api/tasks/<id>/
Delete a task.

Response:
```json
{
  "message": "Task deleted"
}
```

## Testing

The application includes comprehensive test coverage using Django's test framework.

### Running Tests
- Run all tests: `python manage.py test`
- Run specific test class: `python manage.py test todoapp.tests.APITestCase`
- Run specific test method: `python manage.py test todoapp.tests.APITestCase.test_api_tasks_get`

### Test Coverage
- **API Endpoints**: Tests for all CRUD operations, authentication, and error handling
- **Forms**: Validation tests for user registration, login, and task forms
- **Views**: Tests for web interface views, redirects, and user permissions
- **Database**: Tests for raw SQL operations and data integrity

### Testing Considerations
- Tests use an in-memory SQLite database for isolation
- Authentication is tested to ensure user data security
- API tests verify JSON responses and proper HTTP status codes
- Form tests check validation rules and error messages
- All tests are designed to run independently without side effects

## Deployment

### Local Development
Follow the setup instructions above for local development.

### Production Deployment

#### Prerequisites
- Python 3.8+
- Virtual environment
- Web server (e.g., Nginx)
- Application server (e.g., Gunicorn)

#### Steps
1. **Prepare the Application**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd todoapp
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install gunicorn  # For production server
   ```

2. **Configure Settings**
   - Set `DEBUG = False` in `todoproj/settings.py`
   - Configure `ALLOWED_HOSTS` with your domain
   - Set up environment variables for sensitive data (SECRET_KEY, database credentials)
   - Configure logging for production (e.g., to files or external services)

3. **Database Setup**
   ```bash
   python manage.py migrate
   python manage.py collectstatic  # If using static files
   ```

4. **Run with Gunicorn**
   ```bash
   gunicorn todoproj.wsgi:application --bind 0.0.0.0:8000
   ```

5. **Configure Nginx (Optional)**
   Create `/etc/nginx/sites-available/todoapp`:
   ```
   server {
       listen 80;
       server_name your-domain.com;
       
       location = /favicon.ico { access_log off; log_not_found off; }
       
       location / {
           include proxy_params;
           proxy_pass http://127.0.0.1:8000;
       }
   }
   ```
   
   Enable the site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/todoapp /etc/nginx/sites-enabled
   sudo systemctl restart nginx
   ```

6. **SSL Configuration (Recommended)**
   Use Let's Encrypt for free SSL certificates:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Environment Variables For Production Setup and Deployment
Create a `.env` file or set environment variables:
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=sqlite:///db.sqlite3  # Or PostgreSQL/MySQL for production
```

### Deployment Considerations
- Use a production database (PostgreSQL recommended) instead of SQLite
- Set up proper logging and monitoring
- Configure backups for the database
- Use environment-specific settings
- Implement proper error handling and user feedback
- Consider using Docker for containerized deployment
- Set up CI/CD pipelines for automated testing and deployment
- Monitor application performance and security

## Notes

- Uses raw SQL queries instead of Django ORM for task operations
- Logging is configured to file for errors
- Use Class-Based Views for a large production-based TODO App.
- Exception handling is implemented in views
- Templates are integrated with the API logic
