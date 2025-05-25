import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

const PausedGames = ({ setCurrentPage, setGameId, setError }) => {
  const [pausedGames, setPausedGames] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    axios.get(`${API_BASE_URL}/paused-games/`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setPausedGames(response.data);
    }).catch(() => {
      setError('خطا در بارگذاری بازی‌های متوقف‌شده.');
    });
  }, [setError]);

  const handleResumeGame = async (gameId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_BASE_URL}/game/${gameId}/resume/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGameId(gameId);
      setCurrentPage('game');
    } catch (err) {
      setError('خطا در ادامه بازی.');
    }
  };

  return (
    <div className="flex flex-col items-center p-8">
      <h2 className="text-2xl mb-4">بازی‌های متوقف‌شده</h2>
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
          {pausedGames.map(game => (
            <tr key={game.id} className="border-t">
              <td className="p-2">{game.id}</td>
              <td className="p-2">{game.opponent}</td>
              <td className="p-2">{game.level}</td>
              <td className="p-2">
                <button
                  onClick={() => handleResumeGame(game.id)}
                  className="bg-green-500 text-white p-1 rounded hover:bg-green-600"
                >
                  ادامه
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PausedGames;