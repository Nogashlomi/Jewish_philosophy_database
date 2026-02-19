import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'

import Persons from './pages/Persons'
import PersonDetail from './pages/PersonDetail'
import Works from './pages/Works'
import WorkDetail from './pages/WorkDetail'
import Places from './pages/Places'
import PlaceDetail from './pages/PlaceDetail'
import Subjects from './pages/Subjects'
import SubjectDetail from './pages/SubjectDetail'
import Languages from './pages/Languages'
import LanguageDetail from './pages/LanguageDetail'
import Scholarly from './pages/Scholarly'
import ScholarlyDetail from './pages/ScholarlyDetail'
import MapView from './pages/Map'
import Network from './pages/Network'
import Ontology from './pages/Ontology'
import Sources from './pages/Sources'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="persons" element={<Persons />} />
            <Route path="persons/:id" element={<PersonDetail />} />
            <Route path="works" element={<Works />} />
            <Route path="works/:id" element={<WorkDetail />} />
            <Route path="places" element={<Places />} />
            <Route path="places/:id" element={<PlaceDetail />} />
            <Route path="subjects" element={<Subjects />} />
            <Route path="subjects/:id" element={<SubjectDetail />} />
            <Route path="languages" element={<Languages />} />
            <Route path="languages/:id" element={<LanguageDetail />} />
            <Route path="scholarly" element={<Scholarly />} />
            <Route path="scholarly/:id" element={<ScholarlyDetail />} />
            <Route path="map" element={<MapView />} />
            <Route path="network" element={<Network />} />
            <Route path="ontology" element={<Ontology />} />
            <Route path="sources" element={<Sources />} />
            {/* Additional routes will be added here */}
            <Route path="*" element={<div className="p-8">Page Not Found</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
