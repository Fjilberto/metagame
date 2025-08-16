import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from adjustText import adjust_text
import dash_bootstrap_components as dbc
from scipy.stats import norm
#import locale
import plotly.express as px

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# ========== CARGAR DATOS ==========

try:
    meta = pd.read_excel("metaR.xlsx")
    cruces = pd.read_excel("cruces.xlsx")
except FileNotFoundError as e:
    # Si los archivos no se encuentran, la app se iniciará y mostrará este error
    app.layout = html.Div([
        html.H1("Error de carga de datos"),
        html.P(f"No se pudieron encontrar los archivos de datos. Asegúrate de que los archivos metaR.xlsx y cruces.xlsx estén en la misma carpeta que tu código. Error: {e}"),
    ])
    meta = pd.DataFrame() # DataFrame vacío para evitar errores posteriores
    cruces = pd.DataFrame() # DataFrame vacío
except Exception as e:
    # Capturar cualquier otro error durante la lectura de los archivos
    app.layout = html.Div([
        html.H1("Error inesperado al cargar datos"),
        html.P(f"Ocurrió un error inesperado al leer los archivos de datos. Error: {e}"),
    ])
    meta = pd.DataFrame()
    cruces = pd.DataFrame()

# Convertir fechas
meta['Fecha'] = pd.to_datetime(meta['Fecha'], format='%Y.%m.%d',errors='coerce')
cruces['fecha'] = pd.to_datetime(cruces['fecha'], format='%Y.%m.%d',errors='coerce')

# Convertir Top1 y Top3 a numérico
meta['Top1'] = pd.to_numeric(meta['Top1'])
meta['Top3'] = pd.to_numeric(meta['Top3'])

# Definir eventos
eventos = {
    "Mazos jugados desde el baneo/desbaneo Deadly, Tide y otros": datetime(2025, 3, 31),
    "Mazos jugados desde el baneo de All That Glitters": datetime(2024, 5, 13),
    "Mazos jugados desde el baneo de Monastery Swiftspear": datetime(2023, 12, 4)
}

# Configurar locale a español
#try:
#    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para Linux/Mac
#except:
#    locale.setlocale(locale.LC_TIME, 'spanish')  # Para Windows

