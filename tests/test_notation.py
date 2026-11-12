import pytest

from app.notation import note_lettre


@pytest.mark.parametrize(
    ("score", "note"),
    [
        (100, "A"),
        (80, "A"),
        (79.9, "B"),
        (65, "B"),
        (64, "C"),
        (50, "C"),
        (49, "D"),
        (35, "D"),
        (34.9, "E"),
        (0, "E"),
    ],
)
def test_note_lettre_respecte_les_seuils(score, note):
    assert note_lettre(score) == note
