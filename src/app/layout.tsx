import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import { ThemeProvider } from '@/components/theme-provider';
import { DemoProvider } from '@/hooks/use-demo';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ResumeIQ AI - AI-Powered Resume Optimizer',
  description: 'Get more interviews with AI-optimized resumes. Analyze ATS compatibility, generate cover letters, and improve your job application.',
  keywords: ['ATS resume checker', 'AI resume optimizer', 'AI cover letter generator', 'resume optimization', 'job application'],
  authors: [{ name: 'ResumeIQ AI' }],
  openGraph: {
    title: 'ResumeIQ AI - AI-Powered Resume Optimizer',
    description: 'Get more interviews with AI-optimized resumes',
    url: 'https://resumepro.ai',
    siteName: 'ResumeIQ AI',
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ResumeIQ AI - AI-Powered Resume Optimizer',
    description: 'Get more interviews with AI-optimized resumes',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <DemoProvider>
          {children}
          <Toaster />
          </DemoProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
