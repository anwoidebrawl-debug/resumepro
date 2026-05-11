'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, Sparkles, Zap, Crown } from 'lucide-react';
import Link from 'next/link';

const plans = [
  {
    name: 'Free',
    description: 'Perfect for getting started',
    price: 0,
    features: [
      '3 resume analyses per month',
      'ATS score calculation',
      'Basic keyword suggestions',
      'Email support',
    ],
    notIncluded: [
      'Cover letter generation',
      'LinkedIn optimization',
      'Priority processing',
    ],
    tier: 'free',
    stripePriceId: null,
  },
  {
    name: 'Pro',
    description: 'For serious job seekers',
    price: 19,
    features: [
      'Unlimited resume analyses',
      'Cover letter generation',
      'LinkedIn optimization',
      'Advanced ATS features',
      'Priority processing',
      'Email support',
    ],
    notIncluded: [],
    tier: 'pro',
    stripePriceId: 'price_pro_monthly',
    popular: true,
  },
];

export function PricingSection() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4"
          >
            Simple,{' '}
            <span className="text-gradient">Transparent Pricing</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            Start free, upgrade when you need more power.
          </motion.p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className={plan.popular ? 'relative' : ''}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10">
                  <Badge variant="glow" className="px-4 py-1">
                    <Sparkles className="w-3 h-3 mr-1" />
                    Most Popular
                  </Badge>
                </div>
              )}
              <Card className={`h-full glass ${plan.popular ? 'border-primary shadow-lg shadow-primary/10' : ''}`}>
                <CardHeader className="text-center pb-2">
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="text-center">
                  <div className="mb-6">
                    <span className="text-5xl font-bold">
                      ${plan.price}
                    </span>
                    {plan.price > 0 && (
                      <span className="text-muted-foreground">/month</span>
                    )}
                  </div>
                  <ul className="space-y-3 text-left">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm">
                        <Check className="w-4 h-4 text-green-500 shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                    {plan.notIncluded.map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm text-muted-foreground/50">
                        <span className="w-4 h-4 shrink-0">—</span>
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter className="pt-0">
                  <Link href="/signup" className="w-full">
                    <Button
                      className={`w-full ${plan.popular ? 'variant-gradient' : 'variant-outline'}`}
                      variant={plan.popular ? 'gradient' : 'outline'}
                    >
                      {plan.price === 0 ? 'Get Started Free' : 'Start Pro Trial'}
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            </motion.div>
          ))}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center text-sm text-muted-foreground mt-8"
        >
          No credit card required for free tier. Cancel anytime.
        </motion.p>
      </div>
    </section>
  );
}
