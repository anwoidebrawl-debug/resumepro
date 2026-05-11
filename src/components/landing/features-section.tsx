'use client';

import { motion } from 'framer-motion';
import { FileText, Brain, Sparkles, Shield, Zap, Clock, Users, BarChart } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Advanced GPT-4 analysis of your resume content, structure, and keywords for maximum ATS compatibility.',
  },
  {
    icon: Sparkles,
    title: 'Smart Rewrites',
    description: 'Automatically rewrite weak bullet points into impactful, action-oriented statements that grab attention.',
  },
  {
    icon: Shield,
    title: 'ATS Optimization',
    description: 'Ensure your resume passes Applicant Tracking Systems with optimized formatting and keyword placement.',
  },
  {
    icon: Zap,
    title: 'Instant Results',
    description: 'Get comprehensive analysis and suggestions in seconds. No more waiting for days to improve your resume.',
  },
  {
    icon: FileText,
    title: 'Cover Letters',
    description: 'Generate professional, tailored cover letters that complement your optimized resume.',
  },
  {
    icon: Users,
    title: 'LinkedIn Optimization',
    description: 'Get AI suggestions for your LinkedIn headline, summary, and skills to match your resume.',
  },
];

export function FeaturesSection() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4"
          >
            Everything You Need to{' '}
            <span className="text-gradient">Stand Out</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            Powerful AI tools designed to transform your job application and help you land more interviews.
          </motion.p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="h-full glass hover:shadow-lg transition-all duration-300 group">
                <CardContent className="p-6">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <feature.icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
