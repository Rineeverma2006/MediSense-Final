import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [
      react(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['icons/medisense.svg'],
        manifest: {
          name: 'MediSense Healthcare Intelligence',
          short_name: 'MediSense',
          description: 'Personal health records and educational health tools.',
          theme_color: '#211e1b',
          background_color: '#f2f2f0',
          display: 'standalone',
          start_url: '/',
          icons: [
            { src: '/icons/medisense.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' },
          ],
        },
        workbox: {
          navigateFallback: '/index.html',
          navigateFallbackDenylist: [/^\/api(?:\/|$)/],
          globPatterns: ['**/*.{js,css,html,svg,woff2,png,ico}'],
          cleanupOutdatedCaches: true,
        },
      }),
    ],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': { target: env.API_PROXY_TARGET || 'http://localhost:8000', changeOrigin: true },
      },
    },
  };
});
