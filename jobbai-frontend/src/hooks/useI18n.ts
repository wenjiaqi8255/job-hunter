import { useEffect, useState } from 'react'
import { i18n } from '../utils/i18n'

export function useI18n() {
  const [, setUpdate] = useState(0)

  useEffect(() => {
    i18n.init()
    
    const forceUpdate = () => setUpdate(prev => prev + 1)
    i18n.addListener(forceUpdate)
    
    return () => i18n.removeListener(forceUpdate)
  }, [])

  return {
    t: (key: string) => i18n.t(key),
    currentLanguage: i18n.getCurrentLanguage(),
    setLanguage: (lang: string) => i18n.setLanguage(lang),
    languages: i18n.getLanguages(),
  }
}
