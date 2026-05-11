'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { createClient } from '@/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Linkedin,
  Sparkles,
  Loader2,
  Copy,
  Check,
  FileText,
  User,
  Award,
  Lightbulb,
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

export default function LinkedInPage() {
  const [optimizing, setOptimizing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);
  const [optimization, setOptimization] = useState<{
    headline: string;
    about_section: string;
    suggested_skills: string[];
    improvements: string[];
  } | null>(null);
  
  const [formData, setFormData] = useState({
    currentHeadline: '',
    currentAbout: '',
    targetRole: '',
  });
  
  const supabase = createClient();

  useEffect(() => {
    setLoading(false);
  }, []);

  const optimizeLinkedIn = async () => {
    if (!formData.currentHeadline && !formData.currentAbout) {
      toast({ title: 'Error', description: 'Please provide your current headline or about section', variant: 'destructive' });
      return;
    }

    setOptimizing(true);
    try {
      const response = await fetch('/api/linkedin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Optimization failed');
      }

      const data = await response.json();
      setOptimization(data.optimization);
      toast({ title: 'Success', description: 'LinkedIn profile optimized!' });
    } catch (error: any) {
      toast({ title: 'Error', description: error.message || 'Optimization failed', variant: 'destructive' });
    } finally {
      setOptimizing(false);
    }
  };

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(field);
    setTimeout(() => setCopied(null), 2000);
    toast({ title: 'Copied', description: `${field} copied to clipboard` });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold mb-2">LinkedIn Optimizer</h1>
        <p className="text-muted-foreground">Enhance your LinkedIn profile to attract recruiters</p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="glass">
            <CardHeader>
              <CardTitle>Your Current Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="headline">Current Headline</Label>
                <Input
                  id="headline"
                  placeholder="Software Engineer at XYZ Corp"
                  value={formData.currentHeadline}
                  onChange={(e) => setFormData((prev) => ({ ...prev, currentHeadline: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="about">Current About Section</Label>
                <textarea
                  id="about"
                  className="w-full min-h-[150px] rounded-xl border border-input bg-background px-4 py-3 text-sm"
                  placeholder="Paste your current About section here..."
                  value={formData.currentAbout}
                  onChange={(e) => setFormData((prev) => ({ ...prev, currentAbout: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="target">Target Role (Optional)</Label>
                <Input
                  id="target"
                  placeholder="Senior Frontend Developer"
                  value={formData.targetRole}
                  onChange={(e) => setFormData((prev) => ({ ...prev, targetRole: e.target.value }))}
                />
              </div>

              <Button
                onClick={optimizeLinkedIn}
                disabled={optimizing}
                className="w-full"
                variant="gradient"
              >
                {optimizing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Optimizing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Optimize LinkedIn
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          {optimization ? (
            <>
              <Card className="glass">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <User className="w-5 h-5 text-primary" />
                      <CardTitle>Optimized Headline</CardTitle>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(optimization.headline, 'headline')}
                    >
                      {copied === 'headline' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="p-4 rounded-xl bg-primary/10">
                    <p className="font-medium">{optimization.headline}</p>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-primary" />
                      <CardTitle>Optimized About Section</CardTitle>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(optimization.about_section, 'about')}
                    >
                      {copied === 'about' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="p-4 rounded-xl bg-muted/30 whitespace-pre-wrap text-sm">
                    {optimization.about_section}
                  </div>
                </CardContent>
              </Card>

              <Card className="glass">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Award className="w-5 h-5 text-primary" />
                    <CardTitle>Suggested Skills</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {optimization.suggested_skills.map((skill, index) => (
                      <Badge key={index} variant="glow">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="glass">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-primary" />
                    <CardTitle>Improvements</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {optimization.improvements.map((improvement, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <Sparkles className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                        <span>{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="glass">
              <CardContent className="py-16 text-center">
                <Linkedin className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="text-muted-foreground">
                  Enter your current LinkedIn info to get optimization suggestions
                </p>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>
    </div>
  );
}
