-- ResumeIQ AI Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Users table
create table if not exists public.users (
  id uuid references auth.users on delete cascade not null primary key,
  email text not null,
  full_name text,
  avatar_url text,
  role text default 'user' check (role in ('user', 'admin')),
  subscription_tier text default 'free' check (subscription_tier in ('free', 'pro')),
  subscription_status text default 'active' check (subscription_status in ('active', 'canceled', 'past_due', 'trialing', 'inactive')),
  stripe_customer_id text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Row Level Security for users
alter table public.users enable row level security;

create policy "Users can view their own profile"
  on public.users for select
  using (auth.uid() = id);

create policy "Users can update their own profile"
  on public.users for update
  using (auth.uid() = id);

-- Subscriptions table
create table if not exists public.subscriptions (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users on delete cascade not null,
  stripe_subscription_id text unique not null,
  stripe_price_id text not null,
  status text not null check (status in ('active', 'canceled', 'past_due', 'trialing', 'inactive')),
  tier text not null check (tier in ('free', 'pro')),
  current_period_start timestamp with time zone not null,
  current_period_end timestamp with time zone not null,
  cancel_at_period_end boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.subscriptions enable row level security;

create policy "Users can view their own subscriptions"
  on public.subscriptions for select
  using (auth.uid() = user_id);

create policy "Service role can manage subscriptions"
  on public.subscriptions for all
  using (auth.jwt()->>'role' = 'service_role');

-- Resumes table
create table if not exists public.resumes (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users on delete cascade not null,
  file_name text not null,
  file_url text not null,
  file_size integer,
  parsed_content text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.resumes enable row level security;

create policy "Users can manage their own resumes"
  on public.resumes for all
  using (auth.uid() = user_id);

-- Analyses table
create table if not exists public.analyses (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users on delete cascade not null,
  resume_id uuid references public.resumes on delete cascade not null,
  ats_score integer not null,
  keyword_match_score integer not null,
  readability_score integer not null,
  formatting_score integer not null,
  impact_score integer not null,
  improvements jsonb default '[]'::jsonb,
  suggested_skills jsonb default '[]'::jsonb,
  weak_sections jsonb default '[]'::jsonb,
  overall_feedback text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.analyses enable row level security;

create policy "Users can manage their own analyses"
  on public.analyses for all
  using (auth.uid() = user_id);

-- Cover letters table
create table if not exists public.cover_letters (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users on delete cascade not null,
  resume_id uuid references public.resumes on delete set null,
  job_title text not null,
  company_name text not null,
  job_description text,
  content text not null,
  tone text default 'professional' check (tone in ('professional', 'friendly', 'formal', 'confident')),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.cover_letters enable row level security;

create policy "Users can manage their own cover letters"
  on public.cover_letters for all
  using (auth.uid() = user_id);

-- Usage tracking table
create table if not exists public.usage_tracking (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.users on delete cascade not null,
  feature text not null check (feature in ('resume_analysis', 'cover_letter', 'linkedin_optimization')),
  count integer default 0,
  period text default 'monthly',
  reset_at timestamp with time zone not null,
  unique(user_id, feature, period)
);

alter table public.usage_tracking enable row level security;

create policy "Users can manage their own usage"
  on public.usage_tracking for all
  using (auth.uid() = user_id);

-- Function to auto-create user record
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, full_name, avatar_url)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$ language plpgsql security definer;

-- Trigger to auto-create user on signup
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Storage bucket for resumes
insert into storage.buckets (id, name, public)
values ('resumes', 'resumes', false)
on conflict (id) do nothing;

-- Storage policy
create policy "Users can upload their own resumes"
  on storage.objects for insert
  with check (bucket_id = 'resumes' and auth.uid()::text = (name split_part(storage.foldername(name), '/', 1)));

create policy "Users can view their own resumes"
  on storage.objects for select
  using (bucket_id = 'resumes' and auth.uid()::text = (name split_part(storage.foldername(name), '/', 1)));

create policy "Users can delete their own resumes"
  on storage.objects for delete
  using (bucket_id = 'resumes' and auth.uid()::text = (name split_part(storage.foldername(name), '/', 1)));
