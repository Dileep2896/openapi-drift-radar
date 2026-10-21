import { Route, Routes } from 'react-router'
import { Radar } from './pages/Radar.tsx'
import { Story } from './pages/Story.tsx'

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Radar />} />
      <Route path="/story" element={<Story />} />
      <Route path="*" element={<Radar />} />
    </Routes>
  )
}
