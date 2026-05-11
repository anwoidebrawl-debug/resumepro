import { NextResponse, type NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  const url = request.nextUrl;
  const pathname = url.pathname;
  
  // Allow all routes in demo mode
  const isDemo = url.searchParams.get('demo') === 'true';
  
  if (isDemo) {
    return NextResponse.next();
  }
  
  // Public paths
  const publicPaths = ['/', '/login', '/signup', '/pricing', '/contact', '/privacy-policy', '/terms-of-service'];
  const isPublicPath = publicPaths.some(path => pathname === path);
  
  if (isPublicPath) {
    return NextResponse.next();
  }
  
  // Dashboard paths need demo mode
  const dashboardPaths = ['/dashboard', '/upload', '/analysis', '/cover-letter', '/linkedin', '/settings', '/billing'];
  const isDashboardPath = dashboardPaths.some(path => pathname.startsWith(path));
  
  if (isDashboardPath) {
    const redirectUrl = new URL('/login', url);
    redirectUrl.searchParams.set('demo', 'true');
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};