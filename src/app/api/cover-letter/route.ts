import { NextResponse, type NextRequest } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  let jobTitle = 'Software Engineer';
  let companyName = 'Tech Company';
  let tone = 'professional';
  
  try {
    const body = await request.json().catch(() => ({}));
    jobTitle = body.jobTitle || jobTitle;
    companyName = body.companyName || companyName;
    tone = body.tone || tone;

    if (!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY.trim() === '') {
      return NextResponse.json({
        coverLetter: {
          id: `demo-letter-${Date.now()}`,
          user_id: 'demo-user',
          resume_id: 'demo-resume',
          job_title: jobTitle,
          company_name: companyName,
          job_description: '',
          content: `Dear Hiring Manager,

I am writing to express my strong interest in the ${jobTitle} position at ${companyName}. With my extensive experience in software development, I am confident in my ability to contribute significantly to your team.

Throughout my career, I have successfully delivered multiple high-impact projects, including leading the development of REST APIs serving over 100,000 daily active users.

What excites me most about ${companyName} is your commitment to innovation. I would love to bring my technical skills to contribute to your success.

I welcome the opportunity to discuss how my experience aligns with your team's needs. Thank you for considering my application.

Best regards,
Your Name`,
          tone: tone,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      });
    }

    const prompt = `Write a professional cover letter for ${jobTitle} at ${companyName}. Tone: ${tone}. Return JSON with job_title, company_name, content (300-400 words, no brackets).`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are an expert cover letter writer. Always respond with valid JSON only.' },
        { role: 'user', content: prompt },
      ],
      response_format: { type: 'json_object' },
      max_tokens: 1500,
    });

    const letterData = JSON.parse(completion.choices[0]?.message?.content || '{}');

    return NextResponse.json({
      coverLetter: {
        id: `letter-${Date.now()}`,
        user_id: 'demo-user',
        resume_id: 'demo-resume',
        job_title: letterData.job_title || jobTitle,
        company_name: letterData.company_name || companyName,
        job_description: '',
        content: letterData.content || 'Cover letter content here.',
        tone: letterData.tone || tone,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    });

  } catch (error: any) {
    console.error('Cover letter error:', error);
    return NextResponse.json({
      coverLetter: {
        id: `error-letter-${Date.now()}`,
        user_id: 'demo-user',
        resume_id: 'demo-resume',
        job_title: jobTitle,
        company_name: companyName,
        job_description: '',
        content: 'Cover letter generation failed. Please try again.',
        tone: tone,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    });
  }
}