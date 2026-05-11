import { NextResponse, type NextRequest } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { resumeId, jobDescription } = await request.json();

    // Demo mode - return mock data
    if (!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY.trim() === '') {
      const mockAnalysis = {
        id: `demo-${Date.now()}`,
        user_id: 'demo-user',
        resume_id: resumeId || 'demo-resume',
        ats_score: Math.floor(Math.random() * 30) + 70,
        keyword_match_score: Math.floor(Math.random() * 30) + 65,
        readability_score: Math.floor(Math.random() * 20) + 80,
        formatting_score: Math.floor(Math.random() * 20) + 75,
        impact_score: Math.floor(Math.random() * 25) + 70,
        improvements: [
          {
            type: 'rewrite',
            section: 'Experience',
            original: 'Worked on various projects',
            improved: 'Led cross-functional teams delivering 12+ enterprise projects, resulting in $2M+ cost savings for clients',
            reason: 'Quantifiable achievements significantly improve ATS scores',
          },
          {
            type: 'suggestion',
            section: 'Skills',
            original: '',
            suggestion: 'Add cloud platforms (AWS, GCP) to match job descriptions',
            reason: 'Cloud skills are highly sought after',
          },
        ],
        suggested_skills: ['AWS', 'Docker', 'Kubernetes', 'GraphQL', 'Redis', 'React', 'Node.js', 'TypeScript'],
        weak_sections: ['Skills section could be more specific', 'Missing years of experience in header'],
        overall_feedback: 'Your resume is well-structured with good impact statements. Focus on adding quantifiable metrics and cloud technologies.',
      };
      return NextResponse.json({ analysis: mockAnalysis });
    }

    // Real AI analysis
    const resumeContent = jobDescription || 'Software Engineer with experience in full-stack development, React, Node.js, and cloud technologies. Led development of APIs serving 100k+ users.';

    const prompt = `Analyze this resume/job description for ATS compatibility and provide feedback:

${resumeContent}

Provide a JSON response with:
{
  "ats_score": number (0-100),
  "keyword_match_score": number (0-100),
  "readability_score": number (0-100),
  "formatting_score": number (0-100),
  "impact_score": number (0-100),
  "improvements": [
    {
      "type": "rewrite" | "suggestion" | "warning",
      "section": "string",
      "original": "string",
      "improved": "string (optional)",
      "suggestion": "string (optional)",
      "reason": "string"
    }
  ],
  "suggested_skills": ["skill1", "skill2", ...],
  "weak_sections": ["issue1", "issue2", ...],
  "overall_feedback": "string"
}`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are an expert resume analyst. Provide detailed, actionable feedback.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      response_format: { type: 'json_object' },
    });

    const analysisData = JSON.parse(completion.choices[0].message.content || '{}');

    const analysis = {
      id: `analysis-${Date.now()}`,
      user_id: 'demo-user',
      resume_id: resumeId || 'demo-resume',
      ats_score: analysisData.ats_score || 75,
      keyword_match_score: analysisData.keyword_match_score || 70,
      readability_score: analysisData.readability_score || 80,
      formatting_score: analysisData.formatting_score || 75,
      impact_score: analysisData.impact_score || 75,
      improvements: analysisData.improvements || [],
      suggested_skills: analysisData.suggested_skills || [],
      weak_sections: analysisData.weak_sections || [],
      overall_feedback: analysisData.overall_feedback || 'Analysis complete.',
    };

    return NextResponse.json({ analysis });

  } catch (error: any) {
    console.error('Analysis error:', error);
    return NextResponse.json(
      { error: error.message || 'Analysis failed' },
      { status: 500 }
    );
  }
}
