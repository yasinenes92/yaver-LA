import { defineConfig } from 'vite';
import { resolve } from 'path';
import {
  copyFileSync,
  mkdirSync,
  existsSync,
  readdirSync,
  statSync,
} from 'fs';

// Copy helper
function copyDir(src, dest) {
  if (!existsSync(src)) return;
  if (!existsSync(dest)) mkdirSync(dest, { recursive: true });

  for (const entry of readdirSync(src)) {
    const srcPath = resolve(src, entry);
    const destPath = resolve(dest, entry);
    if (statSync(srcPath).isDirectory()) copyDir(srcPath, destPath);
    else copyFileSync(srcPath, destPath);
  }
}

// Custom plugin to copy static assets into dist/
function copyAssetsPlugin() {
  return {
    name: 'copy-assets',
    writeBundle() {
      try {
        // These are used by main.js via scriptURL + 'lib/...', etc.
        copyDir('lib', 'dist/lib');
        copyDir('lang', 'dist/lang');
        copyDir('css', 'dist/css');
        copyDir('images', 'dist/images');

        // These are referenced as scriptURL + 'notify.js' and 'resources.js'
        if (existsSync('notify.js')) copyFileSync('notify.js', 'dist/notify.js');
        if (existsSync('resources.js')) copyFileSync('resources.js', 'dist/resources.js');

        // Publish the unminified script too
        mkdirSync('dist/js', { recursive: true });
        copyFileSync('js/main.js', 'dist/js/main.js');

        // Move dist/src/index.html to dist/index.html (Vite sometimes nests it)
        if (existsSync('dist/src/index.html')) {
          copyFileSync('dist/src/index.html', 'dist/index.html');
        }
      } catch (e) {
        console.warn('[copy-assets] warning:', e?.message || e);
      }
    },
  };
}

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';

  return {
    // GitHub Pages base path (repo name)
    base: '/yaver-LA/',

    root: '.',

    build: {
      outDir: 'dist',
      emptyOutDir: true,
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/index.html'),
          main: resolve(__dirname, 'js/main.js'),
        },
        output: {
          entryFileNames: (chunkInfo) =>
            chunkInfo.name === 'main' ? 'js/main.min.js' : '[name].js',
          assetFileNames: 'assets/[name][extname]',
        },
      },

      // IMPORTANT:
      // Keep it stable; mangling can rename variables into "$" or "_" and break TW runtime.
      minify: isProduction ? 'terser' : false,
      terserOptions: isProduction
        ? {
            mangle: false,
            compress: { drop_console: true },
            format: { comments: false },
          }
        : {},
    },

    server: {
      port: 3000,
      open: '/src/index.html',
    },

    preview: {
      port: 4173,
      open: true,
    },

    plugins: [copyAssetsPlugin()],
  };
});
