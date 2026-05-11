'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Star, Quote } from 'lucide-react';

const testimonials = [
  {
    name: 'Sarah Chen',
    role: 'Software Engineer',
    company: 'Google',
    avatar: 'SC',
    content: 'After using ResumeIQ, my ATS score went from 65 to 94. I started getting interviews within a week. The AI suggestions were incredibly helpful for highlighting my achievements.',
    rating: 5,
  },
  {
    name: 'Michael Rodriguez',
    role: 'Product Manager',
    company: 'Airbnb',
    avatar: 'MR',
    content: 'The cover letter generator saved me hours of work. Each letter sounds authentic and professional. Landed my dream role at Airbnb!',
    rating: 5,
  },
  {
    name: 'Emily Watson',
    role: 'Data Analyst',
    company: 'Microsoft',
    avatar: 'EW',
    content: 'As a career switcher, I struggled with formatting my resume for tech roles. ResumeIQ helped me structure everything perfectly and I got hired as a Data Analyst.',
    rating: 5,
  },
  {
    name: 'David Kim',
    role: 'Frontend Developer',
    company: 'Stripe',
    avatar: 'DK',
    content: 'The keyword optimization feature is incredible. My resume now consistently passes ATS screening for senior frontend positions.',
    rating: 5,
  },
];

export function TestimonialsSection() {
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
            Loved by{' '}
            <span className="text-gradient">Job Seekers</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            Join thousands who have transformed their job applications with ResumeIQ.
          </motion.p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="h-full glass hover:shadow-lg transition-all duration-300">
                <CardContent className="p-6">
                  <div className="flex gap-1 mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <Quote className="w-6 h-6 text-primary/30 mb-4" />
                  <p className="text-sm mb-4 leading-relaxed">{testimonial.content}</p>
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback>{testimonial.avatar}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium text-sm">{testimonial.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {testimonial.role} at {testimonial.company}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
