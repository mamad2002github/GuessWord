import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

const Profile = ({ user }) => {
  const [gameHistory, setGameHistory] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    axios.get(`${API_BASE_URL}/game-history/`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setGameHistory(response.data);
    });
  }, []);

  return (
    <div className="flex flex-col items-center p-8">
      <h2 className="text-2xl mb-4">پروفایل</h2>
      <p>نام: {user.first_name} {user.last_name}</p>
      <p>نام کاربری: {user.username}</p>
      <p>سکه‌ها: {user.coins}</p>
      <p>XP: {user.xp} (سطح: {Math.floor(user.xp / 1000)})</p>
      <h3 className="text-xl mt-4">تاریخچه بازی‌ها</h3>
      <ul className="mt-2 w-full max-w-2xl">
        {gameHistory.map(game => (
          <li key={game.id} className="border p-2 mb-2 rounded">
            بازی {game.id} | حریف: {game.opponent} | سطح: {game.level} | تاریخ: {game.date} | نتیجه: {game.result}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Profile;