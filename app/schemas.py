from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Effort, Pilier, StatutQuestionnaire
from app.secteurs import SECTEURS


class EntrepriseCreate(BaseModel):
    nom: str
    secteur: str = Field(description=f"Un des secteurs : {', '.join(SECTEURS)}")
    effectif: int

    @field_validator("secteur")
    @classmethod
    def secteur_connu(cls, valeur: str) -> str:
        if valeur not in SECTEURS:
            raise ValueError(f"secteur inconnu, doit etre l'un de : {', '.join(SECTEURS)}")
        return valeur


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


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pilier: Pilier | None  # None = score global
    valeur: float


class ComparaisonSecteurOut(BaseModel):
    pilier: Pilier | None  # None = score global
    moyenne: float
    nb_entreprises: int


class HistoriquePointOut(BaseModel):
    questionnaire_id: int
    date: datetime
    pilier: Pilier | None  # None = score global
    valeur: float


class ExtractionReponseOut(BaseModel):
    question_id: int
    valeur: int = Field(ge=0, le=4)
    justification: str


class GreenwashingEcartOut(BaseModel):
    question_id: int
    pilier: Pilier
    libelle: str
    valeur_rapport: int
    valeur_reelle: int
    ecart: int
    justification_rapport: str


class RecommandationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    pilier: Pilier
    libelle: str
    valeur_actuelle: int
    gain_potentiel: float
    action: str | None
    effort: Effort
    gain_points: float = Field(
        description="Points de score global gagnes si la reponse passe a 4/4"
    )
