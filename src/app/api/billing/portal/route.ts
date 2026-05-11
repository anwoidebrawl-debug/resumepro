import { NextResponse } from 'next/server';

export async function POST() {
  // Demo mode - no Stripe
  if (!process.env.STRIPE_SECRET_KEY) {
    return NextResponse.json({ 
      error: 'Billing requires Stripe configuration' 
    }, { status: 400 });
  }

  return NextResponse.json({ error: 'Stripe not configured' }, { status: 400 });
}
