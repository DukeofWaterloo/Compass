import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar.tsx';
import HomePage from './pages/HomePage.tsx';
import RecommendationsPage from './pages/RecommendationsPage.tsx';
import CoursePage from './pages/CoursePage.tsx';
import AboutPage from './pages/AboutPage.tsx';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/course/:courseCode" element={<CoursePage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;