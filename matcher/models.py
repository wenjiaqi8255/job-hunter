from django.db import models
import uuid # Import uuid for UUIDField default
import json # For storing structured profile as JSON
import os

# Create your models here.

def user_cv_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_cvs/<session_key>/<filename>
    return f'user_cvs/{instance.session_key}/{filename}'

class UserProfile(models.Model):
    session_key = models.CharField(max_length=40, primary_key=True, editable=False)
    user_cv_text = models.TextField(blank=True, null=True)
    cv_file = models.FileField(upload_to=user_cv_path, blank=True, null=True)
    user_preferences_text = models.TextField(blank=True, null=True)
    user_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for session {self.session_key}"

class JobListing(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    company_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    translated_description = models.TextField(null=True, blank=True)
    application_url = models.URLField(null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    industry = models.CharField(max_length=100) 
    flexibility = models.CharField(max_length=50, null=True, blank=True)
    salary_range = models.CharField(max_length=100, null=True, blank=True)
    level = models.CharField(max_length=100, null=True, blank=True)
    reason_for_match = models.TextField(null=True, blank=True) 
    source = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class MatchSession(models.Model):
    """Stores a specific matching session, including the skills input used."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skills_text = models.TextField()
    user_preferences_text = models.TextField(null=True, blank=True)
    structured_user_profile_json = models.JSONField(null=True, blank=True)
    matched_at = models.DateTimeField(auto_now_add=True)
    # session_key = models.CharField(max_length=40, null=True, blank=True, unique=True) 

    def __str__(self):
        preferences_snippet = self.user_preferences_text[:30] + "..." if self.user_preferences_text else "No preferences"
        return f"Match on {self.matched_at.strftime('%Y-%m-%d %H:%M')} | CV: {self.skills_text[:30]}... | Prefs: {preferences_snippet}"

    def get_structured_profile(self):
        if self.structured_user_profile_json:
            if isinstance(self.structured_user_profile_json, str):
                try:
                    return json.loads(self.structured_user_profile_json)
                except (json.JSONDecodeError, TypeError):
                    return None
            return self.structured_user_profile_json
        return None

class MatchedJob(models.Model):
    """Links a JobListing to a MatchSession with a specific score and reason for that match."""
    match_session = models.ForeignKey(MatchSession, on_delete=models.CASCADE, related_name='matched_jobs')
    job_listing = models.ForeignKey(JobListing, on_delete=models.CASCADE)
    score = models.IntegerField(default=0) # Score from 0-100
    reason = models.TextField(blank=True, null=True) # Reason from Gemini
    insights = models.TextField(blank=True, null=True) # New field for 'job_insights'
    tips = models.TextField(blank=True, null=True) # New field for 'application_tips'

    class Meta:
        # Ensure a job is only listed once per match session
        unique_together = ('match_session', 'job_listing')
        ordering = ['-score'] # Default ordering by score descending for a given session

    def __str__(self):
        return f"{self.job_listing.job_title} ({self.score}%) for session {self.match_session_id}"

class SavedJob(models.Model):
    STATUS_CHOICES = [
        ('not_applied', 'Not Applied'),
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offer_received', 'Offer Received'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ]

    job_listing = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='saved_instances')
    user_session_key = models.CharField(max_length=40, db_index=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_applied')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job_listing', 'user_session_key')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.job_listing.job_title} - {self.get_status_display()} for session {self.user_session_key}"

class CoverLetter(models.Model):
    saved_job = models.OneToOneField(SavedJob, on_delete=models.CASCADE, related_name='cover_letter') # Assuming one cover letter per saved job for simplicity
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Good to have to see when it was last modified if ever editable

    def __str__(self):
        return f"Cover Letter for {self.saved_job.job_listing.job_title} (SavedJob ID: {self.saved_job.id})"

class Experience(models.Model):
    # This is a placeholder model. The actual data is in Supabase.
    # This model helps avoid migration errors if other parts of the app
    # have temporary foreign key relationships or content type dependencies.
    # The fields can be defined based on the Supabase schema if direct
    # Django integration is ever needed.
    class Meta:
        # By setting managed to False, Django's migrate command will not
        # create, modify, or delete the database table for this model.
        # This is ideal when the table is managed by an external service like Supabase.
        managed = False

class CustomResume(models.Model):
    user_session_key = models.CharField(max_length=40, db_index=True)
    job_listing = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='custom_resumes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_session_key', 'job_listing')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Custom Resume for {self.job_listing.job_title} (Session: {self.user_session_key})"

class JobAnomalyAnalysis(models.Model):
    job_listing = models.OneToOneField(
        JobListing,
        on_delete=models.DO_NOTHING,
        primary_key=True,
        db_column='job_id',
        related_name='anomaly_analysis'
    )
    analysis_data = models.JSONField()

    class Meta:
        managed = False
        db_table = 'job_anomaly_analysis'

    def __str__(self):
        return f"Anomaly Analysis for {self.job_listing.job_title}"
