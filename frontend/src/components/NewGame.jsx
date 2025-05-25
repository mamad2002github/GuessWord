import React from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

const NewGame = ({ setCurrentPage, setGameId, setError }) => {
  const handleNewGame = async (level) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/new-game/`,
        { level },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGameId(response.data.id);
      setCurrentPage('waiting');
      // بررسی وضعیت بازی
      const interval = setInterval(async () => {
        try {
          const stateResponse = await axios.get(`${API_BASE_URL}/game/${response.data.id}/state/`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (stateResponse.data.status === 'active') {
            clearInterval(interval);
            setCurrentPage('game');
          }
        } catch (err) {
          clearInterval(interval);
          setError('خطا در بررسی وضعیت بازی.');
        }
      }, 2000);
    } catch (err) {
      setError('خطا در ایجاد بازی.');
    }
  };

  return (
    <div className="flex flex-col items-center p-8">
      <h2 className="text-2xl mb-4">ایجاد بازی جدید</h2>
      <div className="space-x-4">
        <button
          onClick={() => handleNewGame('easy')}
          className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        >
          ساده
        </button>
        <button
          onClick={() => handleNewGame('medium')}
          className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        >
          متوسط
        </button>
        <button
          onClick={() => handleNewGame('hard')}
          className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        >
          پیشرفته
        </button>
      </div>
    </div>
  );
};

export default NewGame;