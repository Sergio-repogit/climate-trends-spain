import streamlit as st


def render_kpi_card(title, value, delta=None, help_text=None):
    """Tarjeta KPI personalizada"""
    st.metric(label=title, value=value, delta=delta, help=help_text)


def render_trend_indicator(slope, p_value=0.01):
    """Indicador visual de tendencia con significancia"""
    if p_value < 0.05:
        if slope > 0:
            return " ↑ Calentamiento significativo"
        else:
            return " ↓ Enfriamiento significativo"
    else:
        return " ≈ Sin tendencia significativa"
