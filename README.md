# JobbAI - AI-Powered Job Hunting Assistant

JobbAI is a Django-based web application designed to streamline the job hunting process. It leverages the Google Gemini API to intelligently match candidates with job listings, customize resumes for specific roles, and generate compelling cover letters. User authentication is securely handled by Supabase.

## Features

-   **AI-Powered Job Matching**: Analyzes your resume and preferences to find the best job matches from a comprehensive list of openings.
-   **Custom Resume Generation**: Tailors your resume to highlight the most relevant skills and experiences for a specific job description.
-   **Cover Letter Assistance**: Generates opening paragraphs for cover letters to help you get started.
-   **Application Tracking**: Save jobs and track your application status.
-   **Secure Authentication**: Manages user sign-up, login, and profiles using Supabase.

## Tech Stack

-   **Backend**: Python, Django
-   **AI Engine**: Google Gemini API
-   **Database**: SQLite (for local development)
-   **Authentication**: Supabase
-   **Dependency Management**: Poetry
-   **Frontend**: Django Template Language (DTL), HTML, CSS

## Getting Started

Follow these instructions to set up and run the project on your local machine for development and testing purposes.

### 1. Prerequisites

-   [Python 3.11+](https://www.python.org/downloads/)
-   [Poetry](https://python-poetry.org/docs/#installation) for managing dependencies.

### 2. Clone the Repository

```bash
git clone https://github.com/wenjiaqi8255/job-hunter.git
cd job_hunter
```

### 3. Set Up Environment Variables

You will need to configure your environment variables. In the project root directory, create a file named `.env`.

Copy the following content into your new `.env` file and fill in the required values.

```ini

# AI Simulation
# Set to 'False' to use the real Gemini API.
# If 'True' or not set, the app will use simulated AI responses (no API key needed).
USE_SIMULATION_ENV="True"

# Google Gemini API Key (only required if USE_SIMULATION_ENV is 'False')
GEMINI_API_KEY=""

# Supabase Credentials (Required for user authentication)
SUPABASE_URL=""
SUPABASE_KEY=""

GOOGLE_CLIENT_ID=""
GOOGLE_CLIENT_SECRET=""
```

**Key Variable Explanations:**

-   `DJANGO_SECRET_KEY`: A unique, secret key for your Django installation. You can generate one easily [here](https://djecrety.ir/).
-   `USE_SIMULATION_ENV`: **This is the most important setting for testing.** Set it to `True` to run the application without needing a `GEMINI_API_KEY`. The AI features will return simulated data, allowing the full application workflow to be tested.
-   `GEMINI_API_KEY`: Only required if you set `USE_SIMULATION_ENV=False`. Get your key from the [Google AI Studio](https://aistudio.google.com/app/apikey).
-   `SUPABASE_URL` & `SUPABASE_KEY`: These are required for user login and registration. You can get them from your Supabase project's API settings.

### 4. Install Dependencies

Use Poetry to install all the project dependencies specified in `pyproject.toml`. This will create a virtual environment for the project.

```bash
poetry install --no-root
```

### 5. Initialize the Database

First, apply the database migrations to set up the required tables. Then, load the provided seed data from the fixture file.

```bash
# Activate the virtual environment
source "$(poetry env info --path)/bin/activate"

# Apply migrations
python manage.py migrate

# Load initial data (User Profiles, Job Listings, etc.)
python manage.py loaddata initial_data.json
```

### 6. Run the Development Server

You're all set! Start the Django development server.

```bash
python manage.py runserver
```

The application will be running at `http://127.0.0.1:8000/`.

## How to Use the App

1.  Navigate to `http://127.0.0.1:8000/`.
2.  Use an test account or register for a new account.
3.  On the main page, upload your CV (PDF format) and enter your job preferences.
4.  Click "Find Matches" to see a list of jobs scored and ranked by the AI.
5.  Click on any job to view details, generate a custom resume, or create a cover letter.
6.  Use the "My Applications" page to track jobs you've saved or applied to.
