import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useI18n } from '../hooks/useI18n'
import Logo from '../assets/logo.svg'

interface NavbarProps {
  className?: string
}

function Navbar({ className = '' }: NavbarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const { user, isAuthenticated, signOut } = useAuthStore()
  const { t, currentLanguage, setLanguage, languages } = useI18n()
  const location = useLocation()

  const handleSignOut = async () => {
    await signOut()
  }

  const handleLanguageChange = (newLanguage: string) => {
    setLanguage(newLanguage)
  }

  const isActive = (path: string) => {
    return location.pathname === path
  }

  return (
    <nav className={`bg-white shadow-sm fixed top-0 left-0 right-0 z-50 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <img src={Logo} alt="JobbAI Logo" className="h-6" />
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:justify-between flex-grow">
            <div className="flex items-center space-x-8 ml-8">
              <Link to="/" className={`text-sm font-medium ${isActive('/') ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
                {t('home')}
              </Link>
              <Link to="/applications" className={`text-sm font-medium ${isActive('/applications') ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
                {t('applications')}
              </Link>
              <Link to="/profile" className={`text-sm font-medium ${isActive('/profile') ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
                {t('profile')}
              </Link>
            </div>

            {/* User Menu and Actions */}
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-gray-700">
                    {user?.user_metadata?.name || user?.email}
                  </span>
                  <button
                    onClick={handleSignOut}
                    className="text-sm text-gray-700 hover:text-blue-600 font-medium"
                  >
                    {t('logout')}
                  </button>
                </div>
              ) : (
                <Link
                  to="/login"
                  className="text-sm text-gray-700 hover:text-blue-600 font-medium"
                >
                  {t('login')}
                </Link>
              )}

              {/* Language Selector */}
              <div className="relative">
                <select
                  value={currentLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  className="text-sm border border-gray-300 rounded-md px-3 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-blue-600 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            >
              <span className="sr-only">Open main menu</span>
              {isMenuOpen ? (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t border-border">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link to="/" className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/') ? 'bg-background text-primary' : 'text-textSecondary hover:bg-background'}`}>
              {t('home')}
            </Link>
            <Link to="/applications" className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/applications') ? 'bg-background text-primary' : 'text-textSecondary hover:bg-background'}`}>
              {t('applications')}
            </Link>
            <Link to="/profile" className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/profile') ? 'bg-background text-primary' : 'text-textSecondary hover:bg-background'}`}>
              {t('profile')}
            </Link>
          </div>
          <div className="pt-4 pb-3 border-t border-border">
            <div className="px-2 space-y-1">
              {isAuthenticated ? (
                <button
                  onClick={handleSignOut}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-textSecondary hover:bg-background"
                >
                  {t('logout')}
                </button>
              ) : (
                <Link
                  to="/login"
                  className="block px-3 py-2 rounded-md text-base font-medium text-textSecondary hover:bg-background"
                >
                  {t('login')}
                </Link>
              )}
              <div className="px-3 py-2">
                <select
                  value={currentLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  className="w-full text-sm border border-border rounded-md px-3 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.code.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}

export default Navbar
