import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

if (localStorage.getItem('ms_palette') !== 'crimson-cream-v1') {
  localStorage.setItem('ms_palette', 'crimson-cream-v1');
  localStorage.setItem('ms_dark', '0');
} else if (localStorage.getItem('ms_dark') === null) {
  localStorage.setItem('ms_dark', '0');
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

