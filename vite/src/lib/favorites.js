export const FAVORITE_STORAGE_KEY = 'dqmj2-favorite-monsters'

function normalizeMonsterId(value) {
    const numericValue = Number(value)
    return Number.isInteger(numericValue) && numericValue > 0 ? numericValue : null
}

export function getFavoriteIds() {
    try {
        const stored = localStorage.getItem(FAVORITE_STORAGE_KEY)
        const parsed = stored ? JSON.parse(stored) : []

        if (!Array.isArray(parsed)) {
            return []
        }

        return [...new Set(parsed.map(normalizeMonsterId).filter((value) => value !== null))]
    } catch (error) {
        console.error('Unable to read favorite monsters:', error)
        return []
    }
}

export function setFavoriteIds(ids) {
    const normalized = [...new Set(ids.map(normalizeMonsterId).filter((value) => value !== null))]
    localStorage.setItem(FAVORITE_STORAGE_KEY, JSON.stringify(normalized))
    return normalized
}

export function toggleFavorite(monsterId) {
    const id = normalizeMonsterId(monsterId)

    if (id === null) {
        return false
    }

    const current = getFavoriteIds()
    const hasFavorite = current.includes(id)
    const updated = hasFavorite ? current.filter((favoriteId) => favoriteId !== id) : [...current, id]
    setFavoriteIds(updated)
    return !hasFavorite
}

export function isFavorite(monsterId) {
    const id = normalizeMonsterId(monsterId)
    return id !== null && getFavoriteIds().includes(id)
}
