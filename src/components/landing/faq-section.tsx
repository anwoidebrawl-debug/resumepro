'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ChevronDown } from 'lucide-react';

const faqs = [
  {
    question: 'What is ATS and why does it matter?',
    answer: 'ATS (Applicant Tracking System) is software used by recruiters to filter and rank job applications. Most large companies use ATS to screen resumes before a human sees them. A high ATS score means your resume passes the initial screening and reaches a real recruiter.',
  },
  {
    question: 'How does the AI analyze my resume?',
    answer: 'Our AI uses GPT-4 to analyze your resume content, structure, formatting, and keywords. It compares your resume against industry standards and job descriptions you provide, then provides specific suggestions for improvement.',
  },
  {
    question: 'What file formats do you support?',
    answer: 'We currently support PDF and DOCX files. Simply upload your resume and our system will parse the content for analysis.',
  },
  {
    question: 'Can I cancel my subscription anytime?',
    answer: 'Yes, you can cancel your Pro subscription anytime. You will retain access to Pro features until the end of your billing period.',
  },
  {
    question: 'How many analyses can I do with the free plan?',
    answer: 'The free plan includes 3 resume analyses per month. Each time you upload and analyze a resume, it counts as one analysis.',
  },
  {
    question: 'Is my resume data secure?',
    answer: 'Absolutely. We use industry-standard encryption and never share your data with third parties. Your resumes are stored securely and can be deleted at any time.',
  },
];

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4"
          >
            Frequently Asked{' '}
            <span className="text-gradient">Questions</span>
          </motion.h2>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.05 }}
            >
              <Card
                className="glass cursor-pointer hover:shadow-md transition-all duration-200"
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{faq.question}</h3>
                    <ChevronDown
                      className={`w-5 h-5 transition-transform duration-200 ${
                        openIndex === index ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                  {openIndex === index && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-4 text-sm text-muted-foreground"
                    >
                      {faq.answer}
                    </motion.p>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
