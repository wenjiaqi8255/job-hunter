from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
import random
from django.conf import settings # Import Django settings

# Configure the Gemini API client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
            print("INFO: Gemini API configured successfully for job matching.")
        except Exception as e:
            print(f"ERROR: Could not configure Gemini API: {e}. AI features will be effectively simulated.")
            model = None # Ensure model is None if config fails
    else:
        print("WARNING: GEMINI_API_KEY environment variable not found. AI features will be effectively simulated.")
        model = None # Ensure model is None if key is not found
else:
    print("INFO: USE_AI_SIMULATION is True. AI calls will be simulated.")
    model = None # Ensure model is None when simulating

# --- Reusable Helper Functions ---

def _get_processed_job_listings(job_listings, max_jobs_to_process, task_name_for_log="task"):
    """
    Slices the job_listings based on max_jobs_to_process.
    Returns the processed list.
    """
    if max_jobs_to_process is not None and isinstance(max_jobs_to_process, int) and max_jobs_to_process > 0:
        print(f"INFO: Processing only the top {max_jobs_to_process} job listings for {task_name_for_log}.")
        return job_listings[:max_jobs_to_process]
    elif max_jobs_to_process is not None:
        print(f"WARNING: Invalid value for max_jobs_to_process ({max_jobs_to_process}) for {task_name_for_log}. Processing all jobs.")
    return job_listings

def _prepare_job_data_for_prompt(processed_job_listings):
    """Prepares the job data in the format expected by the API prompt."""
    return [
        {
            "id": str(job.get('id')),
            "title": job.get('job_title'),
            "company": job.get('company_name'),
            "description": job.get('description', ''),
            "level": job.get('level', "Not specified"),
            "location": job.get('location', "Not specified"),
            "industry": job.get('industry', "Not specified")
        }
        for job in processed_job_listings
    ]

def _execute_ai_task(
    task_name,
    prompt_generator_func,
    prompt_generator_args: tuple,
    response_parser_func,
    response_parser_args: tuple, # Additional args for the parser besides api_response_text and api_response_object
    simulation_func,
    simulation_args: tuple,
    pass_full_response_to_parser: bool = False
):
    """
    Core function to execute an AI task: either call Gemini API or run a simulation.
    Handles prompt generation, API call, response parsing, and error fallback.
    """
    if settings.USE_AI_SIMULATION or not model:
        sim_reason = "USE_AI_SIMULATION is True" if settings.USE_AI_SIMULATION else "Gemini model not available"
        print(f"INFO: Using simulated {task_name} ({sim_reason}).")
        # Ensure error_message is passed if it's an expected arg for the simulation_func
        # For simplicity, we assume simulation_func can take an error_message as its last arg if needed.
        # This might need adjustment based on specific simulation function signatures.
        # Here, we rely on simulation_args to be structured correctly by the caller.
        return simulation_func(*simulation_args)

    api_response_text = None
    api_response_object = None
    try:
        prompt = prompt_generator_func(*prompt_generator_args)
        print(f"INFO: --- Sending prompt to Gemini for {task_name} ---")
        # print(f"DEBUG Prompt for {task_name} (first 500 chars):\n{prompt[:500]}...")
        
        api_response_object = model.generate_content(prompt)
        api_response_text = api_response_object.text
        # print(f"DEBUG API Response Text for {task_name} (first 500 chars):\n{api_response_text[:500]}...")

        # Pass (api_response_text, api_response_object, ...) to parser
        parser_all_args = (api_response_text, api_response_object) + response_parser_args

        return response_parser_func(*parser_all_args)

    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON from Gemini for {task_name}. Error: {e}. Raw response was: {api_response_text}")
        # Fallback to simulation with error information
        # Ensure the simulation_func can accept an error_message.
        # Typically, simulation_args would already contain placeholders or default values for primary inputs.
        # We append error_message, assuming it's the last parameter in simulation_func's signature if it handles errors.
        error_sim_args = simulation_args + (f"API JSON parsing error: {e}",)
        return simulation_func(*error_sim_args)
    except Exception as e:
        print(f"ERROR: Gemini API call or other processing failed for {task_name}: {e}")
        # import traceback
        # print(traceback.format_exc()) # For deeper debugging
        error_sim_args = simulation_args + (f"API call/processing error: {e}",)
        return simulation_func(*error_sim_args)

