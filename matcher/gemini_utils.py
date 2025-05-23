import os
import google.generativeai as genai
import json
import random
from django.conf import settings # Import Django settings

# Configure the Gemini API client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# print(f"DEBUG: GEMINI_API_KEY from env: '{GEMINI_API_KEY}'") # Keep this commented out for normal use
model = None

# Centralized API configuration
if not settings.USE_AI_SIMULATION:
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

def parse_gemini_object_json_response(response_text):
    """
    Attempts to parse a single JSON object from Gemini's text response.
    Handles cases where the JSON might be wrapped in backticks (```json ... ```) 
    or have leading/trailing text.
    """
    # Try to find JSON within triple backticks (```json ... ```)
    if '```json' in response_text:
        start_marker = response_text.find('```json') + len('```json')
        end_marker = response_text.rfind('```')
        if start_marker != -1 and end_marker != -1 and end_marker > start_marker:
            json_str = response_text[start_marker:end_marker].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSONDecodeError within backticks: {e} in string: '{json_str}'")
                # Fall through to try parsing the whole string if this fails
    
    # If not in backticks or parsing within backticks failed, try to find the first '{' and last '}'
    start_index = response_text.find('{')
    end_index = response_text.rfind('}')

    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = response_text[start_index : end_index + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError for object response: {e} in string: '{json_str}'")
            # If this also fails, try to load the whole string as a last resort if it looks like JSON
            if response_text.strip().startswith("{") and response_text.strip().endswith("}"):
                try:
                    return json.loads(response_text.strip())
                except json.JSONDecodeError:
                    pass # Original error will be re-raised
            raise # Re-raise the specific error from the { } block attempt
    else:
        print(f"Could not find valid JSON object in response: {response_text}")
        raise json.JSONDecodeError("No valid JSON object found in response string", response_text, 0)

def extract_user_profile(user_cv_text, user_preferences_text):
    """
    Uses Gemini API or simulation to extract a structured user profile 
    from CV text and user preferences.
    """
    if settings.USE_AI_SIMULATION or not model:
        if not model and not settings.USE_AI_SIMULATION:
            print("Gemini API not available (model not loaded), falling back to simulated user profile extraction.")
        else:
            print("Using simulated user profile extraction (USE_AI_SIMULATION is True).")
        return simulate_extract_user_profile(user_cv_text, user_preferences_text)

    prompt = f"""
    You are an expert HR and career consultant. Analyze the provided User CV/Resume Text and User Preferences.
    Extract key information and return it as a single, valid JSON object.

    User CV/Resume Text:
    ---
    {user_cv_text}
    ---

    User Preferences Text:
    ---
    {user_preferences_text}
    ---

    Based on the above, provide a JSON object with the following structure and content:
    {{
        "summary": "A concise 2-3 sentence professional summary of the candidate.",
        "key_skills": [
            "skill1", "skill2", "relevant_technology", "methodology" 
        ],
        "experience_level": "Determine one of: Entry-Level, Junior, Mid-Level, Senior, Lead, Principal, Manager, Director, Executive. Be specific.",
        "german_language_proficiency": "Estimate based on CV and preferences. Examples: A1, B2, C1, Native, Not Mentioned.",
        "other_languages": [
            {{"language": "English", "proficiency": "e.g., Native, Fluent, C1"}},
            {{"language": "French", "proficiency": "e.g., Basic, B1"}}
        ],
        "preferences": {{
            "desired_roles": ["role type 1", "job title example"],
            "location_preferences": ["city1", "Remote", "Germany-wide"],
            "work_model": ["Remote", "Hybrid", "On-site"],
            "salary_expectations_eur_k_pa": "e.g., 60-70k EUR per annum, Not Mentioned. Extract if specified.",
            "company_culture_preferences": ["e.g., fast-paced, collaborative, work-life balance. Extract if specified."]
        }},
        "education": [
            {{"degree": "e.g., Master of Science", "field": "e.g., Computer Science", "institution": "University Name", "graduation_year": "YYYY (if available)"}}
        ],
        "extracted_cv_highlights": "A few bullet points of key achievements or experiences from the CV."
    }}

    Ensure the output is ONLY the JSON object, starting with '{{' and ending with '}}'.
    Do not include any explanatory text before or after the JSON object.
    If some information is not available, use "Not Mentioned" or an empty array/object as appropriate for the field type.
    """

    api_response_text = None
    try:
        print("--- Sending prompt to Gemini for user profile extraction ---")
        # print(f"DEBUG Profile Prompt:\n{prompt[:1000]}...") # For debugging if needed
        response = model.generate_content(prompt)
        api_response_text = response.text
        # print(f"DEBUG Profile API Response Text:\n{api_response_text}")

        profile_data = parse_gemini_object_json_response(api_response_text)
        return profile_data

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON from Gemini for user profile. Error: {e}. Raw response was: {api_response_text}")
        return simulate_extract_user_profile(user_cv_text, user_preferences_text, error_message=str(e))
    except Exception as e:
        print(f"ERROR: Gemini API call or other processing failed for user profile extraction: {e}")
        # print(f"Traceback for general error: {traceback.format_exc()}") # For deeper debugging
        return simulate_extract_user_profile(user_cv_text, user_preferences_text, error_message=str(e))

def simulate_extract_user_profile(user_cv_text, user_preferences_text, error_message=None):
    """Simulates user profile extraction."""
    print(f"Executing SIMULATED user profile extraction. CV snippet: {user_cv_text[:50]}..., Prefs snippet: {user_preferences_text[:50]}...")
    simulated_profile = {
        "summary": f"Simulated summary based on CV and preferences. {(error_message if error_message else '')}",
        "key_skills": ["Python", "Django", "JavaScript", "Simulated Skill"],
        "experience_level": "Mid-Level (Simulated)",
        "german_language_proficiency": "B1 (Simulated)",
        "other_languages": [
            {"language": "English", "proficiency": "Fluent (Simulated)"}
        ],
        "preferences": {
            "desired_roles": ["Software Developer", "Backend Engineer (Simulated)"],
            "location_preferences": ["Berlin (Simulated)", "Remote"],
            "work_model": "Hybrid (Simulated)",
            "salary_expectations_eur_k_pa": "65-75k EUR per annum (Simulated)",
            "company_culture_preferences": "Collaborative (Simulated)"
        },
        "education": [
            {"degree": "Simulated Degree", "field": "Simulated Field", "institution": "Simulated University", "graduation_year": "2020"}
        ],
        "extracted_cv_highlights": "Simulated highlight 1.\nSimulated highlight 2."
    }
    if error_message:
        simulated_profile["error_during_api_call"] = error_message
    return simulated_profile

# --- Legacy Job Matching (based on simple skills_text) --- START ---
def match_jobs_legacy_by_skills_text(skills_text, job_listings):
    """Legacy: Uses Gemini API or simulation to match jobs based on simple skills text."""
    if settings.USE_AI_SIMULATION or not model:
        if not model and not settings.USE_AI_SIMULATION:
            print("Gemini API not available (model not loaded), falling back to legacy simulated matching.")
        else:
            print("Using legacy simulated matching (USE_AI_SIMULATION is True).")
        return simulate_match_jobs_legacy_by_skills_text(skills_text, job_listings)

    jobs_data_for_prompt = []
    for job in job_listings:
        jobs_data_for_prompt.append({
            "id": str(job.id),
            "title": job.job_title,
            "company": job.company_name,
            "description": job.description[:1500],
            "level": job.level if job.level else "Not specified"
        })
    
    jobs_json_string = json.dumps(jobs_data_for_prompt, indent=2)

    prompt = f"""
    You are a job matching assistant. Based on the provided user skills and a list of jobs, please evaluate each job.
    Each job listing includes an ID, title, company, description, and job level.
    For each job in the list, provide a matching score between 0 and 100, and a brief 1-2 sentence reason for the score, considering all these details.

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
        return simulate_match_jobs_legacy_by_skills_text(skills_text, job_listings)
    except Exception as e:
        print(f"ERROR: Gemini API batch call or other processing failed for match_jobs: {e}")
        return simulate_match_jobs_legacy_by_skills_text(skills_text, job_listings)

    matched_results.sort(key=lambda x: x['score'], reverse=True)
    return matched_results

# Renamed the old simulation function to be a clear fallback
def simulate_match_jobs_legacy_by_skills_text(skills_text, job_listings):
    """Legacy: Simulates job matching when the Gemini API is not available or a batch call fails."""
    print("Executing SIMULATED LEGACY job matching by skills text.")
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
# --- Legacy Job Matching (based on simple skills_text) --- END ---


# --- Enhanced Job Matching (based on Structured User Profile) --- START ---
def match_jobs(structured_user_profile, job_listings):
    """Enhanced: Uses Gemini API or simulation to match jobs based on a structured user profile."""
    if settings.USE_AI_SIMULATION or not model:
        if not model and not settings.USE_AI_SIMULATION:
            print("Gemini API not available (model not loaded), falling back to ENHANCED simulated matching.")
        else:
            print("Using ENHANCED simulated matching (USE_AI_SIMULATION is True).")
        return simulate_match_jobs(structured_user_profile, job_listings)

    # Prepare jobs data for the prompt
    jobs_data_for_prompt = []
    for job in job_listings:
        jobs_data_for_prompt.append({
            "id": str(job.id),
            "title": job.job_title,
            "company": job.company_name,
            "description": job.description[:2000], # Slightly increased description length for better context
            "level": job.level if job.level else "Not specified",
            "location": job.location if job.location else "Not specified",
            "industry": job.industry if job.industry else "Not specified"
        })
    
    jobs_json_string = json.dumps(jobs_data_for_prompt, indent=2)
    user_profile_json_string = json.dumps(structured_user_profile, indent=2)

    prompt = f"""
    You are a highly sophisticated AI job matching expert for the German market.
    You will receive a detailed structured user profile and a list of job listings.
    Your task is to meticulously analyze each job against the user's profile and provide a comprehensive evaluation.

    Structured User Profile:
    ```json
    {user_profile_json_string}
    ```

    Job Listings (JSON Array):
    ```json
    {jobs_json_string}
    ```

    Output Format Requirements:
    Return a single, valid JSON array. Each object in the array MUST correspond to one job from the input list.
    Each job object in your response MUST contain the following keys:
    - "id": The original ID of the job from the input list (string).
    - "match_score": An integer between 0 and 100, representing the overall suitability of the job for the candidate.
                     Consider all aspects of the profile: skills, experience, preferences (role, location, work model, salary if mentioned), language skills (especially German), and education.
    - "match_reason": A concise string (2-3 sentences) explaining the main factors contributing to the score. Highlight key alignments or mismatches.
    - "job_insights": A string providing 2-3 bullet points of specific insights about this job in relation to the candidate. 
                      Example: "* Pro: Strong alignment with preferred 'Backend Engineer' role. * Con: Location 'Munich' differs from preference 'Berlin'. * Neutral: Industry X is not specified in preferences but skills are transferable."
    - "application_tips": A string offering 1-2 bullet points of actionable advice for the candidate if they were to apply for this job. 
                          Example: "* Emphasize your Python and Django experience as listed in key_skills. * Mention your B2 German proficiency as it is valuable in the German market, even if the job is in English."

    Example for a single job object in the output array:
    {{ 
        "id": "some_job_id", 
        "match_score": 85, 
        "match_reason": "Excellent skills match for a backend role. User's preference for remote work aligns well. German B2 is a plus.",
        "job_insights": "* Pro: Role type matches user preference. * Pro: Desired salary range seems achievable. * Con: Company culture preference for 'fast-paced' might not align with this traditionally structured company.",
        "application_tips": "* Highlight your 5 years of experience with microservices. * Tailor your CV summary to mention the specific industry if you have relevant experience, even if not listed as a key skill."
    }}

    Ensure the output is ONLY the JSON array, starting with '[' and ending with ']'. No other text or explanations.
    Thoroughly analyze the German market context: German language proficiency should influence the score and tips. Cultural fit, if inferable, is a bonus.
    Be critical and realistic in your assessment.
    """

    api_response_text = None
    try:
        print("--- Sending ENHANCED batch prompt to Gemini for job matching ---")
        # print(f"DEBUG Enhanced Prompt (first 1000 chars):\n{prompt[:1000]}...") # For debugging
        response = model.generate_content(prompt)
        api_response_text = response.text
        # print(f"DEBUG Enhanced API Response Text:\n{api_response_text[:1000]}...") # For debugging
        
        api_results_array = parse_gemini_batch_json_response(api_response_text) # Existing parser should work if new fields are just added keys
        
        processed_matches = []
        for item in api_results_array:
            job_id_str = str(item.get('id'))
            # Find the original job object to link it
            original_job_obj = next((job for job in job_listings if str(job.id) == job_id_str), None)
            if not original_job_obj:
                print(f"Warning: Job ID {job_id_str} from API response not found in original job listings. Skipping.")
                continue

            processed_matches.append({
                'job': original_job_obj, # Link to the actual JobListing model instance
                'score': int(item.get('match_score', 0)),
                'reason': str(item.get('match_reason', 'N/A')),
                'insights': str(item.get('job_insights', 'N/A')),
                'tips': str(item.get('application_tips', 'N/A'))
            })

        # Sort by score descending
        processed_matches.sort(key=lambda x: x['score'], reverse=True)
        return processed_matches

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON array from Gemini for ENHANCED match_jobs. Error: {e}.")
        print(f"--- BEGIN Non-parsable API Response Text ---")
        print(api_response_text) # Print the full raw response for debugging
        print(f"--- END Non-parsable API Response Text ---")
        return simulate_match_jobs(structured_user_profile, job_listings, error_message=f"JSON parsing error: {e}")
    except Exception as e:
        print(f"ERROR: Gemini API ENHANCED batch call or other processing failed for match_jobs: {e}")
        # import traceback
        # print(traceback.format_exc()) # For deeper debugging
        return simulate_match_jobs(structured_user_profile, job_listings, error_message=str(e))

def simulate_match_jobs(structured_user_profile, job_listings, error_message=None):
    """Enhanced: Simulates job matching with a structured user profile."""
    print(f"Executing SIMULATED ENHANCED job matching. Profile summary: {structured_user_profile.get('summary', '')[:50]}...")
    matched_results = []
    
    for job in job_listings:
        score = random.randint(30, 95)
        reason_fragments = ["Simulated Enhanced Reason:"]
        insights_fragments = ["Simulated Insights:"]
        tips_fragments = ["Simulated Tips:"]

        # Simple logic for simulation based on profile
        if 'Python' in structured_user_profile.get('key_skills', []) and 'python' in job.job_title.lower():
            score = min(100, score + 5)
            reason_fragments.append("Good Python skill alignment.")
            tips_fragments.append("Highlight Python projects.")
        
        if job.location and structured_user_profile.get('preferences', {}).get('location_preferences'):
            if job.location in structured_user_profile['preferences']['location_preferences']:
                score = min(100, score + 3)
                insights_fragments.append(f"Location {job.location} matches preference.")
            else:
                insights_fragments.append(f"Location {job.location} does not match preference {structured_user_profile['preferences']['location_preferences']}.")

        if not reason_fragments or len(reason_fragments) == 1: reason_fragments.append("General simulated match.")
        if not insights_fragments or len(insights_fragments) == 1: insights_fragments.append("Standard insights apply.")
        if not tips_fragments or len(tips_fragments) == 1: tips_fragments.append("Standard application advice.")
        
        if error_message and job == job_listings[0]: # Add error to the first job for visibility
            reason_fragments.append(f"(SimError: {error_message})")

        matched_results.append({
            'job': job,
            'score': score,
            'reason': " ".join(reason_fragments),
            'insights': " ".join(insights_fragments),
            'tips': " ".join(tips_fragments)
        })
    matched_results.sort(key=lambda x: x['score'], reverse=True)
    return matched_results
# --- Enhanced Job Matching (based on Structured User Profile) --- END ---

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
    Job Title: {job.job_title}
    Company: {job.company_name}
    Level: {job.level if job.level else "Not specified"}
    Description: {job.description}
    
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