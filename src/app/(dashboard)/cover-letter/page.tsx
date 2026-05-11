'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useDemo } from '@/hooks/use-demo';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Mail,
  Sparkles,
  Loader2,
  Copy,
  Check,
  FileText,
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { formatDate } from '@/lib/utils';
import type { CoverLetter } from '@/types';

export default function CoverLetterPage() {
  const { coverLetters, isDemo, addCoverLetter } = useDemo();
  const [selectedLetter, setSelectedLetter] = useState<CoverLetter | null>(null);
  const [copied, setCopied] = useState(false);
  const [generating, setGenerating] = useState(false);
  
  const [formData, setFormData] = useState({
    jobTitle: '',
    companyName: '',
    tone: 'professional',
  });
  
  useEffect(() => {
    if (isDemo && coverLetters.length > 0 && !selectedLetter) {
      setSelectedLetter(coverLetters[0]);
    }
  }, [isDemo, coverLetters, selectedLetter]);

  const generateCoverLetter = async () => {
    if (!formData.jobTitle || !formData.companyName) {
      toast({ title: 'Error', description: 'Please fill in all required fields', variant: 'destructive' });
      return;
    }

    setGenerating(true);
    try {
      const response = await fetch('/api/cover-letter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Generation failed');
      }

      const data = await response.json();
      
      if (isDemo) {
        addCoverLetter(data.coverLetter);
        setSelectedLetter(data.coverLetter);
      }
      
      toast({ title: 'Success', description: 'Cover letter generated!' });
    } catch (error: any) {
      toast({ title: 'Error', description: 'Generation failed', variant: 'destructive' });
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = async () => {
    if (!selectedLetter) return;
    await navigator.clipboard.writeText(selectedLetter.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({ title: 'Copied', description: 'Cover letter copied to clipboard' });
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold mb-2">Cover Letter Generator</h1>
        <p className="text-muted-foreground">Create professional cover letters tailored to each job</p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="glass">
            <CardHeader>
              <CardTitle>Generate New</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="jobTitle">Job Title</Label>
                <Input
                  id="jobTitle"
                  placeholder="Senior Software Engineer"
                  value={formData.jobTitle}
                  onChange={(e) => setFormData((prev) => ({ ...prev, jobTitle: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company">Company Name</Label>
                <Input
                  id="company"
                  placeholder="Acme Corp"
                  value={formData.companyName}
                  onChange={(e) => setFormData((prev) => ({ ...prev, companyName: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tone">Tone</Label>
                <select
                  id="tone"
                  className="w-full h-11 rounded-xl border border-input bg-background px-4 text-sm"
                  value={formData.tone}
                  onChange={(e) => setFormData((prev) => ({ ...prev, tone: e.target.value }))}
                >
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="formal">Formal</option>
                  <option value="confident">Confident</option>
                </select>
              </div>

              <Button
                onClick={generateCoverLetter}
                disabled={generating}
                className="w-full"
                variant="gradient"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Cover Letter
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
          className="lg:col-span-2"
        >
          {selectedLetter ? (
            <Card className="glass">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{selectedLetter.job_title}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      at {selectedLetter.company_name} • {formatDate(selectedLetter.created_at)}
                    </p>
                  </div>
                  <Button variant="outline" size="icon" onClick={copyToClipboard}>
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="p-6 rounded-xl bg-muted/30">
                  <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                    {selectedLetter.content}
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Badge variant="outline">{selectedLetter.tone} tone</Badge>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="glass">
              <CardContent className="py-16 text-center">
                <Mail className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="text-muted-foreground">
                  Generate your first cover letter to see it here
                </p>
              </CardContent>
            </Card>
          )}

          {coverLetters.length > 1 && (
            <Card className="glass mt-6">
              <CardHeader>
                <CardTitle className="text-lg">Previous Letters</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {coverLetters.slice(1).map((letter) => (
                    <div
                      key={letter.id}
                      onClick={() => setSelectedLetter(letter)}
                      className="p-4 rounded-xl bg-muted/30 hover:bg-muted/50 cursor-pointer transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{letter.job_title}</p>
                          <p className="text-sm text-muted-foreground">
                            at {letter.company_name}
                          </p>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(letter.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>
    </div>
  );
}
