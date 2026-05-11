'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { createClient } from '@/supabase/client';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { FileUp, Sparkles, Target, Check, Loader2 } from 'lucide-react';
import { useEffect } from 'react';

const steps = [
  {
    title: 'Upload Your Resume',
    description: 'Add your resume to get started with AI-powered analysis',
    icon: FileUp,
    action: '/upload',
  },
  {
    title: 'Set Your Goals',
    description: 'Define your target roles and companies',
    icon: Target,
    action: '/dashboard',
  },
  {
    title: 'Start Analyzing',
    description: 'Get your ATS score and improvement suggestions',
    icon: Sparkles,
    action: '/analysis',
  },
];

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [completing, setCompleting] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  const completeOnboarding = async () => {
    setCompleting(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      await supabase
        .from('users')
        .update({ onboarding_completed: true })
        .eq('id', user.id);
    }
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-b from-background via-background to-muted/30">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-2xl relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center gap-2 rounded-full glass px-4 py-2 mb-4">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">Welcome to ResumeIQ</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Let's Get Started</h1>
          <p className="text-muted-foreground">
            Follow these steps to optimize your resume and land more interviews
          </p>
        </motion.div>

        <div className="flex justify-center gap-2 mb-8">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`h-1.5 rounded-full transition-all ${
                index <= currentStep ? 'w-8 bg-primary' : 'w-8 bg-muted'
              }`}
            />
          ))}
        </div>

        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <Card className="glass">
            <CardContent className="p-8">
              <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                {currentStep === 0 && <FileUp className="w-8 h-8 text-primary" />}
                {currentStep === 1 && <Target className="w-8 h-8 text-primary" />}
                {currentStep === 2 && <Sparkles className="w-8 h-8 text-primary" />}
              </div>

              <h2 className="text-2xl font-bold text-center mb-2">
                {steps[currentStep].title}
              </h2>
              <p className="text-muted-foreground text-center mb-8">
                {steps[currentStep].description}
              </p>

              <div className="flex justify-center gap-4">
                {currentStep < steps.length - 1 ? (
                  <Button
                    variant="gradient"
                    size="lg"
                    onClick={() => setCurrentStep(prev => prev + 1)}
                    className="gap-2"
                  >
                    Next Step
                    <Check className="w-4 h-4" />
                  </Button>
                ) : (
                  <Button
                    variant="gradient"
                    size="lg"
                    onClick={completeOnboarding}
                    disabled={completing}
                    className="gap-2"
                  >
                    {completing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Finishing...
                      </>
                    ) : (
                      <>
                        Complete Setup
                        <Check className="w-4 h-4" />
                      </>
                    )}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <div className="flex justify-center gap-4">
          {steps.map((step, index) => (
            <button
              key={index}
              onClick={() => setCurrentStep(index)}
              className={`p-3 rounded-xl transition-all ${
                index === currentStep
                  ? 'bg-primary/10 ring-2 ring-primary'
                  : 'hover:bg-muted/50'
              }`}
            >
              <step.icon className={`w-5 h-5 ${
                index === currentStep ? 'text-primary' : 'text-muted-foreground'
              }`} />
            </button>
          ))}
        </div>

        <p className="text-center text-sm text-muted-foreground mt-6">
          <button
            onClick={completeOnboarding}
            className="text-primary hover:underline"
          >
            Skip setup and go to dashboard
          </button>
        </p>
      </div>
    </div>
  );
}