# --- JSON Parsing Utilities (kept as is, but could be integrated if only used once) ---
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

# --- User Profile Extraction ---

def _generate_user_profile_prompt(user_cv_text, user_preferences_text):
    return f"""
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

def _parse_user_profile_response(api_response_text, _api_response_object=None): # Add _api_response_object for consistent signature
    return parse_gemini_object_json_response(api_response_text)

def simulate_extract_user_profile(user_cv_text, user_preferences_text, error_message=None):
    """Simulates user profile extraction."""
    print(f"INFO: Executing SIMULATED user profile extraction. CV snippet: {user_cv_text[:50]}..., Prefs snippet: {user_preferences_text[:50]}...")
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

def extract_user_profile(user_cv_text, user_preferences_text):
    """
    Uses Gemini API or simulation to extract a structured user profile 
    from CV text and user preferences.
    """
    return _execute_ai_task(
        task_name="user profile extraction",
        prompt_generator_func=_generate_user_profile_prompt,
        prompt_generator_args=(user_cv_text, user_preferences_text),
        response_parser_func=_parse_user_profile_response,
        response_parser_args=(), # No extra args for this parser
        simulation_func=simulate_extract_user_profile,
        simulation_args=(user_cv_text, user_preferences_text),
        pass_full_response_to_parser=False # Not strictly needed for this one
    )

# --- Legacy Job Matching (based on simple skills_text) --- REMOVED ---

# --- Enhanced Job Matching (based on Structured User Profile) --- START ---

def _generate_match_jobs_prompt(structured_user_profile, jobs_json_string):
    user_profile_json_string = json.dumps(structured_user_profile, indent=2)
    return f"""
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

def _parse_match_jobs_response(api_response_text, _api_response_object, original_processed_job_listings):
    api_results_array = parse_gemini_batch_json_response(api_response_text)
    
    processed_matches = []
    for item in api_results_array:
        job_id_str = str(item.get('id'))
        original_job_dict = next((job for job in original_processed_job_listings if str(job.get('id')) == job_id_str), None)
        
        if not original_job_dict:
            print(f"WARNING: Job ID {job_id_str} from API response not found in the processed job listings. Skipping.")
            continue

        processed_matches.append({
            'job': original_job_dict,
            'score': int(item.get('match_score', 0)),
            'reason': str(item.get('match_reason', 'N/A')),
            'insights': str(item.get('job_insights', 'N/A')),
            'tips': str(item.get('application_tips', 'N/A'))
        })

    processed_matches.sort(key=lambda x: x['score'], reverse=True)
    return processed_matches

