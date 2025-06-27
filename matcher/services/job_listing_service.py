from django.conf import settings
from supabase import create_client, Client
import os
from datetime import datetime, date, time

# Initialize Supabase client
supabase: Client | None = None
try:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL or Key not found in environment variables.")
    supabase = create_client(supabase_url, supabase_key)
    print("INFO: Supabase client initialized successfully for job_listing_service.")
except (ValueError, Exception) as e:
    print(f"ERROR: Failed to initialize Supabase client for job_listing_service: {e}")
    # supabase remains None

def fetch_todays_job_listings_from_supabase():
    """
    Fetches job listings from Supabase that were created today.
    """
    if not supabase:
        print("ERROR: Supabase client not available in fetch_todays_job_listings_from_supabase.")
        return []
    try:
        today = date.today()
        start_of_day = datetime.combine(today, time.min).isoformat()
        end_of_day = datetime.combine(today, time.max).isoformat()

        # Assuming the table is named 'job_listings'
        response = supabase.table('job_listings').select('*').gte('created_at', start_of_day).lte('created_at', end_of_day).execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f"ERROR: Could not fetch today's job listings from Supabase: {e}")
        return []

def fetch_anomaly_analysis_for_jobs_from_supabase(job_ids: list):
    """
    Fetches anomaly analysis for a list of job IDs from Supabase.
    """
    if not supabase or not job_ids:
        if not supabase:
            print("ERROR: Supabase client not available in fetch_anomaly_analysis_for_jobs_from_supabase.")
        return {}
    try:
        # The job_ids are UUIDs, so they should be strings
        str_job_ids = [str(job_id) for job_id in job_ids]
        
        # Assuming the table is named 'job_anomaly_analysis'
        response = supabase.table('job_anomaly_analysis').select('*').in_('job_id', str_job_ids).execute()
        
        if response.data:
            # Return a map of job_id -> anomaly_data
            return {item['job_id']: item for item in response.data}
        return {}
    except Exception as e:
        print(f"ERROR: Could not fetch anomaly analysis from Supabase for jobs {job_ids}: {e}")
        return {}
