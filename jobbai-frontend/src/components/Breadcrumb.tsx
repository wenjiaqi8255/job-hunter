import { Link } from 'react-router-dom'

interface BreadcrumbItem {
  label: string
  href?: string
  active?: boolean
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="breadcrumb" className="mb-6">
      <ol className="flex items-center space-x-2 text-sm">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <i className="fas fa-chevron-right text-gray-400 mx-2"></i>
            )}
            
            {item.active ? (
              <span className="text-gray-600 font-medium">
                {item.label}
              </span>
            ) : (
              <Link
                to={item.href || '#'}
                className="text-blue-600 hover:text-blue-800 hover:underline"
              >
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

export default Breadcrumb
