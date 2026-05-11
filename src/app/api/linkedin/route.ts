import { NextResponse, type NextRequest } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  let currentHeadline = '';
  let currentAbout = '';
  let targetRole = '';
  
  try {
    const body = await request.json().catch(() => ({}));
    currentHeadline = body.currentHeadline || '';
    currentAbout = body.currentAbout || '';
    targetRole = body.targetRole || '';

    if (!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY.trim() === '') {
      return NextResponse.json({
        optimization: {
          headline: currentHeadline || 'Senior Software Engineer | Full-Stack Development | React • Node.js • TypeScript',
          about_section: currentAbout || `Software Engineer passionate about building clean, efficient code.

With 5+ years in the industry, I've helped companies scale from thousands to millions of users. I've led teams delivering 15+ enterprise projects.

My toolkit includes React, Node.js, TypeScript, AWS. I thrive in agile environments where innovation drives results.

Currently seeking opportunities to build performant, user-centric applications.`,
          suggested_skills: ['React', 'Node.js', 'TypeScript', 'AWS', 'Docker', 'PostgreSQL', 'GraphQL'],
          improvements: [
            'Add quantifiable achievements to about section',
            'Include keywords near the start of headline',
            'Add 2-3 relevant certifications',
          ],
        },
      });
    }

    const prompt = `Optimize this LinkedIn profile. Return JSON with headline, about_section, suggested_skills, improvements.${currentHeadline ? ` Headline: ${currentHeadline}` : ''}${currentAbout ? ` About: ${currentAbout}` : ''}${targetRole ? ` Target: ${targetRole}` : ''}`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a LinkedIn optimization expert. Always respond with valid JSON only.' },
        { role: 'user', content: prompt },
      ],
      response_format: { type: 'json_object' },
      max_tokens: 1500,
    });

    const optimizationData = JSON.parse(completion.choices[0]?.message?.content || '{}');

    return NextResponse.json({
      optimization: {
        headline: optimizationData.headline || 'Senior Software Engineer',
        about_section: optimizationData.about_section || 'About section here.',
        suggested_skills: optimizationData.suggested_skills || ['React', 'Node.js'],
        improvements: optimizationData.improvements || [],
      },
    });

  } catch (error: any) {
    console.error('LinkedIn error:', error);
    return NextResponse.json({
      optimization: {
        headline: currentHeadline || 'Senior Software Engineer',
        about_section: currentAbout || 'About section.',
        suggested_skills: ['React', 'Node.js', 'TypeScript'],
        improvements: ['Add metrics to achievements'],
      },
    });
  }
}