// src/main.jsx (برای Vite) یا src/index.js

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx'; // یا App.js
// './index.css' یا یک فایل CSS دیگر ممکن است اینجا ایمپورت شده باشد، styles.css اصلی در App.jsx ایمپورت شده

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);