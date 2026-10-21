import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';
import { installFont } from './font.js';

installFont();

/**
 * Streamlit Components v2 entry point. Called on every Streamlit rerun with fresh
 * `data`; the React root is created once per mount point and re-rendered in place.
 * Actions go back to Python through a single trigger value: {id, type, payload}.
 */
export default function mount(component) {
  const { parentElement, data, setTriggerValue } = component;
  const host = parentElement.querySelector('.aa-root') || parentElement;
  if (!host.__aa) {
    host.__aa = { root: createRoot(host) };
  }
  const emit = (msg) => setTriggerValue('action', msg);
  host.__aa.root.render(<App data={data || {}} emit={emit} />);
}
