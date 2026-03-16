import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import SubmitBadge from './pages/SubmitBadge'
import ReviewResult from './pages/ReviewResult'
import GovernanceLogs from './pages/GovernanceLogs'

function Nav() {
  const linkCls = ({ isActive }) =>
    `text-sm font-medium px-3 py-1.5 rounded transition-colors
     ${isActive
       ? 'bg-white text-njit-red font-semibold'
       : 'text-white/80 hover:text-white hover:bg-white/10'}`

  return (
    <header className="bg-njit-navy text-white">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <NavLink to="/" className="text-white font-bold text-lg tracking-tight hover:opacity-90">
          NJIT Badge Classification
        </NavLink>
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkCls}>Submit Badge</NavLink>
          <NavLink to="/logs" className={linkCls}>Logs</NavLink>
        </nav>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Nav />
        <main>
          <Routes>
            <Route path="/" element={<SubmitBadge />} />
            <Route path="/review/:logId" element={<ReviewResult />} />
            <Route path="/logs" element={<GovernanceLogs />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
