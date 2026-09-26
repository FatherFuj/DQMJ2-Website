import { createClient } from '@supabase/supabase-js'

export const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
export const supabase = createClient(
    supabaseUrl,
    import.meta.env.VITE_SUPABASE_ANON_KEY
)

export const publicStorageUrl = `${supabaseUrl}/storage/v1/object/public/monster-thumbnails`

console.log('URL:', supabaseUrl)
console.log('KEY:', import.meta.env.VITE_SUPABASE_ANON_KEY)