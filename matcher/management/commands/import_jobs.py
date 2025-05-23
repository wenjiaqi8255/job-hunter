import csv
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.conf import settings
from matcher.models import JobListing
import os

class Command(BaseCommand):
    help = 'Imports job listings from job_listings_rows.csv into the database'

    def handle(self, *args, **options):
        csv_file_path = os.path.join(settings.BASE_DIR, 'job_listings_rows.csv')

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at: {csv_file_path}'))
            self.stdout.write(self.style.WARNING('Please ensure job_listings_rows.csv is in the project root directory.'))
            return

        self.stdout.write(self.style.SUCCESS('Deleting existing job listings...'))
        JobListing.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Existing job listings deleted.'))

        self.stdout.write(self.style.SUCCESS(f'Importing job listings from {csv_file_path}...'))
        
        count = 0
        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Helper to get value or None if key doesn't exist or value is empty string
                    def get_val(key, default=None):
                        val = row.get(key)
                        return val if val and val.strip() != '' else default

                    # Data mapping and cleaning
                    job_id = get_val('id')
                    if not job_id: # ID is mandatory
                        self.stdout.write(self.style.WARNING(f'Skipping row due to missing ID: {row}'))
                        continue

                    # For datetime fields, ensure they are parsed correctly or set to None
                    # Assuming processed_at might be empty or a valid datetime string
                    processed_at_str = get_val('processed_at')
                    processed_at_val = None
                    if processed_at_str:
                        try:
                            processed_at_val = parse_datetime(processed_at_str)
                            if not processed_at_val: # parse_datetime can return None if format is wrong
                                self.stdout.write(self.style.WARNING(f'Could not parse processed_at for job ID {job_id}: {processed_at_str}'))
                        except ValueError:
                             self.stdout.write(self.style.WARNING(f'Invalid date format for processed_at for job ID {job_id}: {processed_at_str}'))
                    
                    # Ensure required fields have a value, or provide a default if model allows (e.g. industry)
                    industry_val = get_val('industry')
                    if not industry_val:
                        # As per model, industry is not nullable, so we must have a value or skip
                        # Or, if there's a sensible default, use it. For now, we skip if missing.
                        # self.stdout.write(self.style.WARNING(f'Skipping job ID {job_id} due to missing industry.'))
                        # continue 
                        # Alternative: Provide a default if appropriate, e.g., 'Unknown'
                        industry_val = 'Unknown' # Or handle as an error / skip

                    JobListing.objects.create(
                        id=job_id,
                        company_name=get_val('company_name', 'N/A'),
                        job_title=get_val('job_title', 'N/A'),
                        description=get_val('description'),
                        application_url=get_val('application_url'),
                        location=get_val('location'),
                        industry=industry_val,
                        flexibility=get_val('flexibility'),
                        salary_range=get_val('salary_range'),
                        level=get_val('level', default='entry level'),
                        reason_for_match=get_val('reason_for_match'), 
                        source=get_val('source'),
                        status=get_val('status'), # This field seems more for user interaction later
                        # created_at is auto_now_add
                        processed_at=processed_at_val
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} job listings.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'ERROR: CSV file not found at {csv_file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred during import: {e}')) 