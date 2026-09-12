from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, Entreprise, Question, Questionnaire, Reponse
from app.schemas import (
    EntrepriseCreate,
    EntrepriseOut,
    QuestionnaireCreate,
    QuestionnaireOut,
    QuestionOut,
    ReponseIn,
    ReponseOut,
)
from app.seed import seed_questions


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
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
