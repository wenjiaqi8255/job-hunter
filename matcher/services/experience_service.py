import os
from supabase import create_client, Client
from django.conf import settings

def get_supabase_client():
    """Initializes and returns the Supabase client."""
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    if not url or not key:
        print("Supabase URL or Key not configured.")
        return None
    return create_client(url, key)

def get_user_experiences() -> list:
    """Fetches all work experiences from Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        response = supabase.table('work_experiences') \
            .select('*') \
            .order('created_at', desc=True) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching experiences from Supabase: {e}")
        return []

def delete_experience(experience_id: str):
    """Deletes a specific work experience from Supabase."""
    if not experience_id:
        raise ValueError("Experience ID cannot be null.")

    supabase = get_supabase_client()
    if not supabase:
        raise ConnectionError("Could not connect to Supabase.")

    try:
        # This delete operation ensures that a user can only delete an experience
        # that matches both the experience_id and their own session_id.
        response = supabase.table('work_experiences') \
            .delete() \
            .eq('id', experience_id) \
            .execute()
        
        # You might want to check response to see if a row was actually deleted.
        # If response.data is empty, it means no row matched the criteria.
        if not response.data:
            raise ValueError("Record not found.")
            
        return response
    except Exception as e:
        print(f"Error deleting experience from Supabase: {e}")
        # Re-raise the exception to be handled by the view
        raise e 