import sys
from pathlib import Path

import streamlit as st

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

from utils.styling import load_css  # noqa: E402

st.set_page_config(page_title="Metodología", layout="wide")
load_css()


def app():
    st.title("Metodología y Fundamentos Matemáticos")

    st.header("1. Estimador de Pendiente de Sen (Sen's Slope)")
    st.latex(r"""
    \beta = Median \left( \frac{x_j - x_k}{j - k} \right) \quad \text{para todo } k < j
    """)
    st.markdown(
        "Es un estimador no paramétrico robusto ante valores atípicos (outliers) utilizado para determinar la magnitud de la tendencia."
    )

    st.header("2. Test de Mann-Kendall con Pre-Whitening (TFPW)")
    st.markdown(
        "Para eliminar el efecto de la autocorrelación serial (Lag-1) que suele inflar la significancia estadística."
    )
    st.latex(r"""
    S = \sum_{k=1}^{n-1} \sum_{j=k+1}^n \text{sgn}(x_j - x_k)
    """)

    st.header("3. Test de Pettitt")
    st.markdown("Detección de puntos de cambio estructurales en la serie.")
    st.latex(r"""
    U_{t,N} = \sum_{i=1}^t \sum_{j=t+1}^N \text{sgn}(x_i - x_j)
    """)

    st.header("4. Bootstrap")
    st.markdown(
        "Cálculo del IC al 95% remuestreando los residuos con repetición (N=1000)."
    )


if __name__ == "__main__":
    app()
