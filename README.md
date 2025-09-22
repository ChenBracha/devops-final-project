# Budget App with Google OAuth

A family budget management application built with Flask, featuring Google OAuth authentication and JWT-based API access.

## Features

- 🔐 **Google OAuth Authentication** - Sign in with your Google account
- 👨‍👩‍👧‍👦 **Family Budget Sharing** - Share budgets with family members
- 📊 **Category Management** - Create and manage expense categories
- 🎯 **Budget Tracking** - Set monthly budgets and track spending
- 🔒 **Secure API** - JWT-protected REST API endpoints

## Quick Start

### 1. Google OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set the application type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:8888/auth/google/callback`
   - `http://127.0.0.1:8888/auth/google/callback`
7. Copy the Client ID and Client Secret

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql+psycopg2://app:app@db:5432/app
POSTGRES_DB=app
POSTGRES_USER=app
POSTGRES_PASSWORD=app

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-me-in-production

# Flask Session Secret
SECRET_KEY=your-flask-secret-key-change-me-in-production

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=1
```

### 3. Run the Application

```bash
# Build and start the services
docker-compose up --build

# The application will be available at:
# http://localhost:8888
```

## Usage

### Authentication

1. **Google OAuth**: Click "Continue with Google" on the login page
2. **Email/Password**: Use the traditional login form (for existing users)

### API Access

After authentication, you'll receive a JWT token that's automatically stored in localStorage. Use this token to access protected API endpoints:

```bash
# Get categories
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8888/api/categories

# Create a category
curl -X POST -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Groceries", "monthly_budget": 500}' \
     http://localhost:8888/api/categories
```

## API Endpoints

### Authentication
- `GET /login` - Login page with Google OAuth
- `GET /auth/google` - Initiate Google OAuth flow
- `GET /auth/google/callback` - OAuth callback handler
- `GET /auth/logout` - Logout and clear session
- `POST /api/auth/login` - Email/password login
- `POST /api/auth/register` - User registration

### Protected Endpoints
- `GET /dashboard` - User dashboard
- `GET /api/categories` - List categories
- `POST /api/categories` - Create category
- `GET /api/health` - Health check

## Development

### Project Structure

```
devops-final-project/
├── app/
│   ├── __init__.py
│   └── main.py          # Flask application with OAuth
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── Dockerfile
├── requirements.txt     # Python dependencies
└── README.md
```

### Database Schema

- **families** - Family groups for budget sharing
- **users** - User accounts with Google OAuth support
- **categories** - Expense categories with monthly budgets
- **transactions** - Individual expense records

### Security Features

- JWT tokens for API authentication
- Google OAuth 2.0 integration
- Session state validation
- Family-scoped data access
- Secure password hashing (for email/password users)

## Deployment

The application is containerized and ready for deployment:

1. **Development**: Use `docker-compose up --build`
2. **Production**: Update environment variables and deploy containers

### Environment Variables for Production

Make sure to set secure values for:
- `JWT_SECRET_KEY` - Use a strong random key
- `SECRET_KEY` - Flask session secret
- `GOOGLE_CLIENT_ID` - Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Your Google OAuth client secret

## Troubleshooting

### Common Issues

1. **OAuth not working**: Check that redirect URIs match exactly in Google Console
2. **Database connection**: Ensure PostgreSQL container is running
3. **Missing environment variables**: Verify all required vars are set in `.env`

### Logs

```bash
# View application logs
docker-compose logs web

# View all service logs
docker-compose logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.