# ========== UI ==========
app.layout = dbc.Container([
    html.H1("Metagame torneos Pauper", className="mt-3 mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Tabs(
                        id="tabs",
                        value="metagame",
                        vertical=True,
                        parent_style={
                            'width': '250px',  # Aumentar este valor para hacerlo más ancho
                            'min-width': '250px',  # Ancho mínimo garantizado
                            'margin-right': '20px'  # Espacio entre pestañas y contenido
                        },
                        style={
                            'height': '100%',
                            'border-right': '1px solid #d6d6d6',
                            'background': '#f8f9fa'  # Fondo ligeramente diferenciado
                        },
                        children=[
                            dcc.Tab(
                                label="Metagame",
                                value="metagame",
                                style={
                                    'padding': '12px 20px',  # Más espacio interno (arriba/abajo, izquierda/derecha)
                                    'font-size': '14px',
                                    'text-align': 'left',
                                    'margin-bottom': '8px'  # Más espacio entre pestañas
                                },
                                selected_style={
                                    'border-left': '4px solid #007bff',
                                    'font-weight': 'bold',
                                    'background-color': '#e9ecef'  # Fondo cuando está seleccionado
                                }
                            ),
                            dcc.Tab(
                                label="Torneos ganados o podios",
                                value="top_distribution",
                                style={'margin-bottom': '5px', 'padding': '10px', 'font-size': '14px'},
                                selected_style={'border-bottom': '3px solid #007bff', 'font-weight': 'bold'}
                            ),
                            dcc.Tab(
                                label="Presencia mensual",
                                value="evolution",
                                style={'margin-bottom': '5px', 'padding': '10px', 'font-size': '14px'},
                                selected_style={'border-bottom': '3px solid #007bff', 'font-weight': 'bold'}
                            ),
                            dcc.Tab(
                                label="Winrate por mazo",
                                value="winrate",
                                style={'margin-bottom': '5px', 'padding': '10px', 'font-size': '14px'},
                                selected_style={'border-bottom': '3px solid #007bff', 'font-weight': 'bold'}
                            ),
                            dcc.Tab(
                                label="Winrate vs Porcentaje de Juego",
                                value="winrate_juego",
                                style={'margin-bottom': '5px', 'padding': '10px', 'font-size': '14px'},
                                selected_style={'border-bottom': '3px solid #007bff', 'font-weight': 'bold'}
                            ),
                            dcc.Tab(
                                label="Cruces entre mazos",
                                value="heatmap",
                                style={'padding': '10px', 'font-size': '14px'},
                                selected_style={'border-bottom': '3px solid #007bff', 'font-weight': 'bold'}
                            ),
                        ]
                    ),
                    
                    # Filtros condicionales
                    html.Div(id="filtro-metagame", children=[
                        dbc.RadioItems(
                            id="filtro-metagame-radio",
                            options=[
                                {"label": "Por evento", "value": "evento"},
                                {"label": "Por rango de fechas", "value": "fechas"},
                                {"label": "Torneo específico", "value": "fecha_puntual"}
                            ],
                            value="evento"
                        )
                    ], style={'display': 'none'}),
                    
                    html.Div(id="filtro-winrate", children=[
                        dbc.RadioItems(
                            id="filtro-winrate-radio",
                            options=[
                                {"label": "Por evento", "value": "evento"},
                                {"label": "Por rango de fechas", "value": "fechas"}
                            ],
                            value="evento"
                        )
                    ], style={'display': 'none'}),
                    
                    html.Div(id="filtro-heatmap", children=[
                        dbc.RadioItems(
                            id="filtro-heatmap-radio",
                            options=[{"label": "Por evento", "value": "evento"}],
                            value="evento"
                        )
                    ], style={'display': 'none'}),
                    
                    # Selector de evento (compartido)
                    dcc.Dropdown(
                        id="evento-dropdown",
                        options=[{"label": k, "value": k} for k in eventos.keys()],
                        style={'font-size': '12px'},
                        value=list(eventos.keys())[0],
                        disabled=False,
                        className="mb-3"
                    ),
                    
                    # Selector de rango de fechas
                    dcc.DatePickerRange(
                        id="fechas-picker",
                        start_date=meta['Fecha'].min(),
                        end_date=meta['Fecha'].max(),
                        display_format='YYYY-MM-DD',
                        disabled=True,
                        className="mb-3"
                    ),
                    
                    # Selector de fecha puntual
                    dcc.Dropdown(
                        id="fecha-unica-dropdown",
                        options=[{"label": str(date.date()), "value": date} 
                                for date in sorted(meta['Fecha'].unique(), reverse=True)],
                        disabled=True,
                        className="mb-3"
                    ),
                    
                    # Selector de color para Winrate vs Porcentaje
                    dcc.Dropdown(
                        id="color-opcion-dropdown",
                        options=[
                            {"label": "Torneos ganados", "value": "Top1"},
                            {"label": "Presencia en podio", "value": "Top3"}
                        ],
                        value="Top1",
                        disabled=True,
                        className="mb-3"
                    ),
                    
                    html.Label("Top mazos más jugados:"),
                    dcc.Slider(
                        id='top-mazos-slider',
                        min=5,
                        max=20,
                        step=1,
                        value=10,
                        marks={i: str(i) for i in range(5, 21, 5)}
                    ),

                    html.Label("Cantidad mazos más jugados"),
                    dcc.Slider(
                        id='top-mazos-slider2',
                        min=3,
                        max=8,
                        step=1,
                        value=5,
                        marks={i: str(i) for i in range(3, 9)}
                    ),

                    html.Label("Minimo de partidas:"),
                    dcc.Slider(
                        id="min-juegos-slider",
                        min=20,
                        max=50,
                        step=1,
                        value=30,
                        marks={i: str(i) for i in range(20, 51, 5)},
                        tooltip={"placement": "bottom", "always_visible": True},
                        #disabled=True,
                        className="mb-4"
                    )
                ])
            ])
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="tab-content")
                ])
            ], style={"height": "650px"})
        ], md=9)
    ])
], fluid=True)

