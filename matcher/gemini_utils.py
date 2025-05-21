import os
import google.generativeai as genai
import json
import random
from django.conf import settings # Import Django settings

# Configure the Gemini API client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# print(f"DEBUG: GEMINI_API_KEY from env: '{GEMINI_API_KEY}'") # Keep this commented out for normal use
model = None

if not settings.USE_AI_SIMULATION: # Only configure API if not simulating
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # Using a model that supports function calling or structured output is ideal.
            # 'gemini-1.5-flash-latest' is a good candidate for speed and capability.
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            print("Gemini API configured successfully for job matching.")
        except Exception as e:
            print(f"ERROR: Could not configure Gemini API: {e}. AI features will be effectively simulated.")
            model = None # Ensure model is None if config fails
    else:
        print("WARNING: GEMINI_API_KEY environment variable not found. AI features will be effectively simulated.")
        model = None # Ensure model is None if key is not found
else:
    print("INFO: USE_AI_SIMULATION is True. AI calls will be simulated.")
    model = None # Ensure model is None when simulating

def parse_gemini_batch_json_response(response_text):
    """Attempts to parse a JSON array from Gemini's text response.
       Handles cases where the JSON might be wrapped in backticks or have leading/trailing text.
    """
    # Find the start of the array and end of the array
    start_index = response_text.find('[')
    end_index = response_text.rfind(']')

    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = response_text[start_index : end_index + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError for batch response: {e} in string: '{json_str}'")
            raise # Re-raise the error to be caught by the caller
    else:
        print(f"Could not find valid JSON array in batch response: {response_text}")
        raise json.JSONDecodeError("No valid JSON array found in batch response string", response_text, 0)

def match_jobs(skills_text, job_listings):
    """Uses Gemini API or simulation to match jobs based on skills."""
    if settings.USE_AI_SIMULATION or not model:
        if not model and not settings.USE_AI_SIMULATION:
            print("Gemini API not available (model not loaded), falling back to simulated matching for jobs.")
        else:
            print("Using simulated matching for jobs (USE_AI_SIMULATION is True).")
        return simulate_match_jobs(skills_text, job_listings)

    # Prepare jobs data for the prompt
    jobs_data_for_prompt = []
    for job in job_listings:
        jobs_data_for_prompt.append({
            "id": str(job.id), # Ensure ID is string for JSON consistency
            "title": job.job_title,
            "company": job.company_name,
            "description": job.description[:1500] # Truncate long descriptions to manage token limits
        })
    
    jobs_json_string = json.dumps(jobs_data_for_prompt, indent=2)

    prompt = f"""
    You are a job matching assistant. Based on the provided user skills and a list of jobs, please evaluate each job.
    For each job in the list, provide a matching score between 0 and 100, and a brief 1-2 sentence reason for the score.

    User Skills:
    {skills_text}

    Job Listings (JSON Array):
    {jobs_json_string}

    Your Response Format:
    Return a single, valid JSON array. Each object in the array should correspond to one job from the input list and MUST contain the following keys:
    - "id": The original ID of the job from the input list.
    - "score": An integer between 0 and 100 representing the match score.
    - "reason": A brief string (1-2 sentences) explaining the score.
    Example for a single job in the array: {{"id": "some_job_id", "score": 85, "reason": "Excellent match due to strong Python skills and relevant project experience."}}
    Ensure the output is ONLY the JSON array, starting with '[' and ending with ']'.
    """

    api_response_text = None
    try:
        print("--- Sending single batch prompt to Gemini for job matching ---")
        response = model.generate_content(prompt)
        api_response_text = response.text
        
        api_results_array = parse_gemini_batch_json_response(api_response_text)
        
        api_scores_reasons = {{item['id']: {'score': int(item.get('score', 0)), 'reason': str(item.get('reason', 'N/A'))} for item in api_results_array}}

        matched_results = []
        for job in job_listings:
            job_id_str = str(job.id)
            if job_id_str in api_scores_reasons:
                score = max(0, min(100, api_scores_reasons[job_id_str]['score']))
                reason = api_scores_reasons[job_id_str]['reason']
            else:
                print(f"Warning: Job ID {job_id_str} not found in Gemini's batch response.")
                score = 0 
                reason = "Not processed by API in this batch or ID mismatch."
            
            matched_results.append({
                'job': job,
                'score': score,
                'reason': reason
            })

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON array from Gemini batch response for match_jobs. Error: {e}. Raw response was: {api_response_text}")
        return simulate_match_jobs(skills_text, job_listings)
    except Exception as e:
        print(f"ERROR: Gemini API batch call or other processing failed for match_jobs: {e}")
        return simulate_match_jobs(skills_text, job_listings)

    matched_results.sort(key=lambda x: x['score'], reverse=True)
    return matched_results

# Renamed the old simulation function to be a clear fallback
def simulate_match_jobs(skills_text, job_listings):
    """Simulates job matching when the Gemini API is not available or a batch call fails."""
    print("Executing SIMULATED job matching.")
    matched_results = []
    skills_lower = skills_text.lower()
    for job in job_listings:
        score = random.randint(40, 90)
        reason_fragments = ["Simulated:"]
        if 'python' in skills_lower and 'python' in job.job_title.lower():
            score = min(100, score + 10)
            reason_fragments.append("Python skill noted.")
        if not reason_fragments or len(reason_fragments) == 1:
            reason_fragments.append("General simulated match.")
        reason = " ".join(reason_fragments)
        score = max(0, min(100, score))
        matched_results.append({
            'job': job,
            'score': score,
            'reason': reason
        })
    matched_results.sort(key=lambda x: x['score'], reverse=True)
    return matched_results

def generate_cover_letter(skills_text, job):
    """Uses Gemini API or simulation to generate a cover letter opening."""
    if settings.USE_AI_SIMULATION or not model:
        if not model and not settings.USE_AI_SIMULATION:
            print("Gemini API not available (model not loaded), falling back to simulated cover letter.")
        else:
            print("Using simulated cover letter generation (USE_AI_SIMULATION is True).")
        return f"(Simulated Cover Letter for {job.job_title} at {job.company_name}) Based on your skills in {skills_text[:50]}..., this job seems like a good fit because... (simulated reason)."

    prompt = f"""
    Based on the following user skills and job details, write a concise and compelling opening paragraph for a cover letter (1-2 sentences maximum).
    
    User Skills: {skills_text}
    Job: {job.job_title} at {job.company_name} - {job.description}
    
    Cover Letter Opening Paragraph:
    """
    try:
        print(f"--- Sending prompt to Gemini for cover letter: {job.job_title} ---")
        response = model.generate_content(prompt)
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            return f"Could not generate cover letter due to safety settings. Reason: {response.prompt_feedback.block_reason}"
        return response.text.strip()
    except Exception as e:
        print(f"ERROR: Cover letter generation API call failed for job '{job.job_title}': {e}")
        return "(Error generating cover letter via API. Please try again.)" 