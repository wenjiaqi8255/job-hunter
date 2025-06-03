from django.core.management.base import BaseCommand
from matcher.services import pdf_parser

class Command(BaseCommand):
    help = 'Parse a resume PDF and extract key information'

    def add_arguments(self, parser):
        parser.add_argument('pdf_path', type=str, help='Path to the PDF file')

    def handle(self, *args, **kwargs):
        pdf_path = kwargs['pdf_path']
        text = pdf_parser.extract_text_from_pdf(pdf_path)

        self.stdout.write(f"Resume: {pdf_path}")

        name = pdf_parser.extract_name(text)
        self.stdout.write(f"Name: {name or 'Not found'}")

        contact_number = pdf_parser.extract_contact_number_from_resume(text)
        self.stdout.write(f"Contact Number: {contact_number or 'Not found'}")

        email = pdf_parser.extract_email_from_resume(text)
        self.stdout.write(f"Email: {email or 'Not found'}")

        skills_list = ['Python', 'Data Analysis', 'Machine Learning', 'Communication', 'Project Management', 'Deep Learning', 'SQL', 'Tableau']
        skills = pdf_parser.extract_skills_from_resume(text, skills_list)
        self.stdout.write(f"Skills: {', '.join(skills) if skills else 'Not found'}")

        education = pdf_parser.extract_education_from_resume(text)
        self.stdout.write(f"Education: {', '.join(education) if education else 'Not found'}")
