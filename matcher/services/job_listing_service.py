from supabase import Client
import os
from datetime import datetime, date, time

def fetch_todays_job_listings_from_supabase(supabase: Client):
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

def fetch_anomaly_analysis_for_jobs_from_supabase(supabase: Client, job_ids: list):
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
        response = supabase.table('job_anomaly_analysis').select('*').in_('job_listing_id', str_job_ids).execute()
        
        if response.data:
            # Return a map of job_id -> anomaly_data
            return {item['job_listing_id']: item for item in response.data}
        return {}
    except Exception as e:
        print(f"ERROR: Could not fetch anomaly analysis from Supabase for jobs {job_ids}: {e}")
        return {}
