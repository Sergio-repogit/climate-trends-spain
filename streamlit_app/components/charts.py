import plotly.express as px


def create_timeseries_plot(df, x_col, y_col, color_col=None, title="Serie Temporal"):
    fig = px.line(
        df, x=x_col, y=y_col, color=color_col, title=title, template="plotly_white"
    )
    fig.update_layout(hovermode="x unified")
    return fig


def create_scatter_with_regression(df, x_col, y_col, title="Scatter", hover_name=None):
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        trendline="ols",
        template="plotly_white",
        title=title,
        hover_name=hover_name,
    )
    return fig