# ========== CALLBACKS ==========
# ========== CALLBACKS ==========
@app.callback(
    [Output("filtro-metagame", "style"),
     Output("filtro-winrate", "style"),
     Output("filtro-heatmap", "style"),
     Output("evento-dropdown", "disabled"),
     Output("fechas-picker", "disabled"),
     Output("fecha-unica-dropdown", "disabled"),
     Output("color-opcion-dropdown", "disabled"),
     Output("min-juegos-slider", "disabled"),
     Output("top-mazos-slider", "disabled"),
     Output("top-mazos-slider2", "disabled")],
    [Input("tabs", "value")]
)
def update_filtros_visibilidad(tab):
    if tab == "metagame":
        return (
            {"display": "block"}, {"display": "none"}, {"display": "none"},
            False, False, False, True, True, False, True  # top-mazos-slider2 deshabilitado
        )
    elif tab == "winrate":
        return (
            {"display": "none"}, {"display": "none"}, {"display": "none"},
            False, True, True, True, False, True, True
        )
    elif tab == "winrate_juego":
        return (
            {"display": "none"}, {"display": "block"}, {"display": "none"},
            False, False, True, False, True, True, True
        )
    elif tab == "heatmap":
        return (
            {"display": "none"}, {"display": "none"}, {"display": "block"},
            False, True, True, True, False, True, True
        )
    elif tab == "top_distribution":
        return (
            {"display": "none"}, {"display": "none"}, {"display": "none"},
            False, True, True, False, True, True, True
        )
    elif tab == "evolution":
        return (
            {"display": "none"}, {"display": "none"}, {"display": "none"},
            False, True, True, True, True, True, False  # Solo top-mazos-slider2 habilitado
        )

@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "value"),
     Input("filtro-metagame-radio", "value"),
     Input("filtro-winrate-radio", "value"),
     Input("filtro-heatmap-radio", "value"),
     Input("evento-dropdown", "value"),
     Input("fechas-picker", "start_date"),
     Input("fechas-picker", "end_date"),
     Input("fecha-unica-dropdown", "value"),
     Input("color-opcion-dropdown", "value"),
     Input("top-mazos-slider", "value"),
     Input("top-mazos-slider2", "value"),
     Input("min-juegos-slider", "value")]
)
def update_tab_content(tab, filtro_metagame=None, filtro_winrate=None, filtro_heatmap=None,
                     evento=None, start_date=None, end_date=None, fecha_unica=None,
                     color_opcion=None, n_top=None, n_top_evolution=None, min_juegos=None):
    
    # Filtrar datos según la pestaña activa
    if tab == "metagame":
        if filtro_metagame == "evento":
            fecha_corte = eventos[evento]
            df_filtrado = meta[meta['Fecha'] >= fecha_corte]
        elif filtro_metagame == "fechas":
            df_filtrado = meta[(meta['Fecha'] >= start_date) &
                              (meta['Fecha'] <= end_date)]
        else:  # fecha_puntual
            df_filtrado = meta[meta['Fecha'] == fecha_unica]

        return update_metagame(df_filtrado, filtro_metagame, evento, start_date, end_date, fecha_unica, n_top)
    
    elif tab == "evolution":
        fecha_corte = eventos[evento]
        df_filtrado = meta[meta['Fecha'] >= fecha_corte]
        return update_evolution(df_filtrado, n_top_evolution)  # Usar slider2 para evolución

    elif tab == "winrate":
        if filtro_winrate == "evento":
            fecha_corte = eventos[evento]
            df_filtrado = meta[meta['Fecha'] >= fecha_corte]
        else:
            df_filtrado = meta[(meta['Fecha'] >= start_date) &
                              (meta['Fecha'] <= end_date)]
        return update_winrate(df_filtrado, min_juegos)

    elif tab == "winrate_juego":
        if filtro_winrate == "evento":
            fecha_corte = eventos[evento]
            df_filtrado = meta[meta['Fecha'] >= fecha_corte]
        else:
            df_filtrado = meta[(meta['Fecha'] >= start_date) &
                              (meta['Fecha'] <= end_date)]
        return update_winrate_juego(df_filtrado, color_opcion)

    elif tab == "heatmap":
        fecha_corte = eventos[evento]
        df_filtrado = cruces[cruces['fecha'] >= fecha_corte]
        return update_heatmap(df_filtrado, min_juegos)
    
    elif tab == "top_distribution":
        fecha_corte = eventos[evento]
        df_filtrado = meta[meta['Fecha'] >= fecha_corte]
        return update_top_distribution(df_filtrado, color_opcion)
        
