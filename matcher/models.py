from django.db import models

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
