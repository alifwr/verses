import { createClient, type SupabaseClient } from '@supabase/supabase-js'

let client: SupabaseClient | null = null

export function useSupabaseClient(): SupabaseClient {
  if (client) return client

  const config = useRuntimeConfig()
  client = createClient(config.public.supabaseUrl, config.public.supabaseAnonKey)
  return client
}
