import { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { toast } from 'react-toastify';

function JoinGame() {
  const [games, setGames] = useState([]);
  const [gameId, setGameId] = useState('');
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('/api/pending-games/', {
      headers: { Authorization: `Token ${token}` }
    }).then(response => {
      setGames(response.data);
    }).catch(() => {
      toast.error('Error fetching games');
    });
  }, [token]);

  const handleJoin = async (id) => {
    try {
      await axios.post(`/api/join-game/${id}/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      toast.success('Joined game!');
      navigate(`/game/${id}`);
    } catch (error) {
      toast.error('Error joining game');
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/join-game/${gameId}/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      toast.success('Joined game!');
      navigate(`/game/${gameId}`);
    } catch (error) {
      toast.error('Game not found');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-6">Join Game</h2>
        <form onSubmit={handleSearch} className="mb-6">
          <div className="flex">
            <input
              type="text"
              value={gameId}
              onChange={(e) => setGameId(e.target.value)}
              placeholder="Enter Game ID"
              className="flex-1 p-2 border rounded-l"
            />
            <button type="submit" className="bg-blue-500 text-white p-2 rounded-r hover:bg-blue-600">
              Search
            </button>
          </div>
        </form>
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-200">
              <th className="p-2 border">Game ID</th>
              <th className="p-2 border">Creator</th>
              <th className="p-2 border">Level</th>
              <th className="p-2 border">Action</th>
            </tr>
          </thead>
          <tbody>
            {games.map((game) => (
              <tr key={game.game_id}>
                <td className="p-2 border">{game.game_id}</td>
                <td className="p-2 border">{game.player1}</td>
                <td className="p-2 border">{game.level}</td>
                <td className="p-2 border">
                  <button
                    onClick={() => handleJoin(game.game_id)}
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                  >
                    Join
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default JoinGame;