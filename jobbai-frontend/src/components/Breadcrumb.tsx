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
    <nav aria-label="breadcrumb" className="mb-4">
      <ol className="flex items-center space-x-2 text-sm text-textSecondary">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <span className="mx-2">/</span>
            )}
            
            {item.active ? (
              <span className="font-medium text-textPrimary">
                {item.label}
              </span>
            ) : (
              <Link
                to={item.href || '#'}
                className="text-textSecondary hover:text-textPrimary hover:underline"
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