def simulate_match_jobs(structured_user_profile, job_listings, max_jobs_to_process=None, error_message=None):
    """Enhanced: Simulates job matching with a structured user profile."""
    print(f"INFO: Executing SIMULATED ENHANCED job matching. Profile summary: {structured_user_profile.get('summary', '')[:50]}...")
    
    # Use the helper for consistent job list processing
    processed_job_listings = _get_processed_job_listings(job_listings, max_jobs_to_process, "enhanced simulation")
        
    matched_results = []
    
    for i, job in enumerate(processed_job_listings): # Use the (potentially sliced) list
        score = random.randint(30, 95)
        reason_fragments = ["Simulated Enhanced Reason:"]
        insights_fragments = ["Simulated Insights:"]
        tips_fragments = ["Simulated Tips:"]

        # Simple logic for simulation based on profile
        if 'Python' in structured_user_profile.get('key_skills', []) and 'python' in job.get('job_title', '').lower():
            score = min(100, score + 5)
            reason_fragments.append("Good Python skill alignment.")
            tips_fragments.append("Highlight Python projects.")
        
        job_location = job.get('location')
        if job_location and structured_user_profile.get('preferences', {}).get('location_preferences'):
            if job_location in structured_user_profile['preferences']['location_preferences']:
                score = min(100, score + 3)
                insights_fragments.append(f"Location {job_location} matches preference.")
            else:
                insights_fragments.append(f"Location {job_location} does not match preference {structured_user_profile['preferences']['location_preferences']}.")

        if not reason_fragments or len(reason_fragments) == 1: reason_fragments.append("General simulated match.")
        if not insights_fragments or len(insights_fragments) == 1: insights_fragments.append("Standard insights apply.")
        if not tips_fragments or len(tips_fragments) == 1: tips_fragments.append("Standard application advice.")
        
        if error_message and job == processed_job_listings[0] if processed_job_listings else False: 
            reason_fragments.append(f"(SimError: {error_message})")

        # Enhanced job object with simulated anomaly analysis
        enhanced_job = job.copy()
        
        # Add simulated anomaly analysis to some jobs (not all, to be realistic)
        if i < 2:  # Only add to first 2 jobs for variety
            enhanced_job['anomaly_analysis'] = {
                "role": structured_user_profile.get('preferences', {}).get('desired_roles', ['unknown'])[0] if structured_user_profile.get('preferences', {}).get('desired_roles') else 'unknown',
                "job_id": str(job.get('id', '')),
                "industry": job.get('industry', 'unknown'),
                "job_title": job.get('job_title', ''),
                "company_name": job.get('company_name', ''),
                "semantic_anomalies": [
                    {
                        "type": "Cross-Role",
                        "chunk": f"Simulated anomaly chunk for {job.get('job_title', 'this role')} - potential role mismatch detected.",
                        "similarity_to_role": round(random.uniform(0.2, 0.4), 3),
                        "similarity_to_global": round(random.uniform(0.3, 0.5), 3),
                        "similarity_to_industry": round(random.uniform(0.2, 0.4), 3)
                    },
                    {
                        "type": "Industry-Specific",
                        "chunk": f"Industry-specific anomaly for {job.get('industry', 'this industry')} - unusual requirements detected.",
                        "similarity_to_role": round(random.uniform(0.3, 0.5), 3),
                        "similarity_to_global": round(random.uniform(0.4, 0.6), 3),
                        "similarity_to_industry": round(random.uniform(0.2, 0.3), 3)
                    }
                ] if random.choice([True, False]) else [],  # Sometimes no anomalies
                "effective_description": f"Simulated effective description for {job.get('job_title', 'this position')} at {job.get('company_name', 'this company')}. This is a comprehensive role description with all relevant details."
            }

        matched_results.append({
            'job': enhanced_job,
            'score': score,
            'reason': " ".join(reason_fragments),
            'insights': " ".join(insights_fragments),
            'tips': " ".join(tips_fragments)
        })
    matched_results.sort(key=lambda x: x['score'], reverse=True)
    return matched_results

def match_jobs(structured_user_profile, job_listings, max_jobs_to_process=None):
    """Enhanced: Uses Gemini API or simulation to match jobs based on a structured user profile."""
    print(f"INFO: [match_jobs] Top of function. settings.USE_AI_SIMULATION: {settings.USE_AI_SIMULATION}, Model: {model is not None}")

    # Get the (potentially sliced) list of jobs to process
    processed_job_listings = _get_processed_job_listings(job_listings, max_jobs_to_process, "enhanced job matching")
    
    if not processed_job_listings: # If no jobs to process, return empty list
        print("INFO: [match_jobs] No job listings to process after applying max_jobs_to_process filter.")
        return []

    # Prepare job data specifically for the prompt
    jobs_data_for_prompt = _prepare_job_data_for_prompt(processed_job_listings)
    jobs_json_string = json.dumps(jobs_data_for_prompt, indent=2)

    return _execute_ai_task(
        task_name="enhanced job matching",
        prompt_generator_func=_generate_match_jobs_prompt,
        prompt_generator_args=(structured_user_profile, jobs_json_string),
        response_parser_func=_parse_match_jobs_response,
        response_parser_args=(processed_job_listings,), # Pass the original (but potentially sliced) job dicts for reconstruction
        simulation_func=simulate_match_jobs,
        simulation_args=(structured_user_profile, job_listings, max_jobs_to_process), # Simulation will internally call _get_processed_job_listings
        pass_full_response_to_parser=False # Parser doesn't need the full response object for this one
    )
