import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
  // Check if we have valid Supabase credentials
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  
  // If no valid credentials, return mock client
  if (!supabaseUrl || !supabaseKey || 
      supabaseUrl === 'https://your-project.supabase.co' ||
      supabaseUrl.includes('demo.supabase.co') ||
      !supabaseUrl.startsWith('https://')) {
    return {
      auth: {
        getUser: async () => ({ data: { user: null }, error: null }),
        signInWithPassword: async () => ({ data: null, error: null }),
        signInWithOAuth: async () => ({ data: null, error: null }),
        signUp: async () => ({ data: null, error: null }),
        signOut: async () => ({ error: null }),
      },
      from: () => ({
        select: () => ({ 
          eq: () => ({ 
            single: async () => ({ data: null, error: null }),
            order: () => ({ 
              limit: () => ({ data: [], error: null }) 
            }) 
          }) 
        }),
        insert: async () => ({ data: null, error: null }),
        update: async () => ({ data: null, error: null }),
        delete: async () => ({ data: null, error: null }),
      }),
      storage: {
        from: () => ({
          upload: async () => ({ data: null, error: null }),
          getPublicUrl: () => ({ data: { publicUrl: '' } }),
        }),
      },
    } as any;
  }

  // Use real Supabase client
  return createBrowserClient(supabaseUrl, supabaseKey);
}
