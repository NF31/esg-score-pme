"""Interface Streamlit -- diagnostic ESG en trois etapes : entreprise, questionnaire, resultats."""

import httpx
import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from app.benchmark import comparer_secteur
from app.database import DATABASE_URL, engine, preparer_base_sqlite
from app.esrs import ESRS_LABELS, LIBELLES_COURTS_ESRS, scores_par_esrs
from app.exemple import charger_exemple
from app.export_esrs import generer_export_esrs
from app.extraction_pdf import extraire_reponses
from app.greenwashing import detecter_ecarts
from app.historique import historique_scores
from app.import_entreprises import (
    LONGUEUR_MIN_RECHERCHE,
    EntrepriseTrouvee,
    enregistrer_entreprise,
    rechercher_entreprises,
)
from app.models import Effort, Entreprise, Pilier, Question, Questionnaire, Reponse
from app.notation import note_lettre
from app.rapport import generer_rapport_pdf
from app.recommandations import generer_recommandations
from app.scoring import calculer_scores
from app.secteurs import libelle_secteur
from app.seed import seed_questions

LIBELLE_PILIER = {
    Pilier.ENVIRONNEMENT: "Environnement",
    Pilier.SOCIAL: "Social",
    Pilier.GOUVERNANCE: "Gouvernance",
}
ORDRE_PILIERS = list(Pilier)

# Echelle de reponse 0-4 (docs/SCORING.md), formulee pour un dirigeant de PME
ECHELLE = {
    0: "Non",
    1: "C'est prévu",
    2: "En partie",
    3: "Oui, formalisé",
    4: "Oui, mesuré et suivi",
}
LIBELLE_EFFORT = {Effort.FAIBLE: "Faible", Effort.MOYEN: "Moyen", Effort.ELEVE: "Élevé"}

# En PostgreSQL le schéma est géré par Alembic (`alembic upgrade head`) ;
# en SQLite (dev rapide, démo publique), la base est recréée si son schéma est périmé.
if DATABASE_URL.startswith("sqlite"):
    preparer_base_sqlite(engine)
with Session(engine) as _db:
    seed_questions(_db)

st.set_page_config(page_title="ESG Score PME", page_icon=":material/eco:")

ETAT_INITIAL = {
    "etape": "entreprise",
    "entreprise_id": None,
    "questionnaire_id": None,
    "suggestions_ia": None,
    "recherche": "",
}
for cle, valeur in ETAT_INITIAL.items():
    st.session_state.setdefault(cle, valeur)


@st.cache_data(ttl=3600, max_entries=500, show_spinner="Recherche dans le répertoire…")
def chercher(texte: str) -> list[EntrepriseTrouvee]:
    return rechercher_entreprises(texte)


@st.cache_data
def charger_questions() -> list[dict]:
    with Session(engine) as db:
        questions = db.query(Question).order_by(Question.id).all()
        return [
            {"id": q.id, "pilier": q.pilier, "libelle": q.libelle, "aide": q.aide}
            for q in questions
        ]


def cle_question(question_id: int) -> str:
    return f"q_{question_id}"


def reponses_saisies(questions: list[dict]) -> dict[int, int]:
    return {
        q["id"]: st.session_state[cle_question(q["id"])]
        for q in questions
        if st.session_state.get(cle_question(q["id"])) is not None
    }


def oublier_reponses() -> None:
    for cle in [c for c in st.session_state if str(c).startswith("q_")]:
        del st.session_state[cle]
    st.session_state.suggestions_ia = None


def demarrer_diagnostic(entreprise_id: int) -> None:
    with Session(engine) as db:
        questionnaire = Questionnaire(entreprise_id=entreprise_id)
        db.add(questionnaire)
        db.commit()
        st.session_state.questionnaire_id = questionnaire.id
    st.session_state.entreprise_id = entreprise_id
    st.session_state.pilier_actif = Pilier.ENVIRONNEMENT
    oublier_reponses()
    st.session_state.etape = "questionnaire"


def choisir_entreprise(trouvee: EntrepriseTrouvee) -> None:
    with Session(engine) as db:
        entreprise = enregistrer_entreprise(db, trouvee)
    st.session_state.tranche_effectif = trouvee.tranche_effectif
    demarrer_diagnostic(entreprise.id)


def ouvrir_exemple() -> None:
    with Session(engine) as db:
        questionnaire = charger_exemple(db)
        st.session_state.entreprise_id = questionnaire.entreprise_id
        st.session_state.questionnaire_id = questionnaire.id
    st.session_state.tranche_effectif = None
    oublier_reponses()
    st.session_state.etape = "resultats"


def recommencer() -> None:
    for cle, valeur in ETAT_INITIAL.items():
        st.session_state[cle] = valeur
    oublier_reponses()


