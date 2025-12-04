import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig(({ command }) => ({
    // root: 'src', // Removed to use default root
    base: command === 'build' ? '/static/' : '/', // Base URL for production assets
    build: {
        outDir: '../app/static', // Output to app/static (relative to frontend/)
        emptyOutDir: true,
        manifest: true, // Generate manifest.json for backend integration
        rollupOptions: {
            input: 'src/main.js', // Entry point relative to root
        },
    },
    server: {
        host: true,
        origin: 'http://localhost:5173', // For CORS in dev
    },
}));
