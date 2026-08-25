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


# 1. Obtener todas las ediciones/temporadas disponibles de la FIFA World Cup
@st.cache_data
def get_world_cup_editions():
    comps = sb.competitions()
    # Filtrar únicamente la Copa del Mundo Masculina
    wc_comps = comps[comps["competition_name"] == "FIFA World Cup"].copy()
    # Ordenar por temporada/año de manera descendente
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


# 3. Cargar los eventos de pases de un partido
@st.cache_data
def load_match_passes(match_id):
    events = sb.events(match_id=match_id)

    # Filtrar sólo eventos de tipo Pass
    passes = events[events["type"] == "Pass"].copy()
    passes.reset_index(drop=True, inplace=True)

    # Coordenadas (x, y) de inicio y fin del pase
    passes["x0"] = passes.location.apply(lambda x: x[0])
    passes["y0"] = passes.location.apply(lambda x: x[1])
    passes["x1"] = passes.pass_end_location.apply(lambda x: x[0])
    passes["y1"] = passes.pass_end_location.apply(lambda x: x[1])

    return passes


# --- Carga inicial de ediciones ---
editions_df = get_world_cup_editions()

# --- Barra lateral para filtros en cascada ---
st.sidebar.header("Filtros del Torneo")

# 1. Selector de Edición / Año del Mundial
selected_season = st.sidebar.selectbox(
    "Selecciona la Edición / Año:", editions_df["season_name"].tolist()
)

# Extraer competition_id y season_id elegidos
selected_edition_row = editions_df[
    editions_df["season_name"] == selected_season
].iloc[0]
comp_id = int(selected_edition_row["competition_id"])
seas_id = int(selected_edition_row["season_id"])

# 2. Cargar partidos de la edición seleccionada
matches_df = get_matches_for_edition(comp_id, seas_id)

# 3. Selector de Selección / Equipo
teams = sorted(
    list(
        set(
            matches_df["home_team"].tolist() + matches_df["away_team"].tolist()
        )
    )
)
selected_team = st.sidebar.selectbox("Selecciona una Selección:", teams)

# Filtrar partidos donde participa el equipo seleccionado
team_matches = matches_df[
    (matches_df["home_team"] == selected_team)
    | (matches_df["away_team"] == selected_team)
]

# 4. Selector del Partido específico
match_selected_label = st.sidebar.selectbox(
    "Selecciona el Partido:", team_matches["match_label"].tolist()
)

match_id = team_matches[team_matches["match_label"] == match_selected_label][
    "match_id"
].values[0]

# --- Cargar datos del partido seleccionado ---
passes_df = load_match_passes(match_id)

st.subheader(f"Mundial {selected_season} | {match_selected_label}")

# Selector de minuto mediante Slider
min_minute = int(passes_df["minute"].min())
max_minute = int(passes_df["minute"].max())

minuto_seleccionado = st.slider(
    "Selecciona el minuto del partido:",
    min_value=min_minute,
    max_value=max_minute,
    value=min_minute,
    step=1,
)

# Filtrar pases por el minuto seleccionado
data_minuto = passes_df[passes_df["minute"] == minuto_seleccionado]

# Dibujar la cancha con mplsoccer
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

# Detalles adicionales de los pases
with st.expander("Ver detalles de los pases en este minuto"):
    st.dataframe(
        data_minuto[
            ["minute", "second", "team", "player", "pass_recipient", "type"]
        ]
    )
