import { NextResponse, type NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  const url = request.nextUrl;
  const pathname = url.pathname;
  
  // Public paths
  const publicPaths = ['/', '/login', '/signup', '/forgot-password', '/pricing', '/contact', '/privacy-policy', '/terms-of-service'];
  const isPublicPath = publicPaths.some(path => pathname === path);
  
  if (isPublicPath) {
    return NextResponse.next();
  }
  
  // Dashboard paths - check for demo cookie or param
  const dashboardPaths = ['/dashboard', '/upload', '/analysis', '/cover-letter', '/linkedin', '/settings', '/billing'];
  const isDashboardPath = dashboardPaths.some(path => pathname.startsWith(path));
  
  if (isDashboardPath) {
    const isDemo = url.searchParams.get('demo') === 'true' || 
                   request.cookies.get('demo_mode')?.value === 'true';
    
    if (isDemo) {
      const response = NextResponse.next();
      response.cookies.set('demo_mode', 'true', {
        path: '/',
        maxAge: 60 * 60 * 24,
        httpOnly: false,
        sameSite: 'lax'
      });
      return response;
    }
    
    // No demo mode - redirect to login
    const redirectUrl = new URL('/login', url);
    redirectUrl.searchParams.set('demo', 'true');
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
