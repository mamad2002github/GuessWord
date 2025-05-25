import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { toast } from 'react-toastify';

function Profile() {
  const { user, token } = useContext(AuthContext);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    axios.get('/api/game-history/', {
      headers: { Authorization: `Token ${token}` }
    }).then(response => {
      setHistory(response.data);
    }).catch(() => {
      toast.error('Error fetching game history');
    });
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold mb-6">Profile</h2>
        <div className="mb-6">
          <p><strong>Username:</strong> {user?.username}</p>
          <p><strong>First Name:</strong> {user?.first_name}</p>
          <p><strong>Last Name:</strong> {user?.last_name}</p>
          <p><strong>Coins:</strong> {user?.coins}</p>
          <p><strong>XP:</strong> {user?.xp}</p>
          <p><strong>Level:</strong> {user?.level}</p>
        </div>
        <h3 className="text-xl font-bold mb-4">Game History</h3>
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-200">
              <th className="p-2 border">Game ID</th>
              <th className="p-2 border">Opponent</th>
              <th className="p-2 border">Level</th>
              <th className="p-2 border">Date</th>
              <th className="p-2 border">Result</th>
            </tr>
          </thead>
          <tbody>
            {history.map((game) => (
              <tr key={game.game_id}>
                <td className="p-2 border">{game.game_id}</td>
                <td className="p-2 border">{game.opponent}</td>
                <td className="p-2 border">{game.level}</td>
                <td className="p-2 border">{new Date(game.date).toLocaleString()}</td>
                <td className="p-2 border">{game.result}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Profile;