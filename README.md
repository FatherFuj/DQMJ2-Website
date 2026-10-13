Fun little side project where I make a DQMJ2 website that has all of the information I want in one place.

## Deploying on Vercel

The Vite app is in the `vite` directory. In the Vercel project settings, use `vite` as the Root Directory, `npm run build` as the Build Command, and `dist` as the Output Directory.

The production build publishes the homepage and each HTML page under `/pages/`, including `/pages/monsters.html`, `/pages/monster-detail.html`, `/pages/favorites.html`, `/pages/synthesis.html`, and `/pages/skills.html`.
