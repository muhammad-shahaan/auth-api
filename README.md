# Auth API — FastAPI + Supabase Authentication

A secure authentication API built with Python, FastAPI, and Supabase Auth.

The project demonstrates how users can sign up, log in, receive a JWT access token, access protected routes, and log out. Protected endpoints verify the user's token before returning private data.

## Features

- User Sign Up
- User Log In
- JWT Access Tokens
- Refresh Tokens
- Public API route
- Protected profile route
- Protected dashboard route
- Reusable authentication dependency
- Bearer Token authentication
- Logout endpoint
- Swagger UI authentication
- Supabase Auth integration
- Environment variables for secrets
- Proper HTTP status codes and error handling

## Technologies Used

- Python
- FastAPI
- Supabase Auth
- JWT / Bearer Tokens
- Pydantic
- Uvicorn
- python-dotenv
- Git
- GitHub

## Authentication Flow

The authentication flow works like this:

1. A user signs up using an email and password.
2. Supabase creates and manages the user account.
3. The user logs in through the API.
4. Supabase returns an Access Token (JWT) and Refresh Token.
5. The client sends the JWT with protected requests.
6. The FastAPI backend verifies the JWT with Supabase.
7. Valid users can access protected routes.
8. Missing, invalid, or expired tokens are rejected.

Protected requests use the following HTTP header:

```text
Authorization: Bearer <access_token>
```

## API Endpoints

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| GET | `/` | No | Check that the API is running |
| POST | `/auth/signup` | No | Create a new user |
| POST | `/auth/login` | No | Authenticate a user and return tokens |
| POST | `/auth/logout` | Yes | Log out an authenticated user |
| GET | `/public/info` | No | Read public information |
| GET | `/protected/profile` | Yes | Read the authenticated user's profile |
| GET | `/protected/dashboard` | Yes | Access a protected dashboard |

## HTTP Status Codes

The API uses appropriate HTTP status codes:

- `200 OK` — successful login or protected/public request
- `201 Created` — successful user signup
- `204 No Content` — successful logout
- `400 Bad Request` — missing or invalid signup/login input
- `401 Unauthorized` — invalid login, missing token, or invalid/expired token
- `422 Unprocessable Content` — malformed request body

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/muhammad-shahaan/auth-api.git
cd auth-api
```

### 2. Install Dependencies

Using `requirements.txt`:

```bash
py -m pip install -r requirements.txt
```

### 3. Create a Supabase Project

Create a Supabase project and obtain:

- Project URL
- Publishable / Anon Key

### 4. Create Environment Variables

Create a `.env` file in the project directory.

You can use `.env.example` as a template:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_publishable_key
```

The real `.env` file is ignored by Git and must never be committed to GitHub.

### 5. Run the API

```bash
py -m uvicorn main:app --reload
```

The API will run locally at:

```text
http://127.0.0.1:8000
```

## Swagger UI

FastAPI automatically provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

Protected routes display a lock icon because the API uses FastAPI's `HTTPBearer` security scheme.

### Testing Authentication in Swagger

1. Run `POST /auth/login`.
2. Copy only the returned `access_token`.
3. Click the lock icon on a protected route.
4. Paste only the JWT into the authorization value field.
5. Click **Authorize**.
6. Test `/protected/profile` or `/protected/dashboard`.

Swagger automatically sends the token using:

```text
Authorization: Bearer <access_token>
```

## Tested Authentication Behaviour

The authentication flow was tested through Swagger UI.

### Successful Login

A valid email and password return:

```text
200 OK
```

The response includes an Access Token and Refresh Token.

### Protected Route Without Token

Calling a protected endpoint without authentication returns:

```text
401 Unauthorized
```

### Protected Route With Valid Token

After authorizing with a valid JWT, a protected endpoint returns:

```text
200 OK
```

The API then returns authenticated user information.

### Logout

A valid authenticated logout request returns:

```text
204 No Content
```

## Security

Sensitive Supabase credentials are stored in environment variables rather than directly in the source code.

The real environment file is excluded through `.gitignore`:

```text
.env
```

The project does not intentionally publish passwords, Supabase keys, access tokens, or refresh tokens to GitHub.

Protected routes use a reusable FastAPI dependency to verify the authenticated user before allowing access.

## Swagger UI Screenshot

The screenshot below shows the Auth API routes in FastAPI Swagger UI, including the protected endpoints with Bearer authentication.

![Auth API Swagger UI](screenshots/swagger-ui.png)

## What I Learned

This project helped me understand how authentication works between a client, backend server, and external identity provider.

I learned how users authenticate with Supabase, how JWT access tokens are returned after login, how Bearer Tokens are sent through HTTP Authorization headers, and how a FastAPI backend can verify those tokens before allowing access to protected endpoints.

I also practiced separating authentication logic into a reusable FastAPI dependency instead of repeating token verification inside every protected route.

Finally, I configured Swagger UI with Bearer authentication and tested successful login, unauthorized access, protected routes, and logout through the browser.

## Repository

GitHub:

https://github.com/muhammad-shahaan/auth-api