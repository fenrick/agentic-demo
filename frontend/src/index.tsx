import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Bootstraps the React application and mounts it to the DOM root element.
const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<App />);
}
