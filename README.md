# ResumeIQ AI

AI-Powered Resume Optimizer - Get more interviews with AI-optimized resumes.

![ResumeIQ AI](https://img.shields.io/badge/Next.js-15-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-cyan)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **AI Resume Analysis** - GPT-4 powered analysis with ATS scoring
- **Cover Letter Generator** - AI-generated professional cover letters
- **LinkedIn Optimizer** - Profile optimization suggestions
- **ATS Score Calculation** - Keyword matching, readability, formatting, impact scoring
- **Stripe Subscriptions** - Free and Pro tiers
- **Modern UI** - Glassmorphism, dark/light mode, smooth animations

## Tech Stack

- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Supabase (Auth, Database, Storage), Next.js API Routes
- **AI**: OpenAI GPT-4 API
- **Payments**: Stripe
- **Deployment**: Vercel

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account
- OpenAI API key
- Stripe account

### Environment Variables

Create a `.env.local` file in the root directory:

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Stripe
STRIPE_SECRET_KEY=sk_test_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Database Setup

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Create a new project
3. Run the SQL schema from `supabase/schema.sql` in the SQL Editor
4. Enable Storage and create a bucket named `resumes`

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/resumepro.git
cd resumepro

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy

### Stripe Setup

1. Create a Stripe account
2. Create a product in Stripe Dashboard
3. Copy the Price ID to `STRIPE_PRO_MONTHLY_PRICE_ID`
4. Set up webhook endpoint pointing to `/api/webhooks/stripe`

### Supabase Setup

1. Create project at supabase.com
2. Run `supabase/schema.sql` in SQL Editor
3. Enable Email auth and Google OAuth in Authentication settings
4. Create storage bucket `resumes`

## Project Structure

```
resumepro/
├── src/
│   ├── app/
│   │   ├── (auth)/           # Auth pages
│   │   ├── (dashboard)/      # Dashboard pages
│   │   ├── (admin)/          # Admin pages
│   │   ├── api/              # API routes
│   │   └── ...               # Public pages
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   ├── landing/           # Landing page components
│   │   ├── dashboard/         # Dashboard components
│   │   └── auth/              # Auth components
│   ├── lib/
│   │   ├── utils.ts           # Utility functions
│   │   └── ...
│   ├── hooks/                # Custom React hooks
│   ├── types/                # TypeScript types
│   └── supabase/             # Supabase clients
├── supabase/
│   └── schema.sql            # Database schema
└── ...
```

## API Routes

- `POST /api/analyze` - Analyze resume and generate ATS score
- `POST /api/cover-letter` - Generate cover letter
- `POST /api/linkedin` - Optimize LinkedIn profile
- `POST /api/billing/checkout` - Create Stripe checkout session
- `POST /api/billing/portal` - Open Stripe billing portal
- `POST /api/webhooks/stripe` - Handle Stripe webhooks

## Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
npm run typecheck # Run TypeScript check
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

For support, email support@resumepro.ai or create an issue on GitHub.
