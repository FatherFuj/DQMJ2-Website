import { describe, it, expect } from 'vitest'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

async function getLiveMonsterSummary() {
  const response = await fetch(`${supabaseUrl}/rest/v1/dqmj2_monsters?select=monster_id,name_en,family,rank,size,name_jp&limit=1`, {
    headers: {
      apikey: supabaseAnonKey,
      Authorization: `Bearer ${supabaseAnonKey}`,
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`Supabase request failed: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

describe('Supabase live contract', () => {
  it('is configured with a valid Supabase URL and anon key', () => {
    expect(supabaseUrl).toBeTruthy()
    expect(supabaseAnonKey).toBeTruthy()
    expect(supabaseUrl).toMatch(/^https:\/\/[a-z0-9-]+\.supabase\.co$/i)
  })

  it('exposes the expected monster table columns', async () => {
    const rows = await getLiveMonsterSummary()
    expect(Array.isArray(rows)).toBe(true)
    expect(rows.length).toBeGreaterThan(0)

    const monster = rows[0]
    expect(monster).toHaveProperty('monster_id')
    expect(monster).toHaveProperty('name_en')
    expect(monster).toHaveProperty('family')
    expect(monster).toHaveProperty('rank')
    expect(monster).toHaveProperty('size')
    expect(monster).toHaveProperty('name_jp')
    expect(monster).not.toHaveProperty('id')
  })
})
