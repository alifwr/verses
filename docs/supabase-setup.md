# Supabase Setup Guide

## 1. Create Supabase Project

1. Go to https://supabase.com and create a new project
2. Note down:
   - Project URL (e.g., `https://xxxx.supabase.co`)
   - Anon/public key (from Settings > API)
   - JWT Secret (from Settings > API > JWT Settings)
   - Database connection string (from Settings > Database > Connection string > URI)

## 2. Enable Google Auth

1. In Supabase dashboard: Authentication > Providers > Google
2. Enable Google provider
3. Add your Google OAuth client ID and secret
   - Create these at https://console.cloud.google.com/apis/credentials
   - Authorized redirect URI: `https://<your-supabase-url>/auth/v1/callback`
4. Save

## 3. Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_JWT_SECRET=<jwt-secret>
BACKEND_CORS_ORIGINS=http://localhost:3742,https://verse.alifpunya.com
NUXT_PUBLIC_API_BASE=https://verse-api.alifpunya.com
TUNNEL_TOKEN=<cloudflare-tunnel-token>
```

## 4. Google Cloud Console

1. Create OAuth 2.0 Client ID (Web application)
2. Authorized JavaScript origins: your frontend URL
3. Authorized redirect URIs: `https://<supabase-url>/auth/v1/callback`