def aller_au_pilier(pilier: Pilier) -> None:
    st.session_state.pilier_actif = pilier


def enregistrer_et_calculer(questions: list[dict]) -> None:
    reponses = reponses_saisies(questions)
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
        calculer_scores(db, st.session_state.questionnaire_id)
    st.session_state.etape = "resultats"


def libelle_effectif(entreprise: Entreprise) -> str:
    tranche = st.session_state.get("tranche_effectif")
    return tranche or f"{entreprise.effectif} salariés"


st.title("Diagnostic ESG pour PME")

# --- Etape 1 : trouver son entreprise -------------------------------------------------
if st.session_state.etape == "entreprise":
    st.markdown(
        "Un score par pilier, une comparaison avec votre secteur et un plan d'action "
        "concret, à partir de 24 questions qui se répondent chacune en un clic."
    )

    # L'exemple passe avant la recherche : un visiteur pressé voit le résultat sans rien remplir.
    with st.container(border=True, horizontal=True, vertical_alignment="center"):
        with st.container(width="stretch", gap=None):
            st.markdown("**Envie de voir le résultat d'abord ?**")
            st.caption(
                "Une entreprise exemple déjà remplie, avec son historique et des "
                "concurrents du même secteur. Données fictives."
            )
        st.button(
            "Essayer avec un exemple",
            icon=":material/play_arrow:",
            on_click=ouvrir_exemple,
            width="content",
        )

    with st.container(border=True):
        with st.form("form_recherche", border=False):
            texte = st.text_input(
                "Rechercher votre entreprise",
                placeholder="Nom ou numéro SIREN",
                help="Les informations viennent du répertoire officiel des entreprises "
                "(INSEE, via recherche-entreprises.api.gouv.fr).",
            )
            if st.form_submit_button("Rechercher", type="primary"):
                st.session_state.recherche = texte.strip()

        recherche = st.session_state.recherche
        if recherche:
            resultats: list[EntrepriseTrouvee] = []
            try:
                resultats = chercher(recherche)
            except ValueError:
                st.warning(f"Saisissez au moins {LONGUEUR_MIN_RECHERCHE} caractères.")
            except httpx.HTTPError:
                st.error(
                    "Le répertoire des entreprises ne répond pas pour le moment. "
                    "Réessayez dans quelques instants.",
                    title="Recherche indisponible",
                )
            else:
                if not resultats:
                    st.info(
                        f"Aucune entreprise active trouvée pour « {recherche} ». Vérifiez "
                        "l'orthographe ou essayez avec le numéro SIREN (9 chiffres)."
                    )
                else:
                    index = st.radio(
                        f"{len(resultats)} résultat(s), choisissez votre entreprise",
                        range(len(resultats)),
                        index=None,
                        format_func=lambda i: resultats[i].nom,
                        captions=[
                            f"{r.commune} ({r.code_postal}) · SIREN {r.siren} · "
                            f"{libelle_secteur(r.secteur)}"
                            for r in resultats
                        ],
                        key=f"choix_{recherche}",
                    )
                    if index is not None:
                        choisie = resultats[index]
                        with st.container(horizontal=True):
                            st.metric("Secteur (code NAF)", choisie.code_naf or "Non renseigné")
                            st.metric("Effectif (tranche INSEE)", choisie.tranche_effectif)
                        st.button(
                            "Commencer le diagnostic",
                            type="primary",
                            on_click=choisir_entreprise,
                            args=(choisie,),
                        )

