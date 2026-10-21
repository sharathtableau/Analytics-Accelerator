import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Builds ONE ES module (React bundled in) + ONE stylesheet for st.components.v2.
export default defineConfig({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': '"production"' },
  build: {
    outDir: '../streamlit',
    emptyOutDir: false,
    cssCodeSplit: false,
    minify: 'esbuild',
    lib: { entry: 'src/index.jsx', formats: ['es'], fileName: () => 'app_bundle.js' },
    rollupOptions: { output: { assetFileNames: 'app_styles.css' } },
  },
});
