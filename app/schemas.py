from pydantic import BaseModel, ConfigDict, Field

from app.models import Pilier, StatutQuestionnaire


class EntrepriseCreate(BaseModel):
    nom: str
    secteur: str
    effectif: int


class EntrepriseOut(EntrepriseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pilier: Pilier
    libelle: str


class QuestionnaireCreate(BaseModel):
    entreprise_id: int


class QuestionnaireOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entreprise_id: int
    statut: StatutQuestionnaire


class ReponseIn(BaseModel):
    question_id: int
    valeur: int = Field(ge=0, le=4)


class ReponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    valeur: int
