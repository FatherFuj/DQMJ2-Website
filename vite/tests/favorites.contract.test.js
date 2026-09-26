import { describe, it, expect } from 'vitest'
import { getFavoriteIds, setFavoriteIds, toggleFavorite, isFavorite } from '../src/lib/favorites.js'

describe('favorites contract', () => {
  it('stores favorite monster IDs using the DB primary key field contract', () => {
    setFavoriteIds([1, 2, 3])

    expect(getFavoriteIds()).toEqual([1, 2, 3])
    expect(localStorage.getItem('dqmj2-favorite-monsters')).toBe(JSON.stringify([1, 2, 3]))
  })

  it('switches favorite state without duplicating IDs', () => {
    expect(toggleFavorite(7)).toBe(true)
    expect(toggleFavorite(7)).toBe(false)
    expect(isFavorite(7)).toBe(false)
    expect(getFavoriteIds()).toEqual([])
  })

  it('handles non-numeric or duplicate IDs safely', () => {
    setFavoriteIds([1, '2', 2, NaN, undefined, null])
    expect(getFavoriteIds()).toEqual([1, 2])
    expect(isFavorite(2)).toBe(true)
    expect(isFavorite(99)).toBe(false)
  })
})
