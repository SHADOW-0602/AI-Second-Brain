import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
    root: '.',
    server: {
        port: 5300,
        proxy: {
            '/api': {
                target: 'http://localhost:5300',
                changeOrigin: true,
            }
        }
    },
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './js'),
        },
    },
    build: {
        outDir: '../backend/static',
        emptyOutDir: true,
    }
});
