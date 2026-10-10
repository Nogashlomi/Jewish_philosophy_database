import { useState } from 'react'
import { Menu, X } from 'lucide-react'
import { Outlet, Link, useLocation } from 'react-router-dom'

export default function Layout() {
  const location = useLocation()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const isActive = (path: string) => {
    return location.pathname === path
  }

  const mobileLinks = [
    { to: '/', label: 'Home' },
    { to: '/persons', label: 'Persons' },
    { to: '/works', label: 'Works' },
    { to: '/subjects', label: 'Subjects' },
    { to: '/languages', label: 'Languages' },
    { to: '/sources', label: 'Data Sources / Projects / Collaborators' },
    { to: '/map', label: 'Map' },
    { to: '/network', label: 'Network' },
    { to: '/ontology', label: 'Ontology' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col items-center space-y-4">
            <div className="w-full flex justify-center">
              <span className="text-xl font-bold text-gray-900 tracking-tight font-serif text-center">
                Philosophy in Jewish History: Research Explorer
              </span>
            </div>
            <div className="hidden w-full justify-center sm:flex">
              <div className="hidden sm:flex sm:space-x-4">
                <Link
                  to="/"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Home
                </Link>
                <Link
                  to="/persons"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/persons') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Persons
                </Link>
                <Link
                  to="/works"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/works') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Works
                </Link>

                <Link
                  to="/subjects"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/subjects') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Subjects
                </Link>
                <Link
                  to="/languages"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/languages') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Languages
                </Link>

                <Link
                  to="/sources"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive('/sources')
                      ? 'border-indigo-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  }`}
                >
                  Data Sources / Projects / Collaborators
                </Link>
                <Link
                  to="/map"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/map') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Map
                </Link>
                <Link
                  to="/network"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/network') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Network
                </Link>
                <Link
                  to="/ontology"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/ontology') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}
                >
                  Ontology
                </Link>
              </div>
            </div>
            <div className="w-full sm:hidden">
              <button
                type="button"
                className="flex w-full items-center justify-center gap-2 rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                onClick={() => setMobileNavOpen((isOpen) => !isOpen)}
                aria-expanded={mobileNavOpen}
                aria-controls="mobile-navigation"
              >
                {mobileNavOpen ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
                {mobileNavOpen ? 'Close navigation' : 'Navigate'}
              </button>
              {mobileNavOpen && (
                <nav id="mobile-navigation" aria-label="Mobile navigation" className="mt-2 rounded-md border border-gray-200 bg-white p-2 shadow-sm">
                  {mobileLinks.map(({ to, label }) => (
                    <Link
                      key={to}
                      to={to}
                      onClick={() => setMobileNavOpen(false)}
                      className={`block rounded px-3 py-2 text-sm font-medium ${isActive(to) ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-50'}`}
                    >
                      {label}
                    </Link>
                  ))}
                </nav>
              )}
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
