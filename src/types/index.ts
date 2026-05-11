export type UserRole = 'user' | 'admin';

export type SubscriptionTier = 'free' | 'pro';

export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'trialing' | 'inactive';

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: UserRole;
  subscription_tier: SubscriptionTier;
  subscription_status: SubscriptionStatus;
  stripe_customer_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  stripe_subscription_id: string;
  stripe_price_id: string;
  status: SubscriptionStatus;
  tier: SubscriptionTier;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  created_at: string;
  updated_at: string;
}

export interface Resume {
  id: string;
  user_id: string;
  file_name: string;
  file_url: string;
  file_size: number;
  parsed_content: string | null;
  created_at: string;
  updated_at: string;
}

export interface Analysis {
  id: string;
  user_id: string;
  resume_id: string;
  ats_score: number;
  keyword_match_score: number;
  readability_score: number;
  formatting_score: number;
  impact_score: number;
  improvements: AnalysisImprovement[];
  suggested_skills: string[];
  weak_sections: string[];
  overall_feedback: string;
  created_at: string;
}

export interface AnalysisImprovement {
  type: 'rewrite' | 'suggestion' | 'warning';
  section: string;
  original: string;
  improved?: string;
  suggestion?: string;
  reason: string;
}

export interface CoverLetter {
  id: string;
  user_id: string;
  resume_id: string;
  job_title: string;
  company_name: string;
  job_description: string | null;
  content: string;
  tone: 'professional' | 'friendly' | 'formal' | 'confident';
  created_at: string;
  updated_at: string;
}

export interface LinkedInOptimization {
  id: string;
  user_id: string;
  headline: string;
  about_section: string;
  suggested_skills: string[];
  improvements: string[];
  created_at: string;
  updated_at: string;
}

export interface UsageTracking {
  id: string;
  user_id: string;
  feature: 'resume_analysis' | 'cover_letter' | 'linkedin_optimization';
  count: number;
  period: 'monthly';
  reset_at: string;
}

export interface PricingPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  interval: 'month' | 'year';
  features: string[];
  stripe_price_id: string;
  tier: SubscriptionTier;
}

export interface Testimonial {
  id: string;
  name: string;
  role: string;
  company: string;
  avatar: string;
  content: string;
  rating: number;
}

export interface Feature {
  icon: string;
  title: string;
  description: string;
}
