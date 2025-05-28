// src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import HomePage from './components/HomePage';
import ProtectedRoute from './components/ProtectedRoute';
import NewGameSetupPage from './components/NewGameSetupPage';
import GamePage from './components/GamePage';
import JoinGamePage from './components/JoinGamePage';
import ProfilePage from './components/ProfilePage'; // ✅ ایمپورت انجام شد
import './styles.css';
// در بالای فایل App.jsx
import GameHistoryPage from './components/GameHistoryPage'; // ✅ ایمپورت کامپوننت جدید
// در بالای فایل App.jsx
import PausedGamesPage from './components/PausedGamesPage'; // ✅ ایمپورت کامپوننت جدید


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate replace to="/login" />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/home" element={<HomePage />} />
          <Route path="/new-game" element={<NewGameSetupPage />} />
          <Route path="/game/:gameId" element={<GamePage />} />
          <Route path="/join-game-lobby" element={<JoinGamePage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/game-history" element={<GameHistoryPage />} />
          <Route path="/paused-games" element={<PausedGamesPage />} /> {/* ✅ مسیر جدید اضافه شد */}{/* ✅ مسیر جدید اضافه شد */}{/* ✅ مسیر جدید اضافه شد */}
        </Route>
      </Routes>
    </Router>
  );
}

export default App;