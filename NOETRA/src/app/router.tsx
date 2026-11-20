import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { LandingPage } from '@/pages/LandingPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { LibraryPage } from '@/pages/LibraryPage'
import { VideoWorkspacePage } from '@/pages/VideoWorkspacePage'
import { NotesStudioPage } from '@/pages/NotesStudioPage'
import { TutorPage } from '@/pages/TutorPage'
import { QuizStudioPage } from '@/pages/QuizStudioPage'
import { GeneratedQuizzesPage } from '@/pages/GeneratedQuizzesPage'
import { KnowledgeMapPage } from '@/pages/KnowledgeMapPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { DesignSystemPage } from '@/pages/DesignSystemPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    // Layout route (no path) — wraps all application routes with the sidebar shell
    element: <AppLayout />,
    children: [
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'library', element: <LibraryPage /> },
      { path: 'learn/:videoId', element: <VideoWorkspacePage /> },
      { path: 'notes/:videoId', element: <NotesStudioPage /> },
      { path: 'tutor', element: <TutorPage /> },
      { path: 'quiz/:videoId', element: <QuizStudioPage /> },
      { path: 'quizzes', element: <GeneratedQuizzesPage /> },
      { path: 'knowledge/:videoId', element: <KnowledgeMapPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'design-system', element: <DesignSystemPage /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
])
