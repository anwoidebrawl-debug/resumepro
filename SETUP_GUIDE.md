# ResumeIQ AI - Complete Setup Guide

## Quick Start (Demo Mode - No Database)

The app works with demo mode without any database:

1. **Start the server:**
```powershell
cd C:\resumepro
npm run dev
```

2. **Open:** http://localhost:3000

3. **Click "Try Demo Mode"** on the login page

---

## Full Setup with Supabase

### Step 1: Create Supabase Account
1. Go to https://supabase.com
2. Sign up / Login
3. Create a new project

### Step 2: Get Your Credentials
From your Supabase project dashboard:
- **Project URL** (Settings > API)
- **anon/public key** (Settings > API)
- **service_role key** (Settings > API) - keep secret!

### Step 3: Update .env.local
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
OPENAI_API_KEY=sk-your-openai-key
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Step 4: Run Database Schema
Go to Supabase Dashboard > SQL Editor and run:

```sql
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

-- Enable RLS
alter table public.users enable row level security;

create policy "Users can view own profile" on public.users for select using (auth.uid() = id);
create policy "Users can update own profile" on public.users for update using (auth.uid() = id);

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
create policy "Users manage own resumes" on public.resumes for all using (auth.uid() = user_id);

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
create policy "Users manage own analyses" on public.analyses for all using (auth.uid() = user_id);

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
create policy "Users manage own cover letters" on public.cover_letters for all using (auth.uid() = user_id);

-- Auto-create user on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, full_name)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Storage bucket for resumes
insert into storage.buckets (id, name, public)
values ('resumes', 'resumes', false)
on conflict (id) do nothing;

create policy "Users upload own resumes"
  on storage.objects for insert
  with check (bucket_id = 'resumes' and auth.uid()::text = (name split_part(storage.foldername(name), '/', 1)));

create policy "Users view own resumes"
  on storage.objects for select
  using (bucket_id = 'resumes' and auth.uid()::text = (name split_part(storage.foldername(name), '/', 1)));

create policy "Users delete own resumes"
  on storage.objects for delete
  using (bucket_id = 'resumes' and auth.uid()::text = (name split_part(storage.foldername(name), '/', 1)));
```

### Step 5: Enable Auth Providers
In Supabase Dashboard > Authentication > Providers:
- Enable **Email** (allow sign ups)
- Enable **Google OAuth** (optional, for Google login)

### Step 6: Restart Server
```powershell
npm run dev
```

---

## Testing Without Database

If you just want to test the UI, use **Demo Mode**:
1. Go to login page
2. Click "Try Demo Mode"
3. Explore all features with sample data

---

## Stripe Setup (For Payments)

1. Create Stripe account at https://stripe.com
2. Get API keys from Stripe Dashboard > Developers > API keys
3. Create a product in Stripe Dashboard > Products
4. Add webhook URL in Stripe: `https://your-domain.com/api/webhooks/stripe`
5. Get webhook secret from Stripe Dashboard > Developers > Webhooks

Update .env.local:
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
```

---

## Deploy to Vercel

1. Push code to GitHub
2. Connect to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy

Add env vars in Vercel:
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY
- OPENAI_API_KEY
- STRIPE_SECRET_KEY
- STRIPE_WEBHOOK_SECRET
- NEXT_PUBLIC_APP_URL
