from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from .models import UserProfile, JobListing, MatchSession, MatchedJob, SavedJob, CustomResume, CoverLetter

User = get_user_model()

class MatcherViewsTestCase(TestCase):
    def setUp(self):
        """Set up test data for the tests."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123', email='test@example.com')
        self.user_profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'user_cv_text': 'My skills are Python and Django.'}
        )
        self.job1 = JobListing.objects.create(
            id='job1',
            company_name='TestCorp',
            job_title='Python Developer',
            description='A job for a Python dev.'
        )
        self.job2 = JobListing.objects.create(
            id='job2',
            company_name='AnotherCorp',
            job_title='Frontend Developer',
            description='A job for a frontend dev.'
        )

    def test_main_page_unauthenticated(self):
        """Test that an unauthenticated user is redirected to the login page."""
        response = self.client.get(reverse('matcher:main_page'))
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('matcher:main_page')}")

    @patch('matcher.views.list_supabase_saved_jobs', return_value=[])
    def test_main_page_authenticated_get(self, mock_list_saved_jobs):
        """Test that an authenticated user can access the main page."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('matcher:main_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'matcher/main_page.html')
        self.assertIn('user_cv_text', response.context)
        mock_list_saved_jobs.assert_called_once_with('testuser')

    def test_profile_page_get(self):
        """Test that an authenticated user can access their profile page."""
        self.client.login(username='testuser', password='password123')
        with patch('matcher.views.get_user_experiences', return_value=[]) as mock_get_exp:
            response = self.client.get(reverse('matcher:profile_page'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'matcher/profile_page.html')
            mock_get_exp.assert_called_once_with(self.user)

    def test_profile_page_post_update_cv(self):
        """Test updating the user's CV text via POST request."""
        self.client.login(username='testuser', password='password123')
        new_cv = "I am an expert in FastAPI."
        with patch('matcher.views.get_user_experiences', return_value=[]):
            response = self.client.post(reverse('matcher:profile_page'), {
                'form_type': 'cv_form',
                'user_cv_text': new_cv
            })
            self.assertEqual(response.status_code, 302) # Redirects after successful post
            self.user_profile.refresh_from_db()
            self.assertEqual(self.user_profile.user_cv_text, new_cv)

    @patch('matcher.views.get_supabase_saved_job', return_value=None)
    @patch('matcher.views.fetch_anomaly_analysis_for_jobs_from_supabase', return_value={})
    def test_job_detail_page_get(self, mock_fetch_anomaly, mock_get_saved):
        """Test that the job detail page loads correctly."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('matcher:job_detail_page_no_session', args=[self.job1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'matcher/job_detail.html')
        self.assertEqual(response.context['job'], self.job1)
        mock_get_saved.assert_called_once_with('testuser', self.job1.id)
        mock_fetch_anomaly.assert_called_once_with([self.job1.id])

    @patch('matcher.views.create_supabase_saved_job')
    @patch('matcher.views.get_supabase_saved_job', return_value=None)
    @patch('matcher.views.fetch_anomaly_analysis_for_jobs_from_supabase', return_value={})
    def test_job_detail_page_post_save_job(self, mock_fetch_anomaly, mock_get_saved, mock_create_saved):
        """Test saving a job from the detail page."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('matcher:job_detail_page_no_session', args=[self.job1.id]), {
            'status': 'applied',
            'notes': 'Test note.'
        })
        self.assertEqual(response.status_code, 302)
        mock_create_saved.assert_called_once()
        # Check that a local mirror is created
        self.assertTrue(SavedJob.objects.filter(user=self.user, job_listing=self.job1).exists())

    @patch('matcher.views.gemini_utils.generate_cover_letter', return_value="Generated Cover Letter")
    @patch('matcher.views.get_supabase_saved_job', return_value=None)
    @patch('matcher.views.create_supabase_saved_job', return_value=None)
    def test_generate_cover_letter_page_get(self, mock_create_supa, mock_get_supa, mock_generate_cl):
        """Test that the cover letter page generates a letter on GET if none exists."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('matcher:generate_cover_letter_page', args=[self.job1.id]))
        self.assertEqual(response.status_code, 200)
        mock_generate_cl.assert_called_once()
        self.assertTrue(CoverLetter.objects.filter(saved_job__job_listing=self.job1, saved_job__user=self.user).exists())
        self.assertIn('Generated Cover Letter', response.context['cover_letter_content'])

    @patch('matcher.views.gemini_utils.generate_custom_resume', return_value="Generated Custom Resume")
    @patch('matcher.views.get_supabase_saved_job', return_value=None)
    @patch('matcher.views.create_supabase_saved_job', return_value=None)
    def test_generate_custom_resume_page_post(self, mock_create_supa, mock_get_supa, mock_generate_resume):
        """Test generating a custom resume via POST."""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('matcher:generate_custom_resume_page', args=[self.job1.id]))
        self.assertEqual(response.status_code, 200)
        mock_generate_resume.assert_called_once()
        self.assertTrue(CustomResume.objects.filter(job_listing=self.job1, user=self.user).exists())
        self.assertIn('Generated Custom Resume', response.context['custom_resume_content'])