# --- Etape 2 : questionnaire, pilier par pilier --------------------------------------
elif st.session_state.etape == "questionnaire":
    questions = charger_questions()
    with Session(engine) as db:
        entreprise = db.get(Entreprise, st.session_state.entreprise_id)
        st.header(entreprise.nom)
        st.caption(f"{libelle_secteur(entreprise.secteur)} · {libelle_effectif(entreprise)}")

    with st.expander(
        "Pré-remplir depuis un rapport RSE (PDF) avec l'IA", icon=":material/upload_file:"
    ):
        pdf_upload = st.file_uploader("Rapport RSE au format PDF", type="pdf")
        if pdf_upload is not None and st.button("Analyser le rapport"):
            with st.spinner("Analyse du rapport en cours…"), Session(engine) as db:
                try:
                    reponses_ia = extraire_reponses(db, pdf_upload.getvalue())
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.session_state.suggestions_ia = {r["question_id"]: r for r in reponses_ia}
                    for suggestion in reponses_ia:
                        st.session_state[cle_question(suggestion["question_id"])] = suggestion[
                            "valeur"
                        ]
                    st.success(
                        f"{len(reponses_ia)} réponse(s) suggérée(s). Vérifiez-les avant de "
                        "calculer le score."
                    )
    suggestions_ia = st.session_state.suggestions_ia or {}

    reponses = reponses_saisies(questions)
    par_pilier = {p: [q for q in questions if q["pilier"] == p] for p in ORDRE_PILIERS}

    def libelle_onglet(pilier: Pilier) -> str:
        faites = sum(1 for q in par_pilier[pilier] if q["id"] in reponses)
        return f"{LIBELLE_PILIER[pilier]} ({faites}/{len(par_pilier[pilier])})"

    st.session_state.setdefault("pilier_actif", Pilier.ENVIRONNEMENT)
    pilier = st.segmented_control(
        "Pilier",
        ORDRE_PILIERS,
        format_func=libelle_onglet,
        key="pilier_actif",
        required=True,
        label_visibility="collapsed",
        width="stretch",
    )
    st.progress(
        len(reponses) / len(questions), text=f"{len(reponses)} questions sur {len(questions)}"
    )

    for question in par_pilier[pilier]:
        with st.container(border=True):
            st.segmented_control(
                question["libelle"],
                list(ECHELLE),
                format_func=ECHELLE.get,
                key=cle_question(question["id"]),
                persist_state="page",
                wrap=True,
            )
            if question["aide"]:
                st.caption(question["aide"])
            suggestion = suggestions_ia.get(question["id"])
            if suggestion:
                st.caption(f":material/smart_toy: Suggestion IA : {suggestion['justification']}")

    position = ORDRE_PILIERS.index(pilier)
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if position > 0:
            st.button(
                f"Retour : {LIBELLE_PILIER[ORDRE_PILIERS[position - 1]]}",
                on_click=aller_au_pilier,
                args=(ORDRE_PILIERS[position - 1],),
            )
        else:
            st.button("Changer d'entreprise", on_click=recommencer)
        if position < len(ORDRE_PILIERS) - 1:
            st.button(
                f"Suivant : {LIBELLE_PILIER[ORDRE_PILIERS[position + 1]]}",
                type="primary",
                on_click=aller_au_pilier,
                args=(ORDRE_PILIERS[position + 1],),
            )
        else:
            manquantes = len(questions) - len(reponses)
            st.button(
                "Calculer mon score",
                type="primary",
                disabled=manquantes > 0,
                help=f"Encore {manquantes} question(s) sans réponse." if manquantes else None,
                on_click=enregistrer_et_calculer,
                args=(questions,),
            )

