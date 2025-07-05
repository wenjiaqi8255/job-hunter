import { useI18n } from '../hooks/useI18n'

function Footer() {
  const { t } = useI18n()
  
  return (
    <footer className="bg-gray-100 py-4 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center text-gray-600">
          <span className="text-sm">
            {t('footer_text')}
          </span>
        </div>
      </div>
    </footer>
  )
}

export default Footer
