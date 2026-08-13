# InterviewSage AI - Frontend

## Overview

Frontend for InterviewSage AI - An Agentic AI Interview Simulation Platform.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State Management**: TanStack Query (server state) + Context API (UI state)
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **HTTP Client**: Axios

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # Application entry point
│   ├── App.tsx               # Root component with providers
│   ├── routes/
│   │   └── index.tsx         # Route configuration
│   ├── pages/                # Page components
│   │   ├── LandingPage/
│   │   ├── AuthPage/
│   │   ├── DashboardPage/
│   │   ├── ResumeUploadPage/
│   │   ├── JDUploadPage/
│   │   ├── InterviewWizardPage/
│   │   ├── LiveInterviewPage/
│   │   ├── EvaluationPage/
│   │   ├── ReportPage/
│   │   ├── AnalyticsPage/
│   │   ├── HistoryPage/
│   │   ├── AdminDashboardPage/
│   │   └── SettingsPage/
│   ├── components/           # Reusable components
│   │   ├── layout/          # Navbar, Sidebar, PageShell
│   │   ├── ui/              # Buttons, Cards, Dialogs, Inputs
│   │   ├── interview/       # QuestionCard, EvaluationCard
│   │   ├── charts/          # Chart wrappers
│   │   └── feedback/        # EmptyState, ErrorState, Skeletons
│   ├── context/             # React contexts
│   │   ├── AuthContext.tsx  # Authentication state
│   │   └── ThemeContext.tsx # Theme (light/dark) state
│   ├── hooks/               # Custom hooks
│   ├── api/                 # API client and endpoints
│   │   └── client.ts        # Axios configuration
│   ├── types/               # TypeScript types
│   │   └── domain.ts        # Domain types (mirroring backend)
│   ├── styles/              # Global styles
│   │   └── globals.css      # Design tokens and Tailwind
│   └── tests/               # Component tests
├── public/                  # Static assets
├── tailwind.config.js       # Tailwind configuration
├── vite.config.ts           # Vite configuration
└── package.json             # Dependencies
```

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file from template:
```bash
cp .env.example .env
```

3. Configure environment variables in `.env`:
   - `VITE_API_BASE_URL`: Backend API URL (default: http://127.0.0.1:8000)

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:5173

### Building

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Design System

InterviewSage AI follows a minimalist, professional design inspired by Linear, Cursor, and Stripe:

- **Colors**: Restrained palette with a single accent color (blue)
- **Typography**: Inter for UI, Fira Code for code snippets
- **Spacing**: 4px-based scale (4, 8, 12, 16, 24, 32, 48, 64)
- **Shadows**: Three elevation tiers (subtle, medium, prominent)
- **Themes**: Full light and dark mode support

## Testing

Run tests:
```bash
npm test
```

With coverage:
```bash
npm run test:coverage
```

## Architecture Highlights

### State Management

- **TanStack Query** owns all server state (resumes, interviews, reports)
- **Context API** owns UI/session state (auth, theme)
- No business data in Context (enforced by convention)

### API Layer

All HTTP requests go through `src/api/client.ts` with:
- Automatic JWT token injection
- Centralized error handling
- Response normalization
- Auto-redirect on 401

### Routing

React Router v6 with route-based code splitting (future optimization)

## Phase 0 Status

✓ Complete folder structure
✓ Tailwind CSS configured with design tokens
✓ React Router setup with all routes
✓ AuthContext and ThemeContext
✓ API client with interceptors
✓ TypeScript domain types
✓ Placeholder pages for all routes
✓ Vite dev server with proxy to backend

## Next Steps (Phase 10)

- Implement design system components
- Build out page implementations
- Add SSE streaming for live interview
- Implement charts for analytics
- Full accessibility pass

## License

Proprietary - InterviewSage AI
