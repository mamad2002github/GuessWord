import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

function Home() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-lg">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Welcome, {user?.username}</h2>
          <button
            onClick={() => {
              logout();
              navigate('/');
            }}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
          >
            Logout
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => navigate('/profile')}
            className="bg-blue-500 text-white p-4 rounded hover:bg-blue-600"
          >
            Profile
          </button>
          <button
            onClick={() => navigate('/new-game')}
            className="bg-blue-500 text-white p-4 rounded hover:bg-blue-600"
          >
            New Game
          </button>
          <button
            onClick={() => navigate('/join-game')}
            className="bg-blue-500 text-white p-4 rounded hover:bg-blue-600"
          >
            Join Game
          </button>
          <button
            onClick={() => navigate('/paused-games')}
            className="bg-blue-500 text-white p-4 rounded hover:bg-blue-600"
          >
            Paused Games
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home;