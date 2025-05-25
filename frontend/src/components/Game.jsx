import React, { useState, useEffect } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

const Game = ({ gameId, setCurrentPage, setError }) => {
  const [gameState, setGameState] = useState(null);
  const [guess, setGuess] = useState('');
  const [fullGuess, setFullGuess] = useState('');
  const [guessedLetters, setGuessedLetters] = useState([]);

  // بارگذاری وضعیت بازی
  useEffect(() => {
    const token = localStorage.getItem('token');
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/game/${gameId}/state/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setGameState(response.data);
        setGuessedLetters(response.data.guessed_letters || []);
        if (response.data.status === 'finished') {
          setCurrentPage('home');
          setError(response.data.winner ? `بازی تمام شد! برنده: ${response.data.winner}` : 'بازی تمام شد!');
        }
      } catch (err) {
        setError('خطا در بارگذاری وضعیت بازی.');
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [gameId, setCurrentPage, setError]);

  // حدس حرف
  const handleGuess = async () => {
    if (!gameState?.is_turn || !guess) return;
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/game/${gameId}/guess/`,
        { letter: guess },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGameState(response.data);
      setGuessedLetters([...guessedLetters, { letter: guess, correct: response.data.correct }]);
      setGuess('');
    } catch (err) {
      setError('خطا در حدس حرف.');
    }
  };

  // درخواست نکته بیشتر
  const handleHint = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/game/${gameId}/hint/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGameState(response.data);
    } catch (err) {
      setError('خطا در دریافت نکته.');
    }
  };

  // نمایش یک حرف
  const handleRevealLetter = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/game/${gameId}/reveal-letter/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGameState(response.data);
    } catch (err) {
      setError('خطا در نمایش حرف.');
    }
  };

  // حدس کل کلمه
  const handleGuessWord = async () => {
    if (!fullGuess) return;
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/game/${gameId}/guess-word/`,
        { word: fullGuess },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setGameState(response.data);
      if (response.data.status === 'finished') {
        setCurrentPage('home');
        setError(response.data.winner ? `بازی تمام شد! برنده: ${response.data.winner}` : 'بازی تمام شد!');
      }
      setFullGuess('');
    } catch (err) {
      setError('خطا در حدس کلمه.');
    }
  };

  // توقف بازی
  const handlePause = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_BASE_URL}/game/${gameId}/pause/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCurrentPage('home');
    } catch (err) {
      setError('خطا در توقف بازی.');
    }
  };

  if (!gameState) return <div className="text-center p-8">در حال بارگذاری...</div>;

  return (
    <div className="flex flex-col items-center p-8">
      <h2 className="text-2xl mb-4">بازی</h2>
      <p className="text-lg mb-2">کلمه: {gameState.word_display.split('').map((char, index) => (
        <span
          key={index}
          className={`inline-block mx-1 text-2xl ${char !== '-' ? 'text-green-500 animate-pulse' : ''}`}
        >
          {char}
        </span>
      ))}</p>
      <p className="mb-2">نکته: {gameState.current_hint}</p>
      <p className="mb-2">سکه‌ها: {gameState.coins}</p>
      <p className="mb-2">امتیاز: {gameState.score}</p>
      <p className="mb-2">زمان باقی‌مانده: {Math.floor(gameState.time_remaining / 60)}:{(gameState.time_remaining % 60).toString().padStart(2, '0')}</p>
      <p className="mb-2">{gameState.is_turn ? 'نوبت شماست!' : 'نوبت حریف!'}</p>
      <div className="mb-4">
        {guessedLetters.map((g, index) => (
          <span
            key={index}
            className={`inline-block mx-1 ${g.correct ? 'text-green-500' : 'text-red-500'} animate-slide-down`}
          >
            {g.letter}
            {!g.correct && <span className="text-red-500">✗</span>}
          </span>
        ))}
      </div>
      {gameState.is_turn && (
        <div className="mb-4">
          <input
            type="text"
            maxLength="1"
            value={guess}
            onChange={(e) => setGuess(e.target.value.toUpperCase())}
            className="p-2 border rounded mr-2"
            placeholder="حرف"
          />
          <button
            onClick={handleGuess}
            className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
          >
            اعمال
          </button>
        </div>
      )}
      {gameState.is_turn && (
        <div className="mb-4">
          <input
            type="text"
            value={fullGuess}
            onChange={(e) => setFullGuess(e.target.value.toUpperCase())}
            className="p-2 border rounded mr-2"
            placeholder="حدس کل کلمه"
          />
          <button
            onClick={handleGuessWord}
            className="bg-yellow-500 text-white p-2 rounded hover:bg-yellow-600"
          >
            حدس کل کلمه
          </button>
        </div>
      )}
      <div className="space-x-4">
        <button
          onClick={handlePause}
          className="bg-red-500 text-white p-2 rounded hover:bg-red-600"
        >
          توقف بازی
        </button>
        <button
          onClick={handleHint}
          className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
        >
          نکته بیشتر
        </button>
        <button
          onClick={handleRevealLetter}
          className="bg-green-500 text-white p-2 rounded hover:bg-green-600"
        >
          نمایش یک حرف
        </button>
      </div>
    </div>
  );
};

export default Game;