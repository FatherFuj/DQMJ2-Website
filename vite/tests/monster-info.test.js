import { describe, expect, it } from 'vitest'
import { parseMonsterInfo } from '../src/lib/monster-info.js'
import recipeSource from '../src/lib/dqmj2-special-recipes.json'

describe('monster info parser', () => {
    it('parses database fields and normalizes list-like values', () => {
        const info = parseMonsterInfo({
            name_en: 'Demo monster',
            family: 'Dragon',
            rank: 'A',
            size: 'L',
            innate_skill: 'Dragon Lore',
            trait_1: 'Attack Boost',
            trait2: 'Immune to sleep',
            scout_locations: 'Albatross; Ice Cave'
        })

        expect(info).toEqual({
            innateSkills: ['Dragon Lore'],
            traits: ['Attack Boost', 'Immune to sleep'],
            family: ['Dragon'],
            rank: ['A'],
            size: ['L'],
            primarySynthesis: [],
            scoutLocations: ['Albatross', 'Ice Cave'],
            scoutable: null,
            normalSynthesis: null
        })
    })

    it('uses the special recipe source when a monster has a special synthesis', () => {
        const info = parseMonsterInfo({ name_en: 'Frou-fry' }, recipeSource)

        expect(info.primarySynthesis).toContainEqual({
            parents: ['Argon lizard', 'Beast (family)']
        })
    })

    it('prefers a monster-provided synthesis recipe over the special recipe fallback', () => {
        const info = parseMonsterInfo({
            name_en: 'Frou-fry',
            primary_synthesis: 'Argon lizard + Dragon'
        }, recipeSource)

        expect(info.primarySynthesis).toEqual(['Argon lizard + Dragon'])
    })

    it('parses source scouting and normal-synthesis availability', () => {
        const info = parseMonsterInfo({
            name_en: 'Slime',
            scoutable: true,
            normal_synthesis: false,
            scout_locations: ['Albatross (Day)', 'Treepidation (Day, Clear)']
        })

        expect(info.scoutable).toBe(true)
        expect(info.normalSynthesis).toBe(false)
        expect(info.scoutLocations).toEqual(['Albatross (Day)', 'Treepidation (Day, Clear)'])
    })
})