# ========== FUNCIONES PARA ACTUALIZAR GRÁFICOS ==========
def update_metagame(df, filtro, evento, start_date, end_date, fecha_unica, n_top=20):
    if df.empty:
        return dcc.Graph(figure=go.Figure().update_layout(
            title="No hay datos disponibles",
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='white',
            paper_bgcolor='white'
        ))

    # 1. Calcular frecuencia y agrupar en "Otros"
    conteo = df['Arquetipo'].value_counts().reset_index()
    conteo.columns = ['Arquetipo', 'Freq']

    if len(conteo) > n_top:
        top_mazos = conteo.head(n_top)
        otros_count = conteo['Freq'].iloc[n_top:].sum()
        otros = pd.DataFrame({'Arquetipo': ['Otros'], 'Freq': [otros_count]})
        conteo = pd.concat([top_mazos, otros]).sort_values('Freq')

    # 2. Crear gráfico según tipo de filtro
    if filtro == "fecha_puntual":
        fecha_formateada = pd.to_datetime(fecha_unica).strftime("%Y-%m-%d")
        fig = go.Figure(go.Pie(
            labels=conteo['Arquetipo'],
            values=conteo['Freq'],
            textinfo='label+value',
            marker=dict(colors=px.colors.qualitative.Set2),
            hole=0.3
        ))
        fig.update_layout(
            title=f"Mazos jugados el {fecha_formateada}",
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True
        )
    else:
        # Gráfico de barras horizontales
        fig = go.Figure(go.Bar(
            x=conteo['Freq'],
            y=conteo['Arquetipo'],
            orientation='h',
            marker_color='dodgerblue',
            hoverinfo='text',
            hovertext=[f"{row['Arquetipo']}: {row['Freq']} apariciones" for _, row in conteo.iterrows()]
        ))
        
        title = (evento if filtro == "evento" 
                else f"Mazos desde {start_date} a {end_date}")
        
        fig.update_layout(
            title=f"{title} (Top {n_top} + Otros)" if len(conteo) > n_top else title,
            xaxis_title="Apariciones",
            yaxis_title="Mazos",
            plot_bgcolor='white',
            paper_bgcolor='white',
            yaxis=dict(
                tickfont=dict(size=9),
                automargin=True,
                tickangle=-15
            ),
            height=700,
            margin=dict(l=100)
        )
    
    return dcc.Graph(figure=fig)

def update_top_distribution(df, top_type):
    # Agrupar por arquetipo y sumar Top1 o Top3 según corresponda
    stats = df.groupby('Arquetipo')[top_type].sum().reset_index()
    stats.columns = ['Arquetipo', 'Count']
    
    # Filtrar solo mazos con al menos un top
    stats = stats[stats['Count'] > 0].sort_values('Count', ascending=False)
    
    if stats.empty:
        return dcc.Graph(figure=go.Figure().update_layout(
            title="No hay datos disponibles",
            xaxis={"visible": False},
            yaxis={"visible": False},
            plot_bgcolor='white',
            paper_bgcolor='white'
        ))
    
    # Agrupar mazos menores como "Otros" si hay muchos
    #if len(stats) > 10:
    #    top_mazos = stats.head(10)
    #    otros_count = stats['Count'].iloc[10:].sum()
    #    otros = pd.DataFrame({'Arquetipo': ['Otros'], 'Count': [otros_count]})
    #    stats = pd.concat([top_mazos, otros])
    
    # Crear gráfico de pie interactivo
    fig = go.Figure(go.Pie(
        labels=stats['Arquetipo'],
        values=stats['Count'],
        textinfo='label+percent',
        insidetextorientation='radial',
        marker=dict(colors=px.colors.qualitative.Pastel),
        hole=0.3,
        hoverinfo='label+value+percent',
        texttemplate='%{label}<br>%{value} (%{percent})',
        pull=[0.1 if i == 0 else 0 for i in range(len(stats))]  # Destacar el primer segmento
    ))
    
    # Configurar título y diseño
    title = f"Distribución de {top_type} - {len(df['Fecha'].unique())} torneos"
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),
        height=650,
        margin=dict(t=100, b=100)
    )
    
    return dcc.Graph(figure=fig)

def update_evolution(df, n_top=5):
    # Procesamiento de datos
    df = df.copy()
    df['Mes'] = df['Fecha'].dt.to_period('M').dt.to_timestamp()
    
    # Calcular frecuencia mensual y porcentaje
    monthly_counts = df.groupby(['Mes', 'Arquetipo']).size().unstack(fill_value=0)
    monthly_pct = monthly_counts.div(monthly_counts.sum(axis=1), axis=0) * 100
    
    # Seleccionar top mazos (basado en el total general)
    top_mazos = monthly_counts.sum().sort_values(ascending=False).head(n_top).index
    monthly_top_pct = monthly_pct[top_mazos]
    
    # Filtrar meses sin datos
    monthly_top_pct = monthly_top_pct[monthly_top_pct.sum(axis=1) > 0]
    
    # Calcular porcentaje acumulado de los top mazos
    monthly_top_pct['Acumulado Top'] = monthly_top_pct.sum(axis=1)
    
    # Crear gráfico
    fig = go.Figure()
    
    # Colores distintivos
    colors = px.colors.qualitative.Plotly

    # Diccionario meses
    MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
