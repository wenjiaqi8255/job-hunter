import os
from supabase import create_client, Client
from django.conf import settings
from django.contrib.auth.models import User # Import User

def get_supabase_client():
    """Initializes and returns the Supabase client."""
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    if not url or not key:
        print("Supabase URL or Key not configured.")
        return None
    return create_client(url, key)

def get_user_experiences(user: User) -> list:
    """Fetches all work experiences for a specific user from Supabase."""
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        # The user's username is the Supabase user UUID
        user_id = user.username
        response = supabase.table('work_experiences') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching experiences for user {user_id} from Supabase: {e}")
        return []

def delete_experience(experience_id: str, user: User):
    """Deletes a specific work experience from Supabase, ensuring user ownership."""
    if not experience_id:
        raise ValueError("Experience ID cannot be null.")

    supabase = get_supabase_client()
    if not supabase:
        raise ConnectionError("Could not connect to Supabase.")

    try:
        user_id = user.username
        # This delete operation ensures that a user can only delete an experience
        # that matches both the experience_id and their own user_id.
        response = supabase.table('work_experiences') \
            .delete() \
            .eq('id', experience_id) \
            .eq('user_id', user_id) \
            .execute()
        
        if not response.data:
            raise ValueError("Record not found or user does not have permission to delete.")
            
        return response
    except Exception as e:
        print(f"Error deleting experience {experience_id} from Supabase: {e}")
        # Re-raise the exception to be handled by the view
        raise e