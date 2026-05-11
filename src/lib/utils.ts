import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date | string): string {
  try {
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) {
      return 'Recent';
    }
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(dateObj);
  } catch {
    return 'Recent';
  }
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount / 100);
}

export function calculateATSScore(analysis: {
  keywordMatch: number;
  readability: number;
  formatting: number;
  impact: number;
}): number {
  const weights = {
    keywordMatch: 0.35,
    readability: 0.2,
    formatting: 0.2,
    impact: 0.25,
  };
  return Math.round(
    analysis.keywordMatch * weights.keywordMatch +
    analysis.readability * weights.readability +
    analysis.formatting * weights.formatting +
    analysis.impact * weights.impact
  );
}

export function getATSScoreGrade(score: number): {
  grade: string;
  color: string;
  description: string;
} {
  if (score >= 90) {
    return {
      grade: 'Excellent',
      color: 'text-green-500',
      description: 'Your resume is highly optimized for ATS systems',
    };
  }
  if (score >= 75) {
    return {
      grade: 'Good',
      color: 'text-emerald-500',
      description: 'Your resume has solid ATS compatibility',
    };
  }
  if (score >= 60) {
    return {
      grade: 'Average',
      color: 'text-yellow-500',
      description: 'Your resume needs some improvements',
    };
  }
  if (score >= 40) {
    return {
      grade: 'Below Average',
      color: 'text-orange-500',
      description: 'Your resume may struggle with ATS systems',
    };
  }
  return {
    grade: 'Poor',
    color: 'text-red-500',
    description: 'Significant improvements needed for ATS success',
  };
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}
