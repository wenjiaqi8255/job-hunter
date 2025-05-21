from django.db import models
import uuid # Import uuid for UUIDField default

# Create your models here.

class JobListing(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    company_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    application_url = models.URLField(null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    # Assuming 'industry' is a required field based on lack of null=True
    industry = models.CharField(max_length=100) 
    flexibility = models.CharField(max_length=50, null=True, blank=True)
    salary_range = models.CharField(max_length=100, null=True, blank=True)
    # 'reason_for_match' will be populated by Gemini, not from CSV typically
    reason_for_match = models.TextField(null=True, blank=True) 
    source = models.CharField(max_length=50, null=True, blank=True)
    # 'status' seems more related to SavedJob, but including if it's in core listings
    status = models.CharField(max_length=50, null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class MatchSession(models.Model):
    """Stores a specific matching session, including the skills input used."""
    # Using Django's session key if available, or a manually generated one
    # If we want to associate with Django user sessions for logged-in users later, this can be adapted.
    # For anonymous users, request.session.session_key can be used if session is saved.
    # For MVP, a simple unique ID per match run might suffice if we don't need strict user separation yet.
    # Let's use a UUIDField for a unique ID for each matching run.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skills_text = models.TextField()
    matched_at = models.DateTimeField(auto_now_add=True)
    # If using Django sessions directly for anonymous users:
    # session_key = models.CharField(max_length=40, null=True, blank=True, unique=True) 

    def __str__(self):
        return f"Match session on {self.matched_at.strftime('%Y-%m-%d %H:%M')} with skills: {self.skills_text[:50]}..."

class MatchedJob(models.Model):
    """Links a JobListing to a MatchSession with a specific score and reason for that match."""
    match_session = models.ForeignKey(MatchSession, on_delete=models.CASCADE, related_name='matched_jobs')
    job_listing = models.ForeignKey(JobListing, on_delete=models.CASCADE)
    score = models.IntegerField(default=0) # Score from 0-100
    reason = models.TextField(blank=True, null=True) # Reason from Gemini

    class Meta:
        # Ensure a job is only listed once per match session
        unique_together = ('match_session', 'job_listing')
        ordering = ['-score'] # Default ordering by score descending for a given session

    def __str__(self):
        return f"{self.job_listing.job_title} ({self.score}%) for session {self.match_session_id}"