# Añadir cada mazo como línea con puntos (porcentaje individual)
    for i, mazo in enumerate(top_mazos):
        fig.add_trace(go.Scatter(
            x=monthly_top_pct.index,
            y=monthly_top_pct[mazo],
            name=mazo,
            mode='lines+markers',
            marker=dict(
                size=8,
                color=colors[i],
                symbol='circle',
                line=dict(width=1, color='DarkSlateGrey')
            ),
            line=dict(width=2, color=colors[i]),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Mes: %{customdata[0]} %{x|%Y}<br>"
                "Porcentaje: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
            text=[mazo]*len(monthly_top_pct),
            customdata=np.column_stack([
                [MESES_ES[mes.month] for mes in monthly_top_pct.index],
                monthly_top_pct['Acumulado Top']
            ])
        ))

# Añadir línea de acumulado
    fig.add_trace(go.Scatter(
        x=monthly_top_pct.index,
        y=monthly_top_pct['Acumulado Top'],
        name=f'Acumulado Top {n_top}',
        mode='lines',
        line=dict(color='black', width=3, dash='dot'),
        hovertemplate=(
            "<b>Acumulado Top {n_top}</b><br>"
            "Mes: %{customdata} %{x|%Y}<br>"
            "Porcentaje total: %{y:.1f}%"
            "<extra></extra>"
        ),
        customdata=[MESES_ES[mes.month] for mes in monthly_top_pct.index]
    ))
    
    # Añadir líneas de eventos (versión robusta)
    for evento, fecha_str in eventos.items():
        try:
            fecha_dt = pd.to_datetime(fecha_str)
            if fecha_dt >= df['Fecha'].min() and fecha_dt <= df['Fecha'].max():
                fig.add_vline(
                    x=fecha_dt.timestamp() * 1000,
                    line_width=1.5,
                    line_dash="dash",
                    line_color="#FF6B6B",
                    opacity=0.8,
                    annotation_text=evento.replace("Mazos jugados desde el ", ""),
                    annotation_position="top right",
                    annotation_font_size=10,
                    annotation_bgcolor="rgba(255,255,255,0.9)"
                )
        except Exception as e:
            print(f"Error al procesar evento {evento}: {str(e)}")
            continue
    
    # Crear etiquetas inteligentes para el eje X (año solo cuando cambie)
    ticktext = []
    prev_year = None
    for fecha in monthly_top_pct.index:
        current_year = fecha.strftime("%Y")
        month_name = fecha.strftime("%B").capitalize()  # Nombre completo en español
    
        if current_year != prev_year:
            ticktext.append(f"{month_name}\n{current_year}")
            prev_year = current_year
        else:
            ticktext.append(month_name)
    
    # Configuración definitiva del eje X
    fig.update_xaxes(
        tickvals=monthly_top_pct.index,
        ticktext=ticktext,
        tickangle=45,
        tickfont=dict(size=10),
        range=[
            monthly_top_pct.index.min() - pd.Timedelta(days=15),
            monthly_top_pct.index.max() + pd.Timedelta(days=15)
        ]
    )
    
    # Configuración del layout
    fig.update_layout(
        title=f'Porcentaje Mensual de Juego (Top {n_top} mazos)',
        xaxis_title='Mes',
        yaxis_title='Porcentaje del Metagame (%)',
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=650,
        legend=dict(  # Configuración CORREGIDA de la leyenda
            orientation="h",
            yanchor="top",
            y=-0.3,  # Posición bajo el gráfico
            xanchor="center",
            x=0.5,
            font=dict(size=10)  # <-- Se eliminó la coma final que causaba el error
        ),
        margin=dict(b=150, t=60, l=60, r=40)  # Márgenes ajustados
    )
    
    # Configuración del eje Y
    fig.update_yaxes(
        rangemode="tozero",
        ticksuffix="%",
        gridcolor='rgba(0,0,0,0.1)'
    )
    
    return dcc.Graph(figure=fig)

