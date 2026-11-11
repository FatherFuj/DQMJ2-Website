function normalizeName(value) {
    return String(value ?? '')
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '')
}

function getFirstValue(record, keys) {
    for (const key of keys) {
        const value = record?.[key]
        if (value !== undefined && value !== null && value !== '') {
            return value
        }
    }

    return null
}

function displayValue(value) {
    if (value === null || value === undefined || value === '') {
        return []
    }

    if (Array.isArray(value)) {
        return value.flatMap(displayValue)
    }

    if (typeof value === 'object') {
        const name = value.name ?? value.label ?? value.value
        if (name !== undefined) {
            return displayValue(name)
        }

        if (Array.isArray(value.parents)) {
            return value.parents.map(parent => {
                if (typeof parent === 'string') {
                    return parent
                }

                const parentName = parent.name ?? parent.family
                return parentName ? `${parentName}${parent.type === 'family' ? ' (family)' : ''}` : ''
            }).filter(Boolean)
        }

        return []
    }

    const text = String(value).trim()
    if (!text) {
        return []
    }

    try {
        const parsed = JSON.parse(text)
        if (Array.isArray(parsed) || (parsed && typeof parsed === 'object')) {
            return displayValue(parsed)
        }
    } catch {
        // Plain text is supported in addition to JSON-encoded database fields.
    }

    return text.split(/[\n;,|]/).map(item => item.trim()).filter(Boolean)
}

function getTraits(monster) {
    const traits = displayValue(getFirstValue(monster, ['traits', 'trait']))

    for (const [key, value] of Object.entries(monster ?? {})) {
        if (/^trait_?\d+$/i.test(key)) {
            traits.push(...displayValue(value))
        }
    }

    return [...new Set(traits)]
}

function getSpecialSynthesis(monster, recipes) {
    const name = normalizeName(monster?.name_en)
    if (!name) {
        return []
    }

    return (recipes?.recipes ?? [])
        .filter(recipe => normalizeName(recipe.result) === name)
        .map(recipe => ({
            parents: (recipe.parents ?? []).map(parent => {
                const parentName = parent.name ?? parent.family
                return parentName
                    ? `${parentName}${parent.type === 'family' ? ' (family)' : ''}`
                    : ''
            }).filter(Boolean)
        }))
}

export function parseMonsterInfo(monster, recipeSource = {}) {
    const primarySynthesisValue = getFirstValue(monster, [
        'primary_synthesis',
        'primary_synthesis_recipe',
        'synthesis_recipe',
        'synthesis'
    ])
    const primarySynthesis = primarySynthesisValue
        ? displayValue(primarySynthesisValue)
        : getSpecialSynthesis(monster, recipeSource)

    return {
        innateSkills: displayValue(getFirstValue(monster, [
            'innate_skill',
            'innate_skills',
            'innateSkill',
            'innateSkills'
        ])),
        traits: getTraits(monster),
        family: displayValue(monster?.family),
        rank: displayValue(monster?.rank),
        size: displayValue(monster?.size),
        primarySynthesis,
        scoutLocations: displayValue(getFirstValue(monster, [
            'scout_locations',
            'scout_location',
            'scouting_locations',
            'scouting_location',
            'scouted_at',
            'obtainment_location'
        ])),
        scoutable: typeof monster?.scoutable === 'boolean' ? monster.scoutable : null,
        normalSynthesis: typeof monster?.normal_synthesis === 'boolean'
            ? monster.normal_synthesis
            : null
    }
}
