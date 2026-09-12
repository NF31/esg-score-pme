import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.models import Base
from app.seed import QUESTIONS_SEED, seed_questions
from main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_questions(db)
    yield
    Base.metadata.drop_all(engine)


client = TestClient(app)


def test_questions_are_seeded_across_the_three_piliers():
    response = client.get("/questions")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) == len(QUESTIONS_SEED)
    assert {q["pilier"] for q in questions} == {"environnement", "social", "gouvernance"}


def test_full_flow_entreprise_questionnaire_reponse():
    entreprise = client.post(
        "/entreprises", json={"nom": "Acme SARL", "secteur": "Industrie", "effectif": 42}
    ).json()

    questionnaire = client.post("/questionnaires", json={"entreprise_id": entreprise["id"]}).json()
    assert questionnaire["statut"] == "en_cours"

    question_id = client.get("/questions").json()[0]["id"]
    reponse = client.post(
        f"/questionnaires/{questionnaire['id']}/reponses",
        json={"question_id": question_id, "valeur": 3},
    )
    assert reponse.status_code == 201
    assert reponse.json()["valeur"] == 3


def test_reponse_valeur_hors_echelle_est_rejetee():
    entreprise = client.post(
        "/entreprises", json={"nom": "Acme SARL", "secteur": "Industrie", "effectif": 42}
    ).json()
    questionnaire = client.post("/questionnaires", json={"entreprise_id": entreprise["id"]}).json()
    question_id = client.get("/questions").json()[0]["id"]

    response = client.post(
        f"/questionnaires/{questionnaire['id']}/reponses",
        json={"question_id": question_id, "valeur": 5},
    )
    assert response.status_code == 422


def test_questionnaire_sur_entreprise_inexistante_est_rejete():
    response = client.post("/questionnaires", json={"entreprise_id": 999})
    assert response.status_code == 404


def test_calculer_score_via_api():
    entreprise = client.post(
        "/entreprises", json={"nom": "Acme SARL", "secteur": "Industrie", "effectif": 42}
    ).json()
    questionnaire = client.post("/questionnaires", json={"entreprise_id": entreprise["id"]}).json()

    for question in client.get("/questions").json():
        client.post(
            f"/questionnaires/{questionnaire['id']}/reponses",
            json={"question_id": question["id"], "valeur": 4},
        )

    response = client.post(f"/questionnaires/{questionnaire['id']}/calculer-score")
    assert response.status_code == 200
    scores = response.json()
    assert len(scores) == 4  # 3 piliers + score global
    assert all(s["valeur"] == 100.0 for s in scores)


def test_calculer_score_sans_reponse_renvoie_400():
    entreprise = client.post(
        "/entreprises", json={"nom": "Acme SARL", "secteur": "Industrie", "effectif": 42}
    ).json()
    questionnaire = client.post("/questionnaires", json={"entreprise_id": entreprise["id"]}).json()

    response = client.post(f"/questionnaires/{questionnaire['id']}/calculer-score")
    assert response.status_code == 400


def test_telecharger_rapport_via_api():
    entreprise = client.post(
        "/entreprises", json={"nom": "Acme SARL", "secteur": "Industrie", "effectif": 42}
    ).json()
    questionnaire = client.post("/questionnaires", json={"entreprise_id": entreprise["id"]}).json()
    for question in client.get("/questions").json():
        client.post(
            f"/questionnaires/{questionnaire['id']}/reponses",
            json={"question_id": question["id"], "valeur": 3},
        )
    client.post(f"/questionnaires/{questionnaire['id']}/calculer-score")

    response = client.get(f"/questionnaires/{questionnaire['id']}/rapport")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_telecharger_rapport_sans_score_renvoie_400():
    entreprise = client.post(
        "/entreprises", json={"nom": "Acme SARL", "secteur": "Industrie", "effectif": 42}
    ).json()
    questionnaire = client.post("/questionnaires", json={"entreprise_id": entreprise["id"]}).json()

    response = client.get(f"/questionnaires/{questionnaire['id']}/rapport")
    assert response.status_code == 400
