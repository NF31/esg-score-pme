"""Interface Streamlit — saisie du questionnaire ESG et affichage du score."""

import streamlit as st
from sqlalchemy.orm import Session

from app.database import DATABASE_URL, engine
from app.models import Base, Entreprise, Pilier, Question, Questionnaire, Reponse
from app.rapport import generer_rapport_pdf
from app.scoring import calculer_scores
from app.seed import seed_questions

LIBELLE_PILIER = {
    Pilier.ENVIRONNEMENT: "🌍 Environnement",
    Pilier.SOCIAL: "🤝 Social",
    Pilier.GOUVERNANCE: "⚖️ Gouvernance",
}

# En PostgreSQL le schéma est géré par Alembic (`alembic upgrade head`) ;
# create_all reste utile en SQLite pour le dev rapide sans migration.
if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(engine)
with Session(engine) as _db:
    seed_questions(_db)

st.set_page_config(page_title="ESG Score PME", page_icon="🌱")
st.title("Diagnostic ESG pour PME")

if "questionnaire_id" not in st.session_state:
    st.session_state.questionnaire_id = None
    st.session_state.entreprise_nom = None
    st.session_state.scores = None

if st.session_state.questionnaire_id is None:
    with st.form("entreprise_form"):
        nom = st.text_input("Nom de l'entreprise")
        secteur = st.text_input("Secteur d'activite")
        effectif = st.number_input("Effectif", min_value=1, step=1)
        submitted = st.form_submit_button("Commencer le diagnostic")

    if submitted:
        if not nom or not secteur:
            st.error("Le nom et le secteur sont requis.")
        else:
            with Session(engine) as db:
                entreprise = Entreprise(nom=nom, secteur=secteur, effectif=int(effectif))
                db.add(entreprise)
                db.commit()
                db.refresh(entreprise)

                questionnaire = Questionnaire(entreprise_id=entreprise.id)
                db.add(questionnaire)
                db.commit()
                db.refresh(questionnaire)

                st.session_state.questionnaire_id = questionnaire.id
                st.session_state.entreprise_nom = entreprise.nom
            st.rerun()

else:
    st.header(f"Questionnaire — {st.session_state.entreprise_nom}")

    with Session(engine) as db:
        questions = db.query(Question).order_by(Question.pilier, Question.id).all()

    with st.form("questionnaire_form"):
        reponses: dict[int, int] = {}
        for pilier in Pilier:
            st.subheader(LIBELLE_PILIER[pilier])
            for question in [q for q in questions if q.pilier == pilier]:
                reponses[question.id] = st.slider(question.libelle, 0, 4, 2, key=f"q_{question.id}")
        valider = st.form_submit_button("Calculer mon score")

    if valider:
        with Session(engine) as db:
            db.query(Reponse).filter(
                Reponse.questionnaire_id == st.session_state.questionnaire_id
            ).delete()
            for question_id, valeur in reponses.items():
                db.add(
                    Reponse(
                        questionnaire_id=st.session_state.questionnaire_id,
                        question_id=question_id,
                        valeur=valeur,
                    )
                )
            db.commit()
            scores = calculer_scores(db, st.session_state.questionnaire_id)
            st.session_state.scores = {s.pilier: s.valeur for s in scores}

    if st.session_state.scores:
        scores = st.session_state.scores
        st.divider()
        st.metric("Score global ESG", f"{scores[None]:.0f}/100")

        colonnes = st.columns(3)
        for colonne, pilier in zip(colonnes, Pilier, strict=True):
            colonne.metric(LIBELLE_PILIER[pilier], f"{scores.get(pilier, 0):.0f}/100")

        with Session(engine) as db:
            pdf_bytes = generer_rapport_pdf(db, st.session_state.questionnaire_id)
        st.download_button(
            "Telecharger le rapport PDF",
            data=pdf_bytes,
            file_name="rapport-esg.pdf",
            mime="application/pdf",
        )

    if st.button("Nouveau diagnostic"):
        st.session_state.questionnaire_id = None
        st.session_state.entreprise_nom = None
        st.session_state.scores = None
        st.rerun()
