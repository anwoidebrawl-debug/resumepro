import { NextResponse, type NextRequest } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const { jobTitle, companyName, tone } = body;

    // Check if OpenAI is configured
    if (!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY.trim() === '') {
      return NextResponse.json({
        coverLetter: {
          id: `demo-letter-${Date.now()}`,
          user_id: 'demo-user',
          resume_id: 'demo-resume',
          job_title: jobTitle || 'Senior Software Engineer',
          company_name: companyName || 'Tech Company',
          job_description: '',
          content: `Dear Hiring Manager,

I am writing to express my strong interest in the ${jobTitle || 'position'} at ${companyName || 'your company'}. With my extensive experience in software development, I am confident in my ability to contribute significantly to your team.

Throughout my career, I have successfully delivered multiple high-impact projects, including leading the development of REST APIs serving over 100,000 daily active users. My expertise spans React, Node.js, Python, and cloud technologies.

What excites me most about ${companyName || 'your company'} is your commitment to innovation. I would love to bring my technical skills to contribute to your success.

I welcome the opportunity to discuss how my experience aligns with your team's needs. Thank you for considering my application.

Best regards,
Your Name`,
          tone: tone || 'professional',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      });
    }

    const prompt = `Write a professional cover letter. Respond ONLY with valid JSON:

{
  "job_title": "the job title",
  "company_name": "the company name",
  "content": "the full cover letter text (300-400 words, no placeholder brackets)",
  "tone": "the tone used"
}

Details:
- Job Title: ${jobTitle || 'Software Engineer'}
- Company: ${companyName || 'Tech Company'}
- Tone: ${tone || 'professional'}

Requirements:
1. Strong opening hook mentioning the position
2. 2-3 relevant qualifications with metrics
3. Show knowledge of the company
4. Clear call to action
5. NO brackets like [Your Name]`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',  // Text-only model
      messages: [
        {
          role: 'system',
          content: 'You are an expert cover letter writer. Always respond with valid JSON only.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      response_format: { type: 'json_object' },
      max_tokens: 1500,
    });

    const content = completion.choices[0]?.message?.content || '{}';
    const letterData = JSON.parse(content);

    return NextResponse.json({
      coverLetter: {
        id: `letter-${Date.now()}`,
        user_id: 'demo-user',
        resume_id: 'demo-resume',
        job_title: letterData.job_title || jobTitle || 'Software Engineer',
        company_name: letterData.company_name || companyName || 'Tech Company',
        job_description: '',
        content: letterData.content || 'Cover letter content here.',
        tone: letterData.tone || tone || 'professional',
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
        job_title: jobTitle || 'Software Engineer',
        company_name: companyName || 'Tech Company',
        job_description: '',
        content: 'Cover letter generation failed. Please try again.',
        tone: 'professional',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    });
  }
}
