import { Outlet, Link, useLocation } from 'react-router-dom'

export default function Layout() {
    const location = useLocation();

    const isActive = (path: string) => {
        return location.pathname === path;
    };

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
                        <div className="w-full flex justify-center">
                            <div className="hidden sm:flex sm:space-x-4">
                                <Link to="/" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Home
                                </Link>
                                <Link to="/persons" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/persons') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Persons
                                </Link>
                                <Link to="/works" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/works') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Works
                                </Link>
                                <Link to="/places" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/places') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Places
                                </Link>
                                <Link to="/subjects" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/subjects') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Subjects
                                </Link>
                                <Link to="/languages" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/languages') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Languages
                                </Link>
                                <Link to="/scholarly" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/scholarly') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Scholarly Works
                                </Link>
                                <Link to="/sources"
                                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/sources')
                                        ? 'border-indigo-500 text-gray-900'
                                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                                        }`}
                                >
                                    Data Sources
                                </Link>
                                <Link to="/map" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/map') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Map
                                </Link>
                                <Link to="/network" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/network') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Network
                                </Link>
                                <Link to="/ontology" className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${isActive('/ontology') ? 'border-indigo-500 text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                    Ontology
                                </Link>
                            </div>
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
