from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Entreprise, Pilier, Question, Questionnaire, Reponse, Score


def test_schema_creates_and_relationships_work():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        entreprise = Entreprise(nom="Acme SARL", secteur="Industrie manufacturiere", effectif=42)
        question = Question(pilier=Pilier.ENVIRONNEMENT, libelle="Mesure son empreinte carbone ?")
        session.add_all([entreprise, question])
        session.flush()

        questionnaire = Questionnaire(entreprise=entreprise)
        session.add(questionnaire)
        session.flush()

        reponse = Reponse(questionnaire=questionnaire, question=question, valeur=3)
        score = Score(questionnaire=questionnaire, pilier=Pilier.ENVIRONNEMENT, valeur=75.0)
        session.add_all([reponse, score])
        session.commit()

        assert entreprise.questionnaires == [questionnaire]
        assert questionnaire.reponses[0].valeur == 3
        assert questionnaire.scores[0].pilier is Pilier.ENVIRONNEMENT
