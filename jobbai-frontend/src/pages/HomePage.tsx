import MainPageLayout from '../components/MainPageLayout';
import ProfilePreview from '../components/ProfilePreview';
import JobList from '../components/JobList';
import { useSessionStore } from '../stores/sessionStore';
import { useAuthStore } from '../stores/authStore';
import { useI18n } from '../hooks/useI18n';
import { Link } from 'react-router-dom';

function GuestWelcomeCard() {
  const { t } = useI18n();
  return (
    <div className="bg-white rounded-xl p-6 border border-border text-center">
      <h2 className="text-xl font-bold text-textPrimary mb-2">{t('welcome_guest')}</h2>
      <p className="text-base text-textSecondary mb-6">
        {t('guest_prompt_long')}
      </p>
      <Link to="/login">
        <button className="bg-primary text-textPrimary rounded-xl px-6 py-3 text-base font-bold w-auto">
          {t('login_to_get_matches')}
        </button>
      </Link>
    </div>
  );
}

function HomePage() {
  const { isAuthenticated } = useAuthStore();
  const { selectedSessionId } = useSessionStore();
  const { t } = useI18n();

  return (
    <MainPageLayout>
      {!isAuthenticated ? (
        <GuestWelcomeCard />
      ) : (
        <>
          <ProfilePreview />
          <div className="mt-6">
             <h2 className="text-lg font-bold text-textPrimary mb-4">{t('match_results')}</h2>
             <JobList showMatchResults={true} sessionId={selectedSessionId} />
          </div>
        </>
      )}
    </MainPageLayout>
  );
}

export default HomePage;
