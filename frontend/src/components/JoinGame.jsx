import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

const JoinGame = ({ setCurrentPage, setGameId, setError }) => {
  const [pendingGames, setPendingGames] = useState([]);
  const [searchGameId, setSearchGameId] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    axios.get(`${API_BASE_URL}/pending-games/`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setPendingGames(response.data);
    }).catch(() => {
      setError('خطا در بارگذاری بازی‌های در انتظار.');
    });
  }, [setError]);

  const handleJoinGame = async (gameId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_BASE_URL}/join-game/${gameId}/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGameId(gameId);
      setCurrentPage('game');
    } catch (err) {
      setError('خطا در پیوستن به بازی.');
    }
  };

  const handleSearchGame = () => {
    if (searchGameId) {
      handleJoinGame(searchGameId);
    }
  };

  return (
    <div className="flex flex-col items-center p-8">
      <h2 className="text-2xl mb-4">پیوستن به بازی</h2>
      <div className="mb-4">
        <input
          type="text"
          placeholder="شناسه بازی"
          value={searchGameId}
          onChange={(e) => setSearchGameId(e.target.value)}
          className="p-2 border rounded mr-2"
        />
        <button
          onClick={handleSearchGame}
          className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        >
          جستجو
        </button>
      </div>
      <table className="w-full max-w-2xl border">
        <thead>
          <tr className="bg-gray-200">
            <th className="p-2">شناسه بازی</th>
            <th className="p-2">حریف</th>
            <th className="p-2">سطح</th>
            <th className="p-2">اقدام</th>
          </tr>
        </thead>
        <tbody>
          {pendingGames.map(game => (
            <tr key={game.id} className="border-t">
              <td className="p-2">{game.id}</td>
              <td className="p-2">{game.opponent}</td>
              <td className="p-2">{game.level}</td>
              <td className="p-2">
                <button
                  onClick={() => handleJoinGame(game.id)}
                  className="bg-green-500 text-white p-1 rounded hover:bg-green-600"
                >
                  پیوستن
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default JoinGame;