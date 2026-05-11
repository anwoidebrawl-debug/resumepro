'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useDemo } from '@/hooks/use-demo';
import { DEMO_ANALYSES, DEMO_RESUMES } from '@/lib/demo';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText,
  Sparkles,
  Target,
  AlertTriangle,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { formatDate, getATSScoreGrade } from '@/lib/utils';
import type { Analysis } from '@/types';

export default function AnalysisPage() {
  const { analyses, resumes, isDemo } = useDemo();
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);

  useEffect(() => {
    if (isDemo && analyses.length > 0) {
      setSelectedAnalysis(analyses[0]);
    }
  }, [isDemo, analyses]);

  useEffect(() => {
    if (analyses.length > 0 && !selectedAnalysis) {
      setSelectedAnalysis(analyses[0]);
    }
  }, [analyses, selectedAnalysis]);

  if (!isDemo && analyses.length === 0) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16"
        >
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
            <FileText className="w-10 h-10 text-primary" />
          </div>
          <h1 className="text-2xl font-bold mb-2">No Analyses Yet</h1>
          <p className="text-muted-foreground mb-6">
            Upload a resume to get your first ATS analysis
          </p>
          <Link href="/upload">
            <Button variant="gradient" className="gap-2">
              <Sparkles className="w-4 h-4" />
              Upload & Analyze
            </Button>
          </Link>
        </motion.div>
      </div>
    );
  }

  const getResumeName = (resumeId: string) => {
    const allResumes = [...DEMO_RESUMES, ...resumes];
    const resume = allResumes.find((r) => r.id === resumeId);
    return resume?.file_name || 'Resume';
  };

  const scoreGrade = selectedAnalysis ? getATSScoreGrade(selectedAnalysis.ats_score) : null;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold mb-2">Analysis Results</h1>
        <p className="text-muted-foreground">View your ATS compatibility scores and suggestions</p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-lg">Recent Analyses</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analyses.map((analysis) => (
                  <div
                    key={analysis.id}
                    onClick={() => setSelectedAnalysis(analysis)}
                    className={`p-4 rounded-xl cursor-pointer transition-all ${
                      selectedAnalysis?.id === analysis.id
                        ? 'bg-primary/10 ring-2 ring-primary'
                        : 'hover:bg-muted/50'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          analysis.ats_score >= 75
                            ? 'bg-green-500'
                            : analysis.ats_score >= 50
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                      />
                      <span className="font-semibold">{analysis.ats_score}</span>
                      <span className="text-sm text-muted-foreground">ATS Score</span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {getResumeName(analysis.resume_id)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(analysis.created_at)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {selectedAnalysis && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2 space-y-6"
          >
            <Card className="glass">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold">ATS Score</h2>
                    <p className="text-muted-foreground">{getResumeName(selectedAnalysis.resume_id)}</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-5xl font-bold ${scoreGrade?.color}`}>
                      {selectedAnalysis.ats_score}
                    </div>
                    <Badge
                      variant={
                        selectedAnalysis.ats_score >= 75
                          ? 'success'
                          : selectedAnalysis.ats_score >= 50
                          ? 'warning'
                          : 'destructive'
                      }
                    >
                      {scoreGrade?.grade}
                    </Badge>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-4 mb-6">
                  <div className="p-4 rounded-xl bg-muted/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-4 h-4 text-primary" />
                      <span className="text-sm font-medium">Keyword Match</span>
                    </div>
                    <p className="text-2xl font-bold">{selectedAnalysis.keyword_match_score}%</p>
                    <Progress value={selectedAnalysis.keyword_match_score} className="mt-2" />
                  </div>
                  <div className="p-4 rounded-xl bg-muted/30">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4 text-blue-500" />
                      <span className="text-sm font-medium">Readability</span>
                    </div>
                    <p className="text-2xl font-bold">{selectedAnalysis.readability_score}%</p>
                    <Progress value={selectedAnalysis.readability_score} className="mt-2" />
                  </div>
                  <div className="p-4 rounded-xl bg-muted/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-green-500" />
                      <span className="text-sm font-medium">Formatting</span>
                    </div>
                    <p className="text-2xl font-bold">{selectedAnalysis.formatting_score}%</p>
                    <Progress value={selectedAnalysis.formatting_score} className="mt-2" />
                  </div>
                  <div className="p-4 rounded-xl bg-muted/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-purple-500" />
                      <span className="text-sm font-medium">Impact</span>
                    </div>
                    <p className="text-2xl font-bold">{selectedAnalysis.impact_score}%</p>
                    <Progress value={selectedAnalysis.impact_score} className="mt-2" />
                  </div>
                </div>

                <p className="text-sm text-muted-foreground">{selectedAnalysis.overall_feedback}</p>
              </CardContent>
            </Card>

            <Tabs defaultValue="improvements">
              <TabsList>
                <TabsTrigger value="improvements">Improvements</TabsTrigger>
                <TabsTrigger value="skills">Suggested Skills</TabsTrigger>
                <TabsTrigger value="weak">Weak Sections</TabsTrigger>
              </TabsList>

              <TabsContent value="improvements" className="mt-4">
                <Card className="glass">
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      {selectedAnalysis.improvements.map((improvement, index) => (
                        <div
                          key={index}
                          className={`p-4 rounded-xl ${
                            improvement.type === 'warning'
                              ? 'bg-yellow-500/10'
                              : 'bg-muted/30'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            {improvement.type === 'warning' ? (
                              <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
                            ) : (
                              <Sparkles className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                            )}
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <Badge variant="outline" className="text-xs">
                                  {improvement.section}
                                </Badge>
                                <Badge
                                  variant={
                                    improvement.type === 'rewrite'
                                      ? 'default'
                                      : improvement.type === 'warning'
                                      ? 'warning'
                                      : 'secondary'
                                  }
                                  className="text-xs"
                                >
                                  {improvement.type}
                                </Badge>
                              </div>
                              <p className="text-sm font-medium mb-2">{improvement.reason}</p>
                              {improvement.original && (
                                <div className="mb-2">
                                  <p className="text-xs text-muted-foreground mb-1">Original:</p>
                                  <p className="text-sm bg-background/50 p-2 rounded-lg">
                                    {improvement.original}
                                  </p>
                                </div>
                              )}
                              {improvement.improved && (
                                <div>
                                  <p className="text-xs text-muted-foreground mb-1">Improved:</p>
                                  <p className="text-sm bg-primary/10 p-2 rounded-lg">
                                    {improvement.improved}
                                  </p>
                                </div>
                              )}
                              {improvement.suggestion && !improvement.improved && (
                                <p className="text-sm bg-primary/10 p-2 rounded-lg">
                                  {improvement.suggestion}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="skills" className="mt-4">
                <Card className="glass">
                  <CardContent className="p-6">
                    <div className="flex flex-wrap gap-2">
                      {selectedAnalysis.suggested_skills.map((skill, index) => (
                        <Badge key={index} variant="glow">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="weak" className="mt-4">
                <Card className="glass">
                  <CardContent className="p-6">
                    <ul className="space-y-3">
                      {selectedAnalysis.weak_sections.map((section, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-1" />
                          <span className="text-sm">{section}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            <div className="flex gap-4">
              <Link href="/upload" className="flex-1">
                <Button variant="outline" className="w-full gap-2">
                  <FileText className="w-4 h-4" />
                  Analyze Another Resume
                </Button>
              </Link>
              <Link href="/cover-letter" className="flex-1">
                <Button variant="gradient" className="w-full gap-2">
                  Generate Cover Letter
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
