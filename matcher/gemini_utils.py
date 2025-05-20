import os
import google.generativeai as genai
import json
import random # Keep for fallback/testing if API fails or is not configured

# Configure the Gemini API client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
print(f"DEBUG: GEMINI_API_KEY from env: '{GEMINI_API_KEY}'")
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Using a model that supports function calling or structured output is ideal.
        # 'gemini-1.5-flash-latest' is a good candidate for speed and capability.
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"ERROR: Could not configure Gemini API: {e}. Falling back to simulated matching.")
else:
    print("WARNING: GEMINI_API_KEY environment variable not found. Falling back to simulated matching.")

def parse_gemini_json_response(response_text):
    """Attempts to parse a JSON object from Gemini's text response.
       Handles cases where the JSON might be wrapped in backticks or have leading/trailing text.
    """
    # Find the start and end of the JSON object
    start_index = response_text.find('{')
    end_index = response_text.rfind('}')

    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = response_text[start_index : end_index + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e} in string: '{json_str}'")
            raise # Re-raise the error to be caught by the caller
    else:
        print(f"Could not find valid JSON object in response: {response_text}")
        raise json.JSONDecodeError("No valid JSON object found in response string", response_text, 0)

def match_jobs(skills_text, job_listings):
    """Uses the Gemini API to match jobs based on skills and job descriptions, 
       returning sorted matching results with scores and reasons.
    """
    if not model: # Fallback to simulation if API is not configured or init failed
        print("Gemini API not available. Using simulated matching.")
        return simulate_match_jobs(skills_text, job_listings)

    matched_results = []

    for job in job_listings:
        prompt = f"""
        Analyze the following user skills and job description to determine a match score and provide a reason.
        Format your response as a single, valid JSON object with two keys: "score" (an integer between 0 and 100) and "reason" (a brief string explaining the score).

        User Skills:
        {skills_text}

        Job Title: {job.job_title}
        Company: {job.company_name}
        Job Description:
        {job.description}

        JSON Response:
        """
        
        api_response_text = None # For logging in case of JSON error
        try:
            # print(f"--- Sending prompt to Gemini for job: {job.job_title} ---")
            response = model.generate_content(prompt)
            api_response_text = response.text # Store for potential error logging
            # print(f"--- Gemini Raw Response for {job.job_title}: {api_response_text} ---")
            
            api_result = parse_gemini_json_response(api_response_text)
            score = int(api_result.get('score', 0))
            reason = str(api_result.get('reason', "No reason provided by API."))
            score = max(0, min(100, score)) # Ensure score is within 0-100

            matched_results.append({
                'job': job,
                'score': score,
                'reason': reason
            })

        except json.JSONDecodeError as e:
            # This catches errors from parse_gemini_json_response
            print(f"ERROR: Could not parse JSON response from Gemini for job '{job.job_title}'. Error: {e}. Raw response was: {api_response_text}")
            matched_results.append({
                'job': job,
                'score': random.randint(20, 50), 
                'reason': "Error processing API response (JSON parsing failed)."
            })
        except Exception as e:
            # This catches other errors, like the API call itself failing
            print(f"ERROR: API call or other processing failed for job '{job.job_title}': {e}")
            matched_results.append({
                'job': job,
                'score': random.randint(20, 50),
                'reason': "API call failed for this job or other processing error."
            })

    matched_results.sort(key=lambda x: x['score'], reverse=True)
    return matched_results

# Renamed the old simulation function to be a clear fallback
def simulate_match_jobs(skills_text, job_listings):
    """Simulates job matching when the Gemini API is not available."""
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
    """(Placeholder) Uses the Gemini API to generate a cover letter."""
    if not model: # Check if model was initialized
        print("Gemini API not available for cover letter. Using placeholder.")
        return f"(Simulated Cover Letter) Dear {job.company_name}, I am interested in {job.job_title}. My skills: {skills_text}."

    prompt = f"""
    Based on the following user skills and job details, write a concise and compelling opening paragraph for a cover letter (1-2 sentences maximum).
    
    User Skills: {skills_text}
    Job: {job.job_title} at {job.company_name} - {job.description}
    
    Cover Letter Opening Paragraph:
    """
    try:
        response = model.generate_content(prompt)
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            return f"Could not generate cover letter due to safety settings. Reason: {response.prompt_feedback.block_reason}"
        return response.text.strip()
    except Exception as e:
        print(f"ERROR: Cover letter generation API call failed for job '{job.job_title}': {e}")
        return "(Error generating cover letter via API. Please try again.)" 