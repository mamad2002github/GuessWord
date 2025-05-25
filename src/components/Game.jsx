import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { toast } from 'react-toastify';
import { connectWebSocket, sendWebSocketMessage, closeWebSocket } from '../websocket';

function Game() {
  const { gameId } = useParams();
  const { user, token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [gameState, setGameState] = useState(null);
  const [letter, setLetter] = useState('');
  const [position, setPosition] = useState(0);
  const [guessWord, setGuessWord] = useState('');

  useEffect(() => {
    const fetchGameState = async () => {
      try {
        const response = await axios.get(`/api/game/${gameId}/state/`, {
          headers: { Authorization: `Token ${token}` }
        });
        setGameState(response.data);
      } catch (error) {
        toast.error('Error fetching game state');
      }
    };

    fetchGameState();
    connectWebSocket(gameId, user, (data) => {
      if (data.status === 'finished') {
        toast.success(`Game ended! Winner: ${data.winner}`);
        navigate('/home');
      } else {
        setGameState((prev) => ({ ...prev, current_player: data.current_player }));
      }
    });

    const interval = setInterval(() => {
      sendWebSocketMessage({ action: 'check_timeout' });
      if (gameState) {
        setGameState((prev) => ({
          ...prev,
          player1_time: prev.player1_time - 1,
          player2_time: prev.player2_time - 1
        }));
      }
    }, 1000);

    return () => {
      closeWebSocket();
      clearInterval(interval);
    };
  }, [gameId, token, user, gameState]);

  const handleGuess = async () => {
    try {
      const response = await axios.post(`/api/game/${gameId}/guess/`, { letter, position }, {
        headers: { Authorization: `Token ${token}` }
      });
      setGameState((prev) => ({ ...prev, guessed_letters: response.data.guessed_letters }));
      if (response.data.status === 'game ended') {
        toast.success(`Game ended! Winner: ${response.data.winner}`);
        navigate('/home');
      }
      setLetter('');
    } catch (error) {
      toast.error('Error guessing letter');
    }
  };

  const handleHint = async () => {
    try {
      const response = await axios.post(`/api/game/${gameId}/hint/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      toast.success(`New hint: ${response.data.hint}`);
    } catch (error) {
      toast.error('Error getting hint');
    }
  };

  const handleRevealLetter = async () => {
    try {
      const response = await axios.post(`/api/game/${gameId}/reveal-letter/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      toast.success(`Revealed letter: ${response.data.letter} at position ${response.data.position}`);
    } catch (error) {
      toast.error('Error revealing letter');
    }
  };

  const handlePause = async () => {
    try {
      await axios.post(`/api/game/${gameId}/pause/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      toast.success('Game paused');
      navigate('/home');
    } catch (error) {
      toast.error('Error pausing game');
    }
  };

  const handleGuessWord = async () => {
    try {
      const response = await axios.post(`/api/game/${gameId}/guess-word/`, { guess: guessWord }, {
        headers: { Authorization: `Token ${token}` }
      });
      toast.success(`Game ended! Winner: ${response.data.winner}`);
      navigate('/home');
    } catch (error) {
      toast.error('Error guessing word');
    }
  };

  if (!gameState) return <div className="text-center mt-10">Loading...</div>;

  const wordDisplay = Array(gameState.word_length).fill('_').map((_, i) => {
    const revealed = gameState.revealed_letters.includes(gameState.word?.text[i]);
    const guessed = Object.entries(gameState.guessed_letters).find(
      ([_, v]) => v.correct && v.position === i
    );
    return revealed || guessed ? gameState.word?.text[i] : '_';
  });

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-6">Game: {gameId}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <p><strong>Your Score:</strong> {gameState.player1_score}</p>
            <p><strong>Opponent Score:</strong> {gameState.player2_score}</p>
            <p><strong>Your Time:</strong> {Math.floor(gameState.player1_time / 60)}:{gameState.player1_time % 60}</p>
            <p><strong>Opponent Time:</strong> {Math.floor(gameState.player2_time / 60)}:{gameState.player2_time % 60}</p>
            <p><strong>Current Turn:</strong> {gameState.current_player}</p>
          </div>
          <div>
            <p><strong>Word:</strong> {wordDisplay.join(' ')}</p>
            <p><strong>Hints:</strong> {gameState.hints.join(', ')}</p>
          </div>
        </div>
        {gameState.current_player === user.username && (
          <div className="mb-6">
            <div className="flex mb-4">
              <input
                type="text"
                value={letter}
                onChange={(e) => setLetter(e.target.value.toUpperCase())}
                maxLength="1"
                className="p-2 border rounded mr-2"
                placeholder="Letter"
              />
              <select
                value={position}
                onChange={(e) => setPosition(Number(e.target.value))}
                className="p-2 border rounded mr-2"
              >
                {Array(gameState.word_length).fill().map((_, i) => (
                  <option key={i} value={i}>{i + 1}</option>
                ))}
              </select>
              <button
                onClick={handleGuess}
                className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
              >
                Guess Letter
              </button>
            </div>
            <div className="flex mb-4">
              <input
                type="text"
                value={guessWord}
                onChange={(e) => setGuessWord(e.target.value)}
                className="p-2 border rounded mr-2"
                placeholder="Guess the word"
              />
              <button
                onClick={handleGuessWord}
                className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
              >
                Guess Word
              </button>
            </div>
            <div className="flex gap-4">
              <button
                onClick={handleHint}
                className="bg-green-500 text-white p-2 rounded hover:bg-green-600"
              >
                Get Hint (1 Coin)
              </button>
              <button
                onClick={handleRevealLetter}
                className="bg-yellow-500 text-white p-2 rounded hover:bg-yellow-600"
              >
                Reveal Letter (1 Coin)
              </button>
              <button
                onClick={handlePause}
                className="bg-red-500 text-white p-2 rounded hover:bg-red-600"
              >
                Pause Game
              </button>
            </div>
          </div>
        )}
        <div className="flex gap-4">
          {Object.entries(gameState.guessed_letters).map(([letter, info]) => (
            <div
              key={letter}
              className={`p-2 border rounded ${info.correct ? 'bg-green-100 fade-in' : 'bg-red-100 shake'}`}
            >
              {letter} {info.correct ? '✅' : '❌'}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Game;