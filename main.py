import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from mplsoccer import Pitch
from statsbombpy import sb

# Configuración de la página
st.set_page_config(
    page_title="Visualizador de Pases - FIFA World Cup 2022", layout="wide"
)
st.title("⚽ Visualizador de Pases - FIFA World Cup 2022")


# 1. Obtener partidos de la World Cup 2022 (competition_id=43, season_id=106)
@st.cache_data
def get_world_cup_matches():
    matches = sb.matches(competition_id=43, season_id=106)
    # Crear una etiqueta legible para cada partido
    matches["match_label"] = (
        matches["home_team"]
        + " vs "
        + matches["away_team"]
        + " (Fase: "
        + matches["competition_stage"].astype(str)
        + ")"
    )
    return matches


# 2. Cargar eventos de un partido específico
@st.cache_data
def load_match_passes(match_id):
    events = sb.events(match_id=match_id)

    # Filtrar solo eventos de tipo Pass
    passes = events[events["type"] == "Pass"].copy()
    passes.reset_index(drop=True, inplace=True)

    # Extracción de coordenadas (x, y)
    passes["x0"] = passes.location.apply(lambda x: x[0])
    passes["y0"] = passes.location.apply(lambda x: x[1])
    passes["x1"] = passes.pass_end_location.apply(lambda x: x[0])
    passes["y1"] = passes.pass_end_location.apply(lambda x: x[1])

    return passes


# Cargar listado de partidos
matches_df = get_world_cup_matches()

# --- Barra lateral para la selección del partido ---
st.sidebar.header("Selección de Partido")

# Lista de selecciones ordenadas alfabéticamente
teams = sorted(
    list(
        set(
            matches_df["home_team"].tolist() + matches_df["away_team"].tolist()
        )
    )
)
selected_team = st.sidebar.selectbox("Selecciona una Selección:", teams)

# Filtrar partidos donde juegue la selección elegida
team_matches = matches_df[
    (matches_df["home_team"] == selected_team)
    | (matches_df["away_team"] == selected_team)
]

# Selector de partido específico
match_selected_label = st.sidebar.selectbox(
    "Selecciona el Partido:", team_matches["match_label"].tolist()
)

# Obtener el ID del partido seleccionado
match_id = team_matches[team_matches["match_label"] == match_selected_label][
    "match_id"
].values[0]

# --- Cargar datos del partido seleccionado ---
passes_df = load_match_passes(match_id)

st.subheader(f"Partido: {match_selected_label}")

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

# Dibujar la cancha
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

# Tabla opcional con los detalles
with st.expander("Ver detalles de los pases en este minuto"):
    st.dataframe(
        data_minuto[
            ["minute", "second", "team", "player", "pass_recipient", "type"]
        ]
    )