# --- Enhanced Job Matching (based on Structured User Profile) --- END ---

# --- Cover Letter Generation ---

def _generate_cover_letter_prompt(skills_text, job):
    return f"""
    Based on the following user skills and job details, write a concise and compelling opening paragraph for a cover letter (1-2 sentences maximum).
    
    User Skills: {skills_text}
    Job Title: {job.get('job_title')}
    Company: {job.get('company_name')}
    Level: {job.get('level', "Not specified")}
    Description: {job.get('description')}
    
    Cover Letter Opening Paragraph:
    """

def _parse_cover_letter_response(api_response_text, api_response_object):
    if api_response_object and api_response_object.prompt_feedback and api_response_object.prompt_feedback.block_reason:
        print(f"WARNING: Cover letter generation might have been blocked. Reason: {api_response_object.prompt_feedback.block_reason}")
        return f"(Could not generate cover letter due to safety settings. Reason: {api_response_object.prompt_feedback.block_reason})"
    return api_response_text.strip()

def simulate_generate_cover_letter(skills_text, job, error_message=None):
    """Simulates cover letter generation."""
    print(f"INFO: Executing SIMULATED cover letter generation for job: {job['job_title']}")
    sim_text = f"(Simulated Cover Letter for {job['job_title']} at {job['company_name']}) Based on your skills in {skills_text[:50]}..., this job seems like a good fit because... (simulated reason)."
    if error_message:
        sim_text += f" (SimError: {error_message})"
    return sim_text

def generate_cover_letter(skills_text, job):
    """Uses Gemini API or simulation to generate a cover letter opening."""
    return _execute_ai_task(
        task_name="cover letter generation",
        prompt_generator_func=_generate_cover_letter_prompt,
        prompt_generator_args=(skills_text, job),
        response_parser_func=_parse_cover_letter_response,
        response_parser_args=(),
        simulation_func=simulate_generate_cover_letter,
        simulation_args=(skills_text, job),
        pass_full_response_to_parser=True # Parser needs the full response for feedback checks
    )

# --- Resume Customization ---

def _generate_custom_resume_prompt(user_cv_text, job):
    return f"""
    You are an expert career consultant and resume writer. Your task is to optimize the user's resume for a specific job, keeping the original structure and formatting as much as possible, but improving the content expression, clarity, and relevance for the target job.

    User Resume (Original):
    ---
    {user_cv_text}
    ---

    Target Job Details:
    ---
    Job Title: {job.get('job_title')}
    Company: {job.get('company_name')}
    Level: {job.get('level', 'Not specified')}
    Description: {job.get('description')}
    ---

    Instructions:
    - Analyze the user's resume and the job description.
    - Identify the structure (sections, headings, bullet points, etc.) of the original resume.
    - Rewrite and optimize the content of each section to better match the target job, using more impactful and relevant language, but do NOT invent experience or skills not present in the original.
    - Keep the formatting and structure (sections, order, bullet points, etc.) as close as possible to the original.
    - Only improve the expression, clarity, and relevance for the target job.
    - Output ONLY the improved resume text, with no extra explanation or commentary.
    """

def _parse_custom_resume_response(api_response_text, api_response_object=None):
    return api_response_text.strip()

def simulate_generate_custom_resume(user_cv_text, job, error_message=None):
    print(f"INFO: Executing SIMULATED custom resume generation for job: {job.get('job_title')}")
    sim_text = f"(Simulated Custom Resume for {job.get('job_title')} at {job.get('company_name')})\n" + user_cv_text[:500] + "...\n[Resume optimized for target job. Simulated output.]"
    if error_message:
        sim_text += f" (SimError: {error_message})"
    return sim_text

def generate_custom_resume(user_cv_text, job):
    return _execute_ai_task(
        task_name="custom resume generation",
        prompt_generator_func=_generate_custom_resume_prompt,
        prompt_generator_args=(user_cv_text, job),
        response_parser_func=_parse_custom_resume_response,
        response_parser_args=(),
        simulation_func=simulate_generate_custom_resume,
        simulation_args=(user_cv_text, job),
        pass_full_response_to_parser=False
    ) 