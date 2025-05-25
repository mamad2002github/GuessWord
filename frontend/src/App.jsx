import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from './config';
import Login from './components/Login';
import Register from './components/Register';
import Home from './components/Home';
import Profile from './components/Profile';
import NewGame from './components/NewGame';
import JoinGame from './components/JoinGame';
import PausedGames from './components/PausedGames';
import Game from './components/Game';

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentPage, setCurrentPage] = useState('login');
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');
  const [gameId, setGameId] = useState(null);

  // بررسی ورود کاربر
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.get(`${API_BASE_URL}/profile/`, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(response => {
        setUser(response.data);
        setIsLoggedIn(true);
        setCurrentPage('home');
      }).catch(() => {
        localStorage.removeItem('token');
      });
    }
  }, []);

  // رندر صفحات
  const renderPage = () => {
    switch (currentPage) {
      case 'login':
        return <Login setCurrentPage={setCurrentPage} setUser={setUser} setIsLoggedIn={setIsLoggedIn} setError={setError} />;
      case 'register':
        return <Register setCurrentPage={setCurrentPage} setError={setError} />;
      case 'home':
        return <Home user={user} setCurrentPage={setCurrentPage} />;
      case 'profile':
        return <Profile user={user} />;
      case 'new-game':
        return <NewGame setCurrentPage={setCurrentPage} setGameId={setGameId} setError={setError} />;
      case 'waiting':
        return (
          <div className="flex flex-col items-center p-8">
            <h2 className="text-2xl mb-4">در انتظار بازیکن دوم...</h2>
            <p>شناسه بازی: {gameId}</p>
          </div>
        );
      case 'join-game':
        return <JoinGame setCurrentPage={setCurrentPage} setGameId={setGameId} setError={setError} />;
      case 'paused-games':
        return <PausedGames setCurrentPage={setCurrentPage} setGameId={setGameId} setError={setError} />;
      case 'game':
        return <Game gameId={gameId} setCurrentPage={setCurrentPage} setError={setError} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 font-sans">
      {error && (
        <div className="fixed top-4 right-4 bg-red-500 text-white p-4 rounded shadow-lg">
          {error}
          <button onClick={() => setError('')} className="ml-4">×</button>
        </div>
      )}
      {renderPage()}
    </div>
  );
};

export default App;