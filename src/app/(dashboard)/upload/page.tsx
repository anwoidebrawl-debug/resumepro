'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useDemo } from '@/hooks/use-demo';
import {
  FileUp,
  FileText,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { formatDate } from '@/lib/utils';
import type { Resume } from '@/types';

export default function UploadPage() {
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [jobDescription, setJobDescription] = useState('');
  const router = useRouter();
  const { resumes, isDemo, addResume, addAnalysis, analyses } = useDemo();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);

    try {
      // Always use demo mode for uploads
      const mockResume: Resume = {
        id: `demo-${Date.now()}`,
        user_id: 'demo-user-1',
        file_name: file.name,
        file_url: 'https://example.com/demo.pdf',
        file_size: file.size,
        parsed_content: `Resume uploaded: ${file.name}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      addResume(mockResume);
      setSelectedResume(mockResume);
      toast({ title: 'Success', description: 'Resume uploaded!' });
    } catch (error: any) {
      toast({ title: 'Error', description: error.message || 'Upload failed', variant: 'destructive' });
    } finally {
      setUploading(false);
    }
  }, [addResume]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  const analyzeResume = async () => {
    if (!selectedResume && analyses.length === 0) {
      toast({ title: 'Error', description: 'Please upload a resume first', variant: 'destructive' });
      return;
    }

    setAnalyzing(true);
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resumeId: selectedResume?.id || 'demo-resume',
          jobDescription: jobDescription || undefined,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Analysis failed');
      }

      const data = await response.json();
      addAnalysis(data.analysis);
      toast({ title: 'Success', description: 'Resume analyzed!' });
      
      setTimeout(() => {
        router.push('/analysis');
      }, 1000);
    } catch (error: any) {
      toast({ title: 'Error', description: error.message || 'Analysis failed', variant: 'destructive' });
    } finally {
      setAnalyzing(false);
    }
  };

  const deleteResume = (id: string) => {
    toast({ title: 'Deleted', description: 'Resume removed' });
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold mb-2">Upload Resume</h1>
        <p className="text-muted-foreground">Upload your resume to get AI-powered analysis</p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2"
        >
          <Card className="glass">
            <CardHeader>
              <CardTitle>Upload Your Resume</CardTitle>
            </CardHeader>
            <CardContent>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200 cursor-pointer ${
                  isDragActive
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <input {...getInputProps()} />
                {uploading ? (
                  <div className="flex flex-col items-center">
                    <Loader2 className="w-12 h-12 mb-4 animate-spin text-primary" />
                    <p className="text-muted-foreground">Uploading...</p>
                  </div>
                ) : (
                  <>
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                      <FileUp className="w-8 h-8 text-primary" />
                    </div>
                    <p className="text-lg font-medium mb-2">
                      {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume'}
                    </p>
                    <p className="text-sm text-muted-foreground mb-4">
                      or click to browse files
                    </p>
                    <Badge variant="outline">PDF or DOCX (max 10MB)</Badge>
                  </>
                )}
              </div>

              {selectedResume && (
                <div className="mt-6 p-4 rounded-xl bg-muted/30">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <FileText className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">{selectedResume.file_name}</p>
                        <p className="text-xs text-muted-foreground">
                          Uploaded {formatDate(selectedResume.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteResume(selectedResume.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <Tabs defaultValue="basic" className="mt-4">
                    <TabsList>
                      <TabsTrigger value="basic">Quick Analysis</TabsTrigger>
                      <TabsTrigger value="with-job">With Job Match</TabsTrigger>
                    </TabsList>
                    <TabsContent value="basic" className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Get an ATS score and general improvement suggestions.
                      </p>
                      <Button
                        onClick={analyzeResume}
                        disabled={analyzing}
                        className="w-full"
                        variant="gradient"
                      >
                        {analyzing ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            Analyzing with AI...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 mr-2" />
                            Analyze with AI
                          </>
                        )}
                      </Button>
                    </TabsContent>
                    <TabsContent value="with-job" className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Get tailored suggestions based on a specific job description.
                      </p>
                      <textarea
                        className="w-full min-h-[120px] rounded-xl border border-input bg-background px-4 py-3 text-sm"
                        placeholder="Paste the job description here..."
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                      />
                      <Button
                        onClick={analyzeResume}
                        disabled={analyzing}
                        className="w-full"
                        variant="gradient"
                      >
                        {analyzing ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 mr-2" />
                            Analyze with Job Match
                          </>
                        )}
                      </Button>
                    </TabsContent>
                  </Tabs>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="glass">
            <CardHeader>
              <CardTitle>Your Resumes</CardTitle>
            </CardHeader>
            <CardContent>
              {resumes.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p className="text-muted-foreground">No resumes uploaded yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {resumes.map((resume) => (
                    <div
                      key={resume.id}
                      onClick={() => setSelectedResume(resume)}
                      className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                        selectedResume?.id === resume.id
                          ? 'bg-primary/10 ring-2 ring-primary'
                          : 'hover:bg-muted/50'
                      }`}
                    >
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <FileText className="w-5 h-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{resume.file_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(resume.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