# --- Etape 3 : resultats et plan d'action --------------------------------------------
else:
    questionnaire_id = st.session_state.questionnaire_id
    with Session(engine) as db:
        entreprise = db.get(Entreprise, st.session_state.entreprise_id)
        questionnaire = db.get(Questionnaire, questionnaire_id)
        scores = {s.pilier: s.valeur for s in questionnaire.scores}
        comparaison = comparer_secteur(db, questionnaire_id)
        profil_esrs = scores_par_esrs(db, questionnaire_id)
        recommandations = generer_recommandations(db, questionnaire_id)
        historique = historique_scores(db, entreprise.id)
        if st.session_state.suggestions_ia:
            ecarts = detecter_ecarts(
                db, questionnaire_id, list(st.session_state.suggestions_ia.values())
            )
        else:
            ecarts = []
        rapport_pdf = generer_rapport_pdf(db, questionnaire_id)
        export_esrs = generer_export_esrs(db, questionnaire_id)
        nom, est_exemple = entreprise.nom, entreprise.est_exemple
        secteur = libelle_secteur(entreprise.secteur)
        effectif = libelle_effectif(entreprise)
        date_diagnostic = questionnaire.created_at

    if est_exemple:
        st.badge("Entreprise exemple : données fictives", icon=":material/science:", color="orange")
    st.header(nom)
    st.caption(f"{secteur} · {effectif} · diagnostic du {date_diagnostic:%d/%m/%Y}")

    score_global = scores[None]
    info_globale = comparaison.get(None)
    with st.container(horizontal=True):
        st.metric(
            "Note ESG",
            note_lettre(score_global),
            border=True,
            help="A : 80 et plus, B : 65 à 79, C : 50 à 64, D : 35 à 49, E : moins de 35.",
        )
        st.metric(
            "Score global",
            f"{score_global:.0f}/100",
            delta=f"{score_global - info_globale['moyenne']:+.0f} vs secteur"
            if info_globale
            else None,
            border=True,
        )

    with st.container(border=True):
        st.markdown("**Par pilier, face à la moyenne du secteur**")
        for pilier in ORDRE_PILIERS:
            if pilier not in scores:
                continue
            info = comparaison.get(pilier)
            secteur_txt = f" · secteur {info['moyenne']:.0f}" if info else ""
            st.progress(
                scores[pilier] / 100,
                text=f"{LIBELLE_PILIER[pilier]} : {scores[pilier]:.0f}/100{secteur_txt}",
            )
        if info_globale:
            st.caption(
                f"Moyenne calculée sur {info_globale['nb_entreprises']} autre(s) diagnostic(s) "
                "du même secteur."
            )
        else:
            st.caption("Pas encore d'autre diagnostic dans ce secteur pour comparer.")

    colonne_radar, colonne_bilan = st.columns(2)
    with colonne_radar, st.container(border=True):
        st.markdown("**Profil par thème ESRS**")
        st.echarts_chart(
            {
                "radar": {
                    "indicator": [
                        {"name": LIBELLES_COURTS_ESRS[code], "max": 100} for code in profil_esrs
                    ],
                    "radius": "55%",
                },
                "tooltip": {},
                "series": [
                    {
                        "type": "radar",
                        "data": [
                            {
                                "name": "Score sur 100",
                                "value": [round(v) for v in profil_esrs.values()],
                                "areaStyle": {"opacity": 0.2},
                            }
                        ],
                    }
                ],
            },
            height=320,
            alt="Score sur 100 de chaque thème ESRS : "
            + ", ".join(f"{LIBELLES_COURTS_ESRS[c]} {v:.0f}" for c, v in profil_esrs.items()),
        )

    with colonne_bilan, st.container(border=True):
        classes = sorted(profil_esrs.items(), key=lambda item: item[1], reverse=True)
        st.markdown("**Points forts**")
        forts = [(c, v) for c, v in classes[:2] if v >= 50]
        st.markdown(
            "\n".join(f"- {ESRS_LABELS[c]} ({v:.0f}/100)" for c, v in forts)
            or "Aucun thème au-dessus de 50/100 pour l'instant."
        )
        st.markdown("**À travailler en priorité**")
        faibles = [(c, v) for c, v in classes[::-1][:2] if v < 100]
        st.markdown("\n".join(f"- {ESRS_LABELS[c]} ({v:.0f}/100)" for c, v in faibles))

        points_globaux = [p for p in historique if p.pilier is None]
        if len(points_globaux) > 1:
            st.markdown("**Évolution du score global**")
            st.line_chart(
                pd.DataFrame(
                    {
                        "Diagnostic": [
                            f"{p.questionnaire.created_at:%Y-%m}" for p in points_globaux
                        ],
                        "Score global": [p.valeur for p in points_globaux],
                    }
                ),
                x="Diagnostic",
                y="Score global",
                height=180,
                alt=f"Score global sur {len(points_globaux)} diagnostics, de "
                f"{points_globaux[0].valeur:.0f} à {points_globaux[-1].valeur:.0f}",
            )

    if recommandations:
        with st.container(border=True):
            st.subheader("Votre plan d'action")
            st.caption("Classé par gain de points pour le moins d'effort : commencez par le haut.")
            st.table(
                pd.DataFrame(
                    {
                        "Action": [r.action or r.libelle for r in recommandations],
                        "Pilier": [LIBELLE_PILIER[r.pilier] for r in recommandations],
                        "Effort": [LIBELLE_EFFORT[r.effort] for r in recommandations],
                        "Gain": [f"+{r.gain_points:.1f} pts" for r in recommandations],
                    }
                ),
                border="horizontal",
                hide_index=True,
                alt="Plan d'action : actions conseillées, effort et gain de points",
            )

    if ecarts:
        with st.container(border=True):
            st.subheader("Risques de greenwashing détectés")
            st.caption(
                "Questions où le rapport RSE annonçait une meilleure pratique que celle "
                "finalement validée : un écart entre le discours et la réalité."
            )
            for ecart in ecarts:
                st.markdown(
                    f"- **{LIBELLE_PILIER[ecart['pilier']]}** — {ecart['libelle']} : "
                    f"rapport {ecart['valeur_rapport']}/4, réponse validée "
                    f"{ecart['valeur_reelle']}/4"
                )
                st.caption(f"D'après le rapport : {ecart['justification_rapport']}")

    with st.container(horizontal=True):
        st.download_button(
            "Télécharger le rapport PDF",
            data=rapport_pdf,
            file_name="rapport-esg.pdf",
            mime="application/pdf",
            type="primary",
            icon=":material/download:",
        )
        st.download_button(
            "Export au format ESRS",
            data=export_esrs,
            file_name="export-esrs.pdf",
            mime="application/pdf",
            icon=":material/download:",
        )
        if not est_exemple:
            st.button(
                "Refaire un diagnostic (même entreprise)",
                on_click=demarrer_diagnostic,
                args=(st.session_state.entreprise_id,),
            )
        st.button("Nouveau diagnostic", on_click=recommencer)
