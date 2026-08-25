import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from mplsoccer import Pitch
from statsbombpy import sb

# Configuración de la página
st.set_page_config(
    page_title="Visualizador de Pases - FIFA World Cup", layout="wide"
)
st.title("⚽ Visualizador de Pases - FIFA World Cup Multi-Edición")


# 1. Obtener todas las ediciones de la FIFA World Cup
@st.cache_data
def get_world_cup_editions():
    comps = sb.competitions()
    wc_comps = comps[comps["competition_name"] == "FIFA World Cup"].copy()
    wc_comps.sort_values(by="season_name", ascending=False, inplace=True)
    return wc_comps


# 2. Obtener los partidos de una edición específica
@st.cache_data
def get_matches_for_edition(competition_id, season_id):
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    matches["match_label"] = (
        matches["home_team"]
        + " vs "
        + matches["away_team"]
        + " ("
        + matches["competition_stage"].astype(str)
        + ")"
    )
    return matches


# 3. Cargar todos los eventos del partido (Pases y Goles)
@st.cache_data
def load_match_events(match_id):
    events = sb.events(match_id=match_id)

    # Filtrar pases
    passes = events[events["type"] == "Pass"].copy()
    passes.reset_index(drop=True, inplace=True)

    # Coordenadas (x, y) del pase
    passes["x0"] = passes.location.apply(
        lambda x: x[0] if isinstance(x, list) else None
    )
    passes["y0"] = passes.location.apply(
        lambda x: x[1] if isinstance(x, list) else None
    )
    passes["x1"] = passes.pass_end_location.apply(
        lambda x: x[0] if isinstance(x, list) else None
    )
    passes["y1"] = passes.pass_end_location.apply(
        lambda x: x[1] if isinstance(x, list) else None
    )

    # Filtrar eventos de gol (Tiros que terminaron en gol o autogoles)
    goals = events[
        (
            (events["type"] == "Shot")
            & (events["shot_outcome"].astype(str) == "Goal")
        )
        | (events["type"] == "Own Goal")
    ].copy()

    return passes, goals


# --- Carga inicial de datos ---
editions_df = get_world_cup_editions()

# --- Barra lateral ---
st.sidebar.header("Filtros del Torneo")

# Selector de Año/Edición
selected_season = st.sidebar.selectbox(
    "Selecciona la Edición / Año:", editions_df["season_name"].tolist()
)

selected_edition_row = editions_df[
    editions_df["season_name"] == selected_season
].iloc[0]
comp_id = int(selected_edition_row["competition_id"])
seas_id = int(selected_edition_row["season_id"])

# Selector de Selección y Partido
matches_df = get_matches_for_edition(comp_id, seas_id)

teams = sorted(
    list(
        set(
            matches_df["home_team"].tolist() + matches_df["away_team"].tolist()
        )
    )
)
selected_team = st.sidebar.selectbox("Selecciona una Selección:", teams)

team_matches = matches_df[
    (matches_df["home_team"] == selected_team)
    | (matches_df["away_team"] == selected_team)
]

match_selected_label = st.sidebar.selectbox(
    "Selecciona el Partido:", team_matches["match_label"].tolist()
)

match_row = team_matches[
    team_matches["match_label"] == match_selected_label
].iloc[0]
match_id = match_row["match_id"]
home_team = match_row["home_team"]
away_team = match_row["away_team"]

# Cargar pases y goles del partido
passes_df, goals_df = load_match_events(match_id)

# --- Slider de Minuto ---
min_minute = int(passes_df["minute"].min())
max_minute = int(passes_df["minute"].max())

minuto_seleccionado = st.slider(
    "Selecciona el minuto del partido:",
    min_value=min_minute,
    max_value=max_minute,
    value=min_minute,
    step=1,
)

# --- Cálculo del Marcador al Minuto Seleccionado ---
# Filtrar goles anotados antes o durante el minuto actual
goals_until_minute = goals_df[goals_df["minute"] <= minuto_seleccionado]

# Asignar goles según el equipo correspondiente
home_score = 0
away_score = 0

for _, goal in goals_until_minute.iterrows():
    team_event = goal["team"]
    is_own_goal = goal["type"] == "Own Goal"

    if not is_own_goal:
        if team_event == home_team:
            home_score += 1
        elif team_event == away_team:
            away_score += 1
    else:
        # En caso de autogol, se le acredita al equipo contrario
        if team_event == home_team:
            away_score += 1
        elif team_event == away_team:
            home_score += 1

# --- Vista del Marcador Dinámico ---
st.markdown(
    f"<h2 style='text-align: center;'>{home_team} {home_score} - {away_score} {away_team}</h2>",
    unsafe_allow_html=True,
)
st.caption(
    f"Marcador acumulado al **minuto {minuto_seleccionado}** (Mundial {selected_season})"
)

# --- Visualización de la Cancha ---
data_minuto = passes_df[passes_df["minute"] == minuto_seleccionado]

pitch = Pitch(pitch_color="grass", line_color="white", stripe=True)
fig, ax = pitch.draw(figsize=(10, 6))

if not data_minuto.empty:
    sns.scatterplot(
        data=data_minuto,
        x="x0",
        y="y0",
        hue="team",
        ax=ax,
        s=120,
        edgecolor="black",
        zorder=3,
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=2)
else:
    st.info(f"No hay registros de pases en el minuto {minuto_seleccionado}.")

st.pyplot(fig)

# Tabla de pases
with st.expander("Ver detalles de los pases en este minuto"):
    st.dataframe(
        data_minuto[
            ["minute", "second", "team", "player", "pass_recipient", "type"]
        ]
    )