def update_winrate(df, min_juegos):
    # Calcular estadísticas por arquetipo
    stats = df.groupby('Arquetipo').agg({
        'Standing': 'count',
        'Wins': 'sum',
        'Loses': 'sum',
        'Draws': 'sum',
        'Top1': 'sum',
        'Top3': 'sum'
    }).reset_index()
    
    stats.columns = ['Arquetipo', 'players', 'win', 'lose', 'draw', 'top1', 'top3']
    
    stats['n'] = stats['win'] + stats['lose'] + stats['draw']
    stats = stats[stats['n'] >= min_juegos]
    
    if stats.empty:
        return dcc.Graph(figure=go.Figure().update_layout(
            title=f"No hay datos con ≥{min_juegos} juegos",
            xaxis={"visible": False},
            yaxis={"visible": False}
        ))
    
    # Calcular winrate e intervalos de confianza
    stats['perwinrate'] = round(stats['win'] / stats['n'] * 100, 2)
    stats['perwinrate2'] = stats['win'] / stats['n']
    
    z = norm.ppf(1 - 0.05/2)
    stats['upper'] = 100 * (stats['perwinrate2'] + z * np.sqrt(stats['perwinrate2'] * (1 - stats['perwinrate2']) / stats['n']))
    stats['lower'] = 100 * (stats['perwinrate2'] - z * np.sqrt(stats['perwinrate2'] * (1 - stats['perwinrate2']) / stats['n']))
    
    stats = stats.sort_values('perwinrate')
    
    # Crear gráfico
    fig = go.Figure()
    
    # Añadir puntos
    fig.add_trace(go.Scatter(
        x=stats['Arquetipo'],
        y=stats['perwinrate'],
        mode='markers',
        marker=dict(size=10, color='rgba(55, 128, 191, 0.7)'),
        hoverinfo='text',
        text=[f"Arquetipo: {row['Arquetipo']}<br>Winrate: {row['perwinrate']}%<br>Juegos: {row['n']}<br>Victorias: {row['win']}<br>Derrotas: {row['lose']}<br>Empates: {row['draw']}"
              for _, row in stats.iterrows()],
        name='Winrate'
    ))
    
    # Añadir barras de error
    for _, row in stats.iterrows():
        fig.add_shape(
            type='line',
            x0=row['Arquetipo'], y0=row['lower'],
            x1=row['Arquetipo'], y1=row['upper'],
            line=dict(color='rgba(55, 128, 191, 0.7)', width=1.5)
        )
    
    # Añadir líneas de referencia
    fig.add_hline(y=50, line_dash="dash", line_color="black")
    fig.add_hline(y=40, line_dash="dash", line_color="red")
    fig.add_hline(y=60, line_dash="dash", line_color="red")
    
    fig.update_layout(
        title=f"Winrate + IC 95% por Mazo (juegos ≥{min_juegos})",
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            title="",
            tickangle=45,
            automargin=True,
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title="Winrate (%)",
            range=[0, 100],
            showgrid=False,
            zeroline=False
        ),
        showlegend=False,
        height=700,
        margin=dict(b=100)
    )
    
    return dcc.Graph(figure=fig)

