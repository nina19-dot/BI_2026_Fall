import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from mplsoccer import Pitch
from statsbombpy import sb

# Configuración de la página
st.set_page_config(
    page_title="Visualizador de Pases - StatsBomb", layout="wide"
)
st.title("⚽ Visualizador de Pases por Minuto")


# Carga de datos optimizada con caché
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


# Cargar datos del partido (ejemplo: Japón en el Mundial 2022)
MATCH_ID = 3857255
passes_df = load_match_passes(MATCH_ID)

# Control de usuario: Slider de Streamlit (Reemplaza a ipywidgets)
min_minute = int(passes_df["minute"].min())
max_minute = int(passes_df["minute"].max())

minuto_seleccionado = st.slider(
    "Selecciona el minuto del partido:",
    min_value=min_minute,
    max_value=max_minute,
    value=1,
    step=1,
)

# Filtrar pases por el minuto seleccionado
data_minuto = passes_df[passes_df["minute"] == minuto_seleccionado]

# Renderizar la cancha con mplsoccer
pitch = Pitch(pitch_color="grass", line_color="white", stripe=True)
fig, ax = pitch.draw(figsize=(10, 6))

if not data_minuto.empty:
    sns.scatterplot(
        data=data_minuto,
        x="x0",
        y="y0",
        hue="team",
        ax=ax,
        s=100,
        edgecolor="black",
        zorder=3,
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=2)
else:
    st.info(f"No hay registros de pases en el minuto {minuto_seleccionado}.")

# Mostrar el gráfico en Streamlit
st.pyplot(fig)

# Tabla opcional con los pases del minuto
with st.expander("Ver detalles de los pases en este minuto"):
    st.dataframe(
        data_minuto[
            ["minute", "second", "team", "player", "pass_recipient", "type"]
        ]
    )
