from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy.orm import Session

from app.benchmark import comparer_secteur
from app.database import DATABASE_URL, engine, get_db
from app.models import Base, Entreprise, Question, Questionnaire, Reponse
from app.rapport import generer_rapport_pdf
from app.recommandations import generer_recommandations
from app.schemas import (
    ComparaisonSecteurOut,
    EntrepriseCreate,
    EntrepriseOut,
    QuestionnaireCreate,
    QuestionnaireOut,
    QuestionOut,
    RecommandationOut,
    ReponseIn,
    ReponseOut,
    ScoreOut,
)
from app.scoring import calculer_scores
from app.seed import seed_questions


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # En PostgreSQL le schéma est géré par Alembic (`alembic upgrade head`) ;
    # create_all reste utile en SQLite pour le dev rapide sans migration.
    if DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_questions(db)
    yield


app = FastAPI(title="ESG Score PME", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/entreprises", response_model=EntrepriseOut, status_code=201)
def create_entreprise(payload: EntrepriseCreate, db: Session = Depends(get_db)):
    entreprise = Entreprise(**payload.model_dump())
    db.add(entreprise)
    db.commit()
    db.refresh(entreprise)
    return entreprise


@app.get("/questions", response_model=list[QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    return db.query(Question).order_by(Question.pilier, Question.id).all()


@app.post("/questionnaires", response_model=QuestionnaireOut, status_code=201)
def create_questionnaire(payload: QuestionnaireCreate, db: Session = Depends(get_db)):
    entreprise = db.get(Entreprise, payload.entreprise_id)
    if entreprise is None:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    questionnaire = Questionnaire(entreprise_id=entreprise.id)
    db.add(questionnaire)
    db.commit()
    db.refresh(questionnaire)
    return questionnaire


@app.post(
    "/questionnaires/{questionnaire_id}/reponses",
    response_model=ReponseOut,
    status_code=201,
)
def submit_reponse(questionnaire_id: int, payload: ReponseIn, db: Session = Depends(get_db)):
    questionnaire = db.get(Questionnaire, questionnaire_id)
    if questionnaire is None:
        raise HTTPException(status_code=404, detail="Questionnaire introuvable")
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question introuvable")

    reponse = Reponse(
        questionnaire_id=questionnaire_id,
        question_id=payload.question_id,
        valeur=payload.valeur,
    )
    db.add(reponse)
    db.commit()
    db.refresh(reponse)
    return reponse


@app.post("/questionnaires/{questionnaire_id}/calculer-score", response_model=list[ScoreOut])
def calculer_score_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    questionnaire = db.get(Questionnaire, questionnaire_id)
    if questionnaire is None:
        raise HTTPException(status_code=404, detail="Questionnaire introuvable")
    try:
        return calculer_scores(db, questionnaire_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get(
    "/questionnaires/{questionnaire_id}/comparaison-sectorielle",
    response_model=list[ComparaisonSecteurOut],
)
def comparaison_sectorielle(questionnaire_id: int, db: Session = Depends(get_db)):
    try:
        comparaison = comparer_secteur(db, questionnaire_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [{"pilier": pilier, **donnees} for pilier, donnees in comparaison.items()]


@app.get(
    "/questionnaires/{questionnaire_id}/recommandations",
    response_model=list[RecommandationOut],
)
def recommandations(questionnaire_id: int, db: Session = Depends(get_db)):
    try:
        return generer_recommandations(db, questionnaire_id)
    except ValueError as exc:
        status_code = 404 if "introuvable" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@app.get("/questionnaires/{questionnaire_id}/rapport")
def telecharger_rapport(questionnaire_id: int, db: Session = Depends(get_db)):
    try:
        pdf_bytes = generer_rapport_pdf(db, questionnaire_id)
    except ValueError as exc:
        status_code = 404 if "introuvable" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=rapport-esg-{questionnaire_id}.pdf"},
    )