def update_winrate_juego(df, color_opcion):
    # Calcular estadísticas
    stats = df.groupby('Arquetipo').agg({
        'Standing': 'count',
        'Wins': 'sum',
        'Loses': 'sum',
        'Draws': 'sum',
        'Top1': 'sum',
        'Top3': 'sum'
    }).reset_index()
    
    stats.columns = ['Arquetipo', 'players', 'win', 'lose', 'draw', 'top1', 'top3']
    
    stats['n'] = stats['win'] + stats['lose'] + stats['draw']
    stats['perwinrate'] = round(stats['win'] / stats['n'] * 100, 2)
    stats['perjuego'] = round(stats['n'] / stats['n'].sum() * 100, 2)
    stats = stats[stats['perjuego'] > 1].reset_index(drop=True)
    
    # Variable de color según selección
    color_var = 'top1' if color_opcion == "Top1" else 'top3'
    color_title = "Torneos ganados" if color_opcion == "Top1" else "Podios (Top3)"
    
    # Crear gráfico interactivo con adjustText
    fig = go.Figure()

    # --------------------------------------------------------------------------------------
    #  CAMBIO CLAVE: AHORA SE CREAN DOS TIPOS DE TRAZAS
    #  1. UNA PARA LOS PUNTOS DEL GRÁFICO (CON TAMAÑO DINÁMICO)
    #  2. OTRA PARA LA LEYENDA (CON TAMAÑO FIJO)
    # --------------------------------------------------------------------------------------
    # Obtener los valores únicos de la columna de color y ordenarlos
    valores_unicos = sorted(stats[color_var].unique())

    # Mapeo de colores: azul para 0, escala de rojos para el resto
    mapeo_colores = {}
    valores_mayores_cero = [v for v in valores_unicos if v > 0]
    
    if 0 in valores_unicos:
        # Asignar un color azul al valor 0
        mapeo_colores[0] = 'rgb(31, 119, 180)'
        
    if valores_mayores_cero:
        # Crear una escala de rojos que va de claro a oscuro
        escala_rojos = px.colors.sequential.Reds[2:]
        pasos_rojos = [escala_rojos[i] for i in range(len(valores_mayores_cero))]

        for i, val in enumerate(valores_mayores_cero):
            # Asignar los colores de la escala de rojos
            mapeo_colores[val] = pasos_rojos[i]

    # Añadir una traza principal para los puntos del gráfico
    # con el tamaño dinámico
    fig.add_trace(go.Scatter(
        x=stats['perjuego'],
        y=stats['perwinrate'],
        mode='markers',
        marker=dict(
            size=stats['perjuego'] * 2,
            # color se asigna por una lista de colores mapeados para cada punto
            color=[mapeo_colores[val] for val in stats[color_var]],
        ),
        hoverinfo='text',
        text=[f"Arquetipo: {row['Arquetipo']}<br>Winrate: {row['perwinrate']}%<br>Juegos: {row['n']}<br>% Juego: {row['perjuego']}%<br>Top1: {row['top1']}<br>Top3: {row['top3']}"
              for _, row in stats.iterrows()],
        showlegend=False, # <-- OCULTAMOS LA LEYENDA DE ESTA TRAZA PRINCIPAL
        name=''
    ))
    
    # Añadir trazas separadas para la leyenda, con un tamaño fijo
    for valor_color in valores_unicos:
        fig.add_trace(go.Scatter(
            x=[None],  # Puntos invisibles para el gráfico
            y=[None],
            mode='markers',
            marker=dict(
                size=12,  # <-- TAMAÑO FIJO PARA LA LEYENDA
                color=mapeo_colores[valor_color],
            ),
            name=f'{color_title}: {valor_color}'
        ))
    # --------------------------------------------------------------------------------------
    
    # Añadir líneas de referencia
    fig.add_hline(y=50, line_dash="dash", line_color="black")
    fig.add_hline(y=40, line_dash="dash", line_color="red")
    fig.add_hline(y=60, line_dash="dash", line_color="red")
    
    # Añadir etiquetas de texto
    annotations = []
    for _, row in stats.iterrows():
        annotations.append(dict(
            x=row['perjuego'],
            y=row['perwinrate'],
            text=row['Arquetipo'],
            showarrow=False,
            font=dict(size=10),
            xanchor='center',
            yanchor='bottom'
        ))
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            title="Porcentaje de Juego (%)",
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            title="Winrate (%)",
            showgrid=False,
            zeroline=False,
            range=[10, 80]
        ),
        annotations=annotations,
        height=700,
        showlegend=True,
        legend_title_text=color_title
    )
    
    return dcc.Graph(figure=fig)

