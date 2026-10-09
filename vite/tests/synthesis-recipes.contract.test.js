import { describe, it, expect } from 'vitest'
import specialRecipeSource from '../src/lib/dqmj2-special-recipes.json'

describe('special synthesis recipe source', () => {
  it('includes the complete sourced recipe list and supported parent counts', () => {
    expect(specialRecipeSource.source).toBe('https://rebjorn-wiki.com/dqmj2/synthesis/special')
    expect(specialRecipeSource.recipes).toHaveLength(223)
    expect(specialRecipeSource.recipes.every(recipe => [2, 4].includes(recipe.parents.length))).toBe(true)
    expect(specialRecipeSource.recipes.filter(recipe => recipe.parents.length === 4)).toHaveLength(33)
  })

  it('preserves the Alabast dragon recipe and family constraints', () => {
    const alabastDragonRecipe = specialRecipeSource.recipes.find(recipe => recipe.result === 'Alabast dragon')

    expect(alabastDragonRecipe.parents.map(parent => parent.name)).toEqual(['Mechanowyrm', 'Drakulard'])
    expect(specialRecipeSource.recipes.flatMap(recipe => recipe.parents).filter(parent => parent.type === 'family')).toHaveLength(31)
    expect(specialRecipeSource.recipes.flatMap(recipe => recipe.parents).filter(parent => parent.type === 'unknown-family')).toHaveLength(8)
  })
})
