"""Interface Streamlit — saisie du questionnaire ESG et affichage du score."""

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from app.benchmark import comparer_secteur
from app.database import DATABASE_URL, engine
from app.extraction_pdf import extraire_reponses
from app.greenwashing import detecter_ecarts
from app.historique import historique_scores
from app.models import Base, Entreprise, Pilier, Question, Questionnaire, Reponse
from app.rapport import generer_rapport_pdf
from app.recommandations import generer_recommandations
from app.scoring import calculer_scores
from app.secteurs import SECTEURS
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
    st.session_state.entreprise_id = None
    st.session_state.entreprise_nom = None
    st.session_state.scores = None
    st.session_state.suggestions_ia = None

if st.session_state.questionnaire_id is None and st.session_state.entreprise_id is not None:
    # Reprise d'un diagnostic pour une entreprise deja existante (cf. bouton "meme entreprise")
    with Session(engine) as db:
        questionnaire = Questionnaire(entreprise_id=st.session_state.entreprise_id)
        db.add(questionnaire)
        db.commit()
        db.refresh(questionnaire)
        st.session_state.questionnaire_id = questionnaire.id
    st.rerun()

elif st.session_state.questionnaire_id is None:
    with st.form("entreprise_form"):
        nom = st.text_input("Nom de l'entreprise")
        secteur = st.selectbox("Secteur d'activite", SECTEURS, index=None)
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
                st.session_state.entreprise_id = entreprise.id
                st.session_state.entreprise_nom = entreprise.nom
            st.rerun()

else:
    st.header(f"Questionnaire — {st.session_state.entreprise_nom}")

    with Session(engine) as db:
        questions = db.query(Question).order_by(Question.pilier, Question.id).all()

    with st.expander("🤖 Pre-remplir depuis un rapport RSE (PDF) via l'IA"):
        pdf_upload = st.file_uploader("Rapport RSE au format PDF", type="pdf")
        if pdf_upload is not None and st.button("Analyser avec l'IA"):
            with st.spinner("Analyse du rapport en cours..."), Session(engine) as db:
                try:
                    reponses_ia = extraire_reponses(db, pdf_upload.getvalue())
                    st.session_state.suggestions_ia = {r["question_id"]: r for r in reponses_ia}
                    st.success(
                        f"{len(reponses_ia)} reponse(s) suggeree(s). Verifie et ajuste les "
                        "curseurs ci-dessous avant de calculer le score."
                    )
                except ValueError as exc:
                    st.error(str(exc))

    suggestions_ia = st.session_state.suggestions_ia or {}

    with st.form("questionnaire_form"):
        reponses: dict[int, int] = {}
        for pilier in Pilier:
            st.subheader(LIBELLE_PILIER[pilier])
            for question in [q for q in questions if q.pilier == pilier]:
                suggestion = suggestions_ia.get(question.id)
                valeur_defaut = suggestion["valeur"] if suggestion else 2
                reponses[question.id] = st.slider(
                    question.libelle, 0, 4, valeur_defaut, key=f"q_{question.id}"
                )
                if suggestion:
                    st.caption(f"🤖 Suggestion IA : {suggestion['justification']}")
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
        with Session(engine) as db:
            comparaison = comparer_secteur(db, st.session_state.questionnaire_id)

        st.divider()
        info_globale = comparaison.get(None)
        st.metric(
            "Score global ESG",
            f"{scores[None]:.0f}/100",
            delta=f"{scores[None] - info_globale['moyenne']:+.0f} vs moyenne secteur"
            if info_globale
            else None,
        )

        colonnes = st.columns(3)
        for colonne, pilier in zip(colonnes, Pilier, strict=True):
            info_pilier = comparaison.get(pilier)
            colonne.metric(
                LIBELLE_PILIER[pilier],
                f"{scores.get(pilier, 0):.0f}/100",
                delta=f"{scores[pilier] - info_pilier['moyenne']:+.0f} vs secteur"
                if info_pilier and pilier in scores
                else None,
            )

        if not comparaison:
            st.caption("Pas encore d'autre diagnostic complete dans ce secteur pour comparer.")
        elif info_globale:
            st.caption(
                f"Comparaison basee sur {info_globale['nb_entreprises']} "
                "diagnostic(s) complete(s) dans le meme secteur."
            )

        if suggestions_ia:
            with Session(engine) as db:
                ecarts = detecter_ecarts(
                    db, st.session_state.questionnaire_id, list(suggestions_ia.values())
                )
            if ecarts:
                st.subheader("⚠️ Risques de greenwashing detectes")
                st.caption(
                    "Questions ou le rapport RSE suggerait une meilleure pratique que ce que "
                    "tu as finalement valide — un ecart marque entre le discours et la realite."
                )
                for ecart in ecarts:
                    st.markdown(
                        f"- **{LIBELLE_PILIER[ecart['pilier']]}** — {ecart['libelle']} : "
                        f"rapport {ecart['valeur_rapport']}/4 vs reponse validee "
                        f"{ecart['valeur_reelle']}/4"
                    )
                    st.caption(f"_D'apres le rapport : {ecart['justification_rapport']}_")

        with Session(engine) as db:
            recommandations = generer_recommandations(db, st.session_state.questionnaire_id)
        if recommandations:
            st.subheader("🎯 Recommandations prioritaires")
            st.caption("Quick wins : les reponses avec le plus fort potentiel de gain de score.")
            for reco in recommandations:
                st.markdown(
                    f"- **{LIBELLE_PILIER[reco.pilier]}** — {reco.libelle} "
                    f"(actuellement {reco.valeur_actuelle}/4)"
                )

        with Session(engine) as db:
            pdf_bytes = generer_rapport_pdf(db, st.session_state.questionnaire_id)
        st.download_button(
            "Telecharger le rapport PDF",
            data=pdf_bytes,
            file_name="rapport-esg.pdf",
            mime="application/pdf",
        )

        with Session(engine) as db:
            historique = historique_scores(db, st.session_state.entreprise_id)
        points_globaux = [point for point in historique if point.pilier is None]
        if len(points_globaux) > 1:
            st.subheader("📈 Evolution du score global")
            df_historique = pd.DataFrame(
                {
                    "date": [point.questionnaire.created_at for point in points_globaux],
                    "Score global": [point.valeur for point in points_globaux],
                }
            ).set_index("date")
            st.line_chart(df_historique)

    colonne_nouveau, colonne_meme_entreprise = st.columns(2)
    if colonne_nouveau.button("Nouveau diagnostic"):
        st.session_state.questionnaire_id = None
        st.session_state.entreprise_id = None
        st.session_state.entreprise_nom = None
        st.session_state.scores = None
        st.session_state.suggestions_ia = None
        st.rerun()
    if st.session_state.scores and colonne_meme_entreprise.button(
        "Refaire un diagnostic (meme entreprise)"
    ):
        st.session_state.questionnaire_id = None
        st.session_state.scores = None
        st.session_state.suggestions_ia = None
        st.rerun()
