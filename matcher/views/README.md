# Views Refactoring Documentation

## Refactoring Overview

The original `views.py` file contained over 800 lines of code. To improve maintainability and code organization, we have refactored it into multiple specialized modules.

## New File Structure

```
matcher/views/
├── __init__.py              # Import all views for backward compatibility
├── auth_views.py            # Authentication-related views (OAuth, login, logout)
├── main_views.py            # Homepage views and job matching logic
├── profile_views.py         # User profile management
├── job_views.py             # Job detail pages
├── application_views.py     # Job application related (cover letters, resume customization, application management)
└── experience_views.py      # Work experience management
```

## Module Responsibilities

### 1. `auth_views.py` - Authentication Management
- `google_login()` - Initiate Google OAuth login
- `google_callback()` - Handle OAuth callback
- `logout_view()` - User logout
- `api_check_auth()` - API authentication status check
- `process_oauth_tokens()` - Process client OAuth tokens
- Helper functions: `get_current_user_info()`, `logout_user()`

### 2. `main_views.py` - Homepage and Matching Logic
- `main_page()` - Homepage view, handles job matching
- Internal helper functions:
  - `_handle_oauth_callback_on_main_page()` - Handle OAuth callback on homepage
  - `_handle_job_matching_post()` - Handle job matching POST requests
  - `_save_job_matches_to_db()` - Save matching results to database
  - `_handle_session_view_get()` - Handle viewing specific matching sessions
  - `_process_matched_jobs_for_session()` - Process job list in matching sessions

### 3. `profile_views.py` - User Profile
- `profile_page()` - User profile page
  - CV text management
  - PDF file upload and text extraction
  - User preference settings

### 4. `job_views.py` - Job Details
- `job_detail_page()` - Job detail page
  - Display job information
  - Matching analysis and recommendations
  - Exception analysis display
  - Application status management

### 5. `application_views.py` - Application Management
- `generate_cover_letter_page()` - Generate cover letters
- `generate_custom_resume_page()` - Generate custom resumes
- `download_custom_resume()` - Download resume PDF
- `my_applications_page()` - My applications management
- `update_job_application_status()` - Update application status

### 6. `experience_views.py` - Experience Management
- `experience_list()` - Work experience list
- `experience_delete()` - Delete work experience
- `experience_completed_callback()` - N8n completion callback

## Backward Compatibility

To ensure existing code is not broken:

1. **Original `views.py`** is now just a simple import file that imports all views from the new submodules
2. **URL configuration** requires no changes, all views can still be accessed via `views.function_name`
3. **Import statements** like `from matcher import views` in other files remain valid

## Benefits of Refactoring

1. **Code Organization** - Related functionality grouped in the same module
2. **Maintainability** - Smaller files are easier to understand and modify
3. **Testing** - Unit tests can target specific functional modules
4. **Team Collaboration** - Different developers can focus on different functional modules
5. **Separation of Concerns** - Each module has clear responsibilities