def update_heatmap(df_filtrado, min_juegos=30):
    if df_filtrado.empty:
        return dcc.Graph(figure=go.Figure().update_layout(
            title="No hay datos disponibles para el heatmap",
            xaxis={"visible": False},
            yaxis={"visible": False}
        ))
    
    try:
        # 1. Crear copia explícita para trabajar
        df_working = df_filtrado.copy()
        
        # 2. Crear combinación única de mazos
        df_working['cruce'] = df_working.apply(
            lambda row: ' - '.join(sorted([str(row['mazo1']), str(row['mazo2'])])), 
            axis=1
        )
        
        # 3. Calcular resultados por cruce
        resultados = []
        for _, row in df_working.iterrows():
            total_partidas = row['v1'] + row['v2']
            resultados.append({
                'mazo': row['mazo1'],
                'vs_mazo': row['mazo2'],
                'victorias': row['v1'],
                'total_partidas': total_partidas,
                'cruce': row['cruce']
            })
            resultados.append({
                'mazo': row['mazo2'],
                'vs_mazo': row['mazo1'],
                'victorias': row['v2'],
                'total_partidas': total_partidas,
                'cruce': row['cruce']
            })
        
        heatmap_data = pd.DataFrame(resultados)
        
        # 4. Agrupar y calcular winrates
        heatmap_stats = heatmap_data.groupby(['mazo', 'vs_mazo']).agg({
            'victorias': 'sum',
            'total_partidas': 'sum'
        }).reset_index()
        
        heatmap_stats['winrate'] = round(
            (heatmap_stats['victorias'] / heatmap_stats['total_partidas'].replace(0, 1)) * 100, 
            1
        )
        
        # 5. Filtrar mazos con pocas partidas
        mazo_counts = heatmap_data.groupby('mazo')['total_partidas'].sum()
        mazos_validos = mazo_counts[mazo_counts >= min_juegos].index
        
        heatmap_stats = heatmap_stats[
            heatmap_stats['mazo'].isin(mazos_validos) & 
            heatmap_stats['vs_mazo'].isin(mazos_validos)
        ]
        
        # 6. Crear matriz completa
        all_mazos = sorted(pd.unique(pd.concat([
            heatmap_stats['mazo'], 
            heatmap_stats['vs_mazo']
        ])))
        
        complete_grid = pd.DataFrame(
            index=all_mazos,
            columns=all_mazos
        )
        
        # 7. Llenar matriz con winrates (excluyendo diagonal)
        for _, row in heatmap_stats.iterrows():
            if row['mazo'] != row['vs_mazo']:  # Excluir diagonal
                complete_grid.loc[row['mazo'], row['vs_mazo']] = row['winrate']
        
        # 8. Preparar texto para tooltips
        text_matrix = []
        hover_matrix = []
        for mazo_y in complete_grid.index:
            row_text = []
            row_hover = []
            for mazo_x in complete_grid.columns:
                if mazo_y == mazo_x:  # Diagonal
                    row_text.append("")
                    row_hover.append("")
                else:
                    value = complete_grid.loc[mazo_y, mazo_x]
                    if pd.notna(value):  # Celda con valor
                        # Buscar los datos originales para el tooltip
                        match_data = heatmap_stats[
                            (heatmap_stats['mazo'] == mazo_y) & 
                            (heatmap_stats['vs_mazo'] == mazo_x)
                        ]
                        if not match_data.empty:
                            v = int(match_data.iloc[0]['victorias'])
                            t = int(match_data.iloc[0]['total_partidas'])
                            row_text.append(f"{value:.0f}%")
                            row_hover.append(f"{mazo_y} vs {mazo_x}<br>Victorias: {v}<br>Juegos: {t}<br>Winrate: {value:.1f}%")
                        else:
                            row_text.append("")
                            row_hover.append("")
                    else:  # Celda sin datos
                        row_text.append("")
                        row_hover.append("")
            text_matrix.append(row_text)
            hover_matrix.append(row_hover)
        
        # 9. Calcular tamaño de fuente dinámico
        num_mazos = len(all_mazos)
        tamano_fuente = max(8, 40 / num_mazos**0.5)
        
        # 10. Crear heatmap corregido
        heatmap = go.Heatmap(
            x=all_mazos,
            y=all_mazos,
            z=complete_grid.values,
            colorscale=[[0, 'dodgerblue'], [0.5, 'whitesmoke'], [1.0, 'orangered']],
            zmin=0,
            zmax=100,
            hoverinfo='text',
            hovertext=hover_matrix,
            text=text_matrix,
            showscale=False,
            texttemplate="%{text}",  # Usar el texto preformateado
            textfont={"size": tamano_fuente}
        )
        
        # 11. Layout mejorado
        layout = go.Layout(
            title=f'Winrates entre Mazos (Mínimo {min_juegos} partidas por mazo)',
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                #title='Mazo Oponente',
                tickangle=45,
                showgrid=False,
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                #title='Mazo Jugador',
                autorange='reversed',
                showgrid=False,
                tickfont=dict(size=12)
            ),
            showlegend=False,
            margin=dict(l=100, r=50, t=100, b=100),
            height=max(600, num_mazos * 30)
        )
        
        return dcc.Graph(figure={'data': [heatmap], 'layout': layout})
    
    except Exception as e:
        print(f"Error al generar heatmap: {str(e)}")
        return dcc.Graph(figure=go.Figure().update_layout(
            title=f"Error al generar heatmap: {str(e)}",
            xaxis={"visible": False},
            yaxis={"visible": False}
        ))

#if __name__ == '__main__':
#    app.run(debug=True)
