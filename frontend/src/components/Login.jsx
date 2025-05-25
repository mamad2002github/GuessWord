import React, { useState } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

const Login = ({ setCurrentPage, setUser, setIsLoggedIn, setError }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/login/`, { username, password });
      localStorage.setItem('token', response.data.access);
      setUser(response.data.user);
      setIsLoggedIn(true);
      setCurrentPage('home');
      setError('');
    } catch (err) {
      setError('نام کاربری یا رمز عبور اشتباه است.');
    }
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <div className="bg-white p-8 rounded-lg shadow-lg w-96">
        <h2 className="text-2xl mb-4 text-center">ورود</h2>
        <form onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="نام کاربری"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full p-2 mb-4 border rounded"
          />
          <input
            type="password"
            placeholder="رمز عبور"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 mb-4 border rounded"
          />
          <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600">
            ورود
          </button>
        </form>
        <p className="mt-4 text-center">
          حساب ندارید؟{' '}
          <button onClick={() => setCurrentPage('register')} className="text-blue-500">
            ثبت‌نام
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;