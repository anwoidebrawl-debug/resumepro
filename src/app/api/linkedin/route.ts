import { NextResponse, type NextRequest } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));
    const { currentHeadline, currentAbout, targetRole } = body;

    const prompt = `Optimize this LinkedIn profile for maximum impact:

${currentHeadline ? `Current Headline:\n${currentHeadline}\n\n` : ''}
${currentAbout ? `Current About Section:\n${currentAbout}\n\n` : ''}
${targetRole ? `Target Role:\n${targetRole}\n` : ''}

Provide:
1. An optimized headline (under 220 chars, keywords near start)
2. An optimized about section with opening hook, achievements, skills, call to action
3. Suggested skills to add
4. Specific improvements to make

Return JSON:
{
  "headline": "Optimized headline...",
  "about_section": "Optimized about section...",
  "suggested_skills": ["skill1", "skill2", ...],
  "improvements": ["improvement1", "improvement2", ...]
}`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are a LinkedIn profile optimization expert. Create punchy, recruiter-friendly content.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      response_format: { type: 'json_object' },
    });

    const optimizationData = JSON.parse(completion.choices[0].message.content || '{}');

    return NextResponse.json({
      optimization: {
        headline: optimizationData.headline || 'Senior Software Engineer | Full-Stack Development',
        about_section: optimizationData.about_section || 'About section content.',
        suggested_skills: optimizationData.suggested_skills || ['React', 'Node.js'],
        improvements: optimizationData.improvements || [],
      },
    });

  } catch (error: any) {
    console.error('LinkedIn optimization error:', error);
    return NextResponse.json(
      { error: error.message || 'LinkedIn optimization failed' },
      { status: 500 }
    );
  }
}
