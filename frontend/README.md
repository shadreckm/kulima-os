# Kulima OS Frontend

A clean, minimal Next.js frontend for the Kulima OS coordination intelligence platform.

## Features

- **Dashboard**: Select zone and view coordination patterns, activities, and insights
- **Signal Input Form**: Submit activity signals to the backend
- **Prospectus Generation**: Generate and download PDF/JSON prospectuses
- **Responsive Design**: Mobile-friendly layout with Tailwind CSS
- **Real-time Results**: Live API integration with backend

## Tech Stack

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

## Development

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

### Installation

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Deployment to Vercel

### Option 1: Vercel CLI

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
cd frontend
vercel
```

### Option 2: Vercel Dashboard

1. Push code to GitHub/GitLab/Bitbucket
2. Import project in Vercel dashboard
3. Configure environment variables:
   - `NEXT_PUBLIC_API_URL`: `https://kulima-os-backend.onrender.com/api/v1`
4. Deploy

### Environment Variables

Set the following environment variable in Vercel:

```
NEXT_PUBLIC_API_URL=https://kulima-os-backend.onrender.com/api/v1
```

## API Integration

The frontend connects to the Kulima OS backend API:

- Base URL: `https://kulima-os-backend.onrender.com/api/v1`
- Endpoints used:
  - `GET /summary/{zone}` - Fetch coordination summary
  - `POST /signal` - Submit activity signal
  - `POST /generate-prospectus` - Generate prospectus
  - `GET /zones` - Get available zones

## Project Structure

```
frontend/
├── app/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── Dashboard.tsx
│   ├── SignalForm.tsx
│   └── ProspectusButton.tsx
├── lib/
│   └── api.ts
├── public/
├── next.config.js
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vercel.json
```

## License

MIT
