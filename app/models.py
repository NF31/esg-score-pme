"""Modèle de données ESG — entreprise, questionnaire, réponses, scores.

Basé sur des critères ESRS simplifiés, regroupés en trois piliers (E/S/G).
La persistance réelle (moteur PostgreSQL, migrations) arrive avec F07 ;
ce module ne définit que le schéma ORM.
"""

import enum
from datetime import UTC, datetime

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Pilier(enum.Enum):
    ENVIRONNEMENT = "environnement"
    SOCIAL = "social"
    GOUVERNANCE = "gouvernance"


class StatutQuestionnaire(enum.Enum):
    EN_COURS = "en_cours"
    TERMINE = "termine"


class Entreprise(Base):
    __tablename__ = "entreprises"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(200))
    secteur: Mapped[str] = mapped_column(String(100))
    effectif: Mapped[int]
    siren: Mapped[str | None] = mapped_column(String(9), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    questionnaires: Mapped[list["Questionnaire"]] = relationship(back_populates="entreprise")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    pilier: Mapped[Pilier] = mapped_column(Enum(Pilier))
    libelle: Mapped[str] = mapped_column(Text)
    poids: Mapped[float] = mapped_column(default=1.0)
    esrs_standard: Mapped[str] = mapped_column(String(20), default="ESRS 2")

    reponses: Mapped[list["Reponse"]] = relationship(back_populates="question")


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id: Mapped[int] = mapped_column(primary_key=True)
    entreprise_id: Mapped[int] = mapped_column(ForeignKey("entreprises.id"))
    statut: Mapped[StatutQuestionnaire] = mapped_column(
        Enum(StatutQuestionnaire), default=StatutQuestionnaire.EN_COURS
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    entreprise: Mapped[Entreprise] = relationship(back_populates="questionnaires")
    reponses: Mapped[list["Reponse"]] = relationship(back_populates="questionnaire")
    scores: Mapped[list["Score"]] = relationship(back_populates="questionnaire")


class Reponse(Base):
    __tablename__ = "reponses"

    id: Mapped[int] = mapped_column(primary_key=True)
    questionnaire_id: Mapped[int] = mapped_column(ForeignKey("questionnaires.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    valeur: Mapped[int]  # échelle 0-4 (Likert)

    questionnaire: Mapped[Questionnaire] = relationship(back_populates="reponses")
    question: Mapped[Question] = relationship(back_populates="reponses")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    questionnaire_id: Mapped[int] = mapped_column(ForeignKey("questionnaires.id"))
    pilier: Mapped[Pilier | None] = mapped_column(
        Enum(Pilier), nullable=True
    )  # None = score global
    valeur: Mapped[float]

    questionnaire: Mapped[Questionnaire] = relationship(back_populates="scores")
