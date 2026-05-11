import { NextResponse, type NextRequest } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const { jobTitle, companyName, tone, resumeContent } = body;

    const prompt = `Generate a professional cover letter with these details:
- Job Title: ${jobTitle || 'Software Engineer'}
- Company: ${companyName || 'Tech Company'}
- Tone: ${tone || 'professional'}
${resumeContent ? `- Resume Content:\n${resumeContent}` : ''}

Requirements:
1. Start with a strong hook mentioning the specific position
2. Highlight 2-3 most relevant qualifications
3. Show understanding of the company
4. End with clear call to action
5. Approximately 300-400 words
6. NO placeholder brackets like [Your Name]

Return JSON:
{
  "job_title": "the job title",
  "company_name": "the company name",
  "content": "the full cover letter text...",
  "tone": "${tone || 'professional'}"
}`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are an expert cover letter writer. Create compelling, ATS-friendly cover letters.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      response_format: { type: 'json_object' },
    });

    const letterData = JSON.parse(completion.choices[0].message.content || '{}');

    const coverLetter = {
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
    };

    return NextResponse.json({ coverLetter });

  } catch (error: any) {
    console.error('Cover letter error:', error);
    return NextResponse.json(
      { error: error.message || 'Cover letter generation failed' },
      { status: 500 }
    );
  }
}
