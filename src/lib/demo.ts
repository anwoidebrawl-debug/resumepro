import type { User, Resume, Analysis, CoverLetter } from '@/types';

export const DEMO_USER: User = {
  id: 'demo-user-1',
  email: 'demo@resumepro.ai',
  full_name: 'Demo User',
  avatar_url: null,
  role: 'user',
  subscription_tier: 'pro',
  subscription_status: 'active',
  stripe_customer_id: 'demo-customer',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const DEMO_RESUMES: Resume[] = [
  {
    id: 'demo-resume-1',
    user_id: 'demo-user-1',
    file_name: 'John_Smith_Resume.pdf',
    file_url: 'https://example.com/resume.pdf',
    file_size: 245000,
    parsed_content: 'Software Engineer with 5 years of experience in full-stack development. Led development of REST APIs serving 100k+ users. Implemented performance optimizations reducing load time by 40%.',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'demo-resume-2',
    user_id: 'demo-user-1',
    file_name: 'Senior_Developer_Resume.pdf',
    file_url: 'https://example.com/resume2.pdf',
    file_size: 312000,
    parsed_content: 'Senior Frontend Developer specializing in React and TypeScript. Built scalable web applications serving Fortune 500 clients.',
    created_at: new Date(Date.now() - 172800000).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const DEMO_ANALYSES: Analysis[] = [
  {
    id: 'demo-analysis-1',
    user_id: 'demo-user-1',
    resume_id: 'demo-resume-1',
    ats_score: 87,
    keyword_match_score: 82,
    readability_score: 91,
    formatting_score: 85,
    impact_score: 88,
    improvements: [
      {
        type: 'rewrite',
        section: 'Experience',
        original: 'Worked on various projects',
        improved: 'Led cross-functional teams delivering 12+ enterprise projects, resulting in $2M+ cost savings for clients',
        reason: 'Quantifiable achievements significantly improve ATS scores',
      },
      {
        type: 'suggestion',
        section: 'Skills',
        original: '',
        suggestion: 'Add cloud platforms (AWS, GCP) to match job descriptions',
        reason: 'Cloud skills are highly sought after',
      },
    ],
    suggested_skills: ['AWS', 'Docker', 'Kubernetes', 'GraphQL', 'Redis'],
    weak_sections: ['Skills section could be more specific', 'Missing years of experience in header'],
    overall_feedback: 'Your resume is well-structured with good impact statements. Focus on adding quantifiable metrics and cloud technologies to improve keyword matching.',
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 'demo-analysis-2',
    user_id: 'demo-user-1',
    resume_id: 'demo-resume-2',
    ats_score: 92,
    keyword_match_score: 88,
    readability_score: 94,
    formatting_score: 92,
    impact_score: 95,
    improvements: [],
    suggested_skills: ['TypeScript', 'Next.js', 'Tailwind CSS'],
    weak_sections: [],
    overall_feedback: 'Excellent ATS score! Your resume is well-optimized for most job applications. Consider tailoring specific keywords for niche roles.',
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
];

export const DEMO_COVER_LETTERS: CoverLetter[] = [
  {
    id: 'demo-cover-1',
    user_id: 'demo-user-1',
    resume_id: 'demo-resume-1',
    job_title: 'Senior Software Engineer',
    company_name: 'TechCorp Inc.',
    job_description: 'Looking for a Senior Software Engineer to join our team...',
    content: `Dear Hiring Manager,

I am writing to express my strong interest in the Senior Software Engineer position at TechCorp Inc. With five years of experience in full-stack development, I have successfully delivered solutions that scale to millions of users.

In my current role at XYZ Corporation, I led the development of REST APIs serving 100k+ daily active users, reducing response times by 40% through strategic optimization initiatives. I have particular expertise in building performant web applications using React and Node.js.

I am excited about TechCorp's mission to revolutionize how businesses approach digital transformation. My experience in agile environments and passion for clean code would make me a valuable addition to your engineering team.

I would welcome the opportunity to discuss how my skills and experience align with your team's needs. Thank you for considering my application.

Best regards,
Demo User`,
    tone: 'professional',
    created_at: new Date(Date.now() - 43200000).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const DEMO_LINKEDIN_OPTIMIZATION = {
  headline: 'Senior Software Engineer | Full-Stack Development | React • Node.js • TypeScript | Building Scalable Web Applications',
  about_section: `Software Engineer passionate about building clean, efficient code that makes a difference.

With 5+ years in the industry, I've helped companies scale their products from thousands to millions of users. I've led teams that delivered 15+ enterprise projects, resulting in significant cost savings and improved user experiences.

My toolkit includes React, Node.js, TypeScript, AWS, and cloud-native architecture. I thrive in agile environments where innovation and collaboration drive results.

Currently seeking opportunities to leverage my expertise in building performant, user-centric applications.`,
  suggested_skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'AWS', 'Docker', 'PostgreSQL', 'GraphQL', 'Next.js', 'Tailwind CSS'],
  improvements: [
    'Add more quantifiable achievements to your about section',
    'Include industry keywords near the beginning of your headline',
    'Consider adding 2-3 relevant certifications',
    'Update your headline with current positioning',
  ],
};

export function isDemoMode(): boolean {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('demo_mode') === 'true' || 
           new URLSearchParams(window.location.search).get('demo') === 'true';
  }
  return process.env.NEXT_PUBLIC_DEMO_MODE === 'true';
}

export function enableDemoMode(): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('demo_mode', 'true');
  }
}

export function disableDemoMode(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('demo_mode');
  }
}
