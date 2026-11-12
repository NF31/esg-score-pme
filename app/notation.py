"""Note lettre (A a E) affichee a cote du score global (F19).

Les seuils sont un choix de lisibilite, pas une norme : ils traduisent le score sur 100
en un repere immediat, comme une etiquette energie. Justification dans docs/SCORING.md.
"""

# (score minimal inclus, note), du meilleur au moins bon
SEUILS_NOTE: list[tuple[float, str]] = [(80, "A"), (65, "B"), (50, "C"), (35, "D"), (0, "E")]


def note_lettre(score: float) -> str:
    for seuil, note in SEUILS_NOTE:
        if score >= seuil:
            return note
    return "E"
