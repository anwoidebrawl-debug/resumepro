'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { DEMO_USER, DEMO_RESUMES, DEMO_ANALYSES, DEMO_COVER_LETTERS, DEMO_LINKEDIN_OPTIMIZATION, isDemoMode, enableDemoMode } from '@/lib/demo';
import type { User, Resume, Analysis, CoverLetter } from '@/types';

interface DemoContextType {
  isDemo: boolean;
  user: User | null;
  resumes: Resume[];
  analyses: Analysis[];
  coverLetters: CoverLetter[];
  linkedInOptimization: typeof DEMO_LINKEDIN_OPTIMIZATION | null;
  enterDemo: () => void;
  exitDemo: () => void;
  addResume: (resume: Resume) => void;
  addAnalysis: (analysis: Analysis) => void;
  addCoverLetter: (letter: CoverLetter) => void;
}

const DemoContext = createContext<DemoContextType | null>(null);

export function DemoProvider({ children }: { children: ReactNode }) {
  const [isDemo, setIsDemo] = useState(false);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [coverLetters, setCoverLetters] = useState<CoverLetter[]>([]);
  const [linkedInOptimization, setLinkedInOptimization] = useState<typeof DEMO_LINKEDIN_OPTIMIZATION | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('demo') === 'true') {
      enableDemoMode();
    }
    setIsDemo(isDemoMode());
  }, []);

  useEffect(() => {
    if (isDemo) {
      setResumes(DEMO_RESUMES);
      setAnalyses(DEMO_ANALYSES);
      setCoverLetters(DEMO_COVER_LETTERS);
      setLinkedInOptimization(DEMO_LINKEDIN_OPTIMIZATION);
    }
  }, [isDemo]);

  const enterDemo = () => {
    enableDemoMode();
    setIsDemo(true);
    setResumes(DEMO_RESUMES);
    setAnalyses(DEMO_ANALYSES);
    setCoverLetters(DEMO_COVER_LETTERS);
    setLinkedInOptimization(DEMO_LINKEDIN_OPTIMIZATION);
  };

  const exitDemo = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('demo_mode');
    }
    setIsDemo(false);
    setResumes([]);
    setAnalyses([]);
    setCoverLetters([]);
    setLinkedInOptimization(null);
  };

  const addResume = (resume: Resume) => {
    setResumes(prev => [resume, ...prev]);
  };

  const addAnalysis = (analysis: Analysis) => {
    setAnalyses(prev => [analysis, ...prev]);
  };

  const addCoverLetter = (letter: CoverLetter) => {
    setCoverLetters(prev => [letter, ...prev]);
  };

  return (
    <DemoContext.Provider
      value={{
        isDemo,
        user: isDemo ? DEMO_USER : null,
        resumes,
        analyses,
        coverLetters,
        linkedInOptimization,
        enterDemo,
        exitDemo,
        addResume,
        addAnalysis,
        addCoverLetter,
      }}
    >
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo() {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error('useDemo must be used within DemoProvider');
  }
  return context;
}
