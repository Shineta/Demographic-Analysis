import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List

def create_population_heatmap(df: pd.DataFrame, swap_axes: bool = False, color_scheme: str = 'Blues') -> go.Figure:
    """
    Create a population heatmap showing grade vs module with people counts
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for population heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Create pivot table - swap axes if requested
    if swap_axes:
        pivot_data = df.pivot_table(
            index='EntityDesc', 
            columns='Grade', 
            values='TOTAL', 
            aggfunc='sum', 
            fill_value=0
        )
    else:
        pivot_data = df.pivot_table(
            index='Grade', 
            columns='EntityDesc', 
            values='TOTAL', 
            aggfunc='sum', 
            fill_value=0
        )
    
    if pivot_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid data for population analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Prepare data for heatmap
    z_data = pivot_data.values
    
    if swap_axes:
        # Modules on y-axis, grades on x-axis
        y_labels = []
        for module in pivot_data.index:
            if len(module) > 30:
                y_labels.append(module[:27] + "...")
            else:
                y_labels.append(module)
        x_labels = [str(grade) for grade in pivot_data.columns]
    else:
        # Grades on y-axis, modules on x-axis (original)
        y_labels = [str(grade) for grade in pivot_data.index]
        x_labels = []
        for module in pivot_data.columns:
            if len(module) > 20:
                x_labels.append(module[:17] + "...")
            else:
                x_labels.append(module)
    
    # Create hover text matrix
    hover_text = []
    for i, row_label in enumerate(pivot_data.index):
        hover_row = []
        for j, col_label in enumerate(pivot_data.columns):
            count = pivot_data.iloc[i, j]
            if swap_axes:
                # Module on y-axis, grade on x-axis
                hover_info = (
                    f"<b>Module:</b> {row_label}<br>"
                    f"<b>Grade:</b> {col_label}<br>"
                    f"<b>Total People:</b> {int(count)}"
                )
            else:
                # Grade on y-axis, module on x-axis
                hover_info = (
                    f"<b>Grade:</b> {row_label}<br>"
                    f"<b>Module:</b> {col_label}<br>"
                    f"<b>Total People:</b> {int(count)}"
                )
            hover_row.append(hover_info)
        hover_text.append(hover_row)
    
    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        customdata=hover_text,
        hovertemplate='%{customdata}<extra></extra>',
        colorscale=color_scheme,
        colorbar=dict(
            title=dict(text="Number of People", font=dict(size=12)),
            x=1.02,
            len=0.8,
            thickness=25,
            tickfont=dict(size=11)
        ),

        showscale=True
    ))
    
    # Update layout based on axis orientation
    if swap_axes:
        title_text = "Population Distribution: Module vs Grade"
        x_title = "Grade Level"
        y_title = "Modules/Lessons"
        x_angle = 0
        y_angle = 0
        x_font_size = 12
        y_font_size = 9
    else:
        title_text = "Population Distribution: Grade vs Module"
        x_title = "Modules/Lessons"
        y_title = "Grade Level"
        x_angle = 90
        y_angle = 0
        x_font_size = 10
        y_font_size = 12
    
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title=x_title,
            tickangle=x_angle,
            side='bottom',
            tickfont=dict(size=x_font_size),
            automargin=True
        ),
        yaxis=dict(
            title=y_title,
            tickfont=dict(size=y_font_size),
            automargin=True
        ),
        template='plotly_white',
        height=max(500, len(y_labels) * 50 + 200),
        width=max(1000, len(x_labels) * 80 + 300),
        margin=dict(l=100, r=150, t=100, b=200),
        font=dict(size=10)
    )
    
    return fig

def create_grade_summary_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a summary bar chart showing total people per grade
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate total people per grade
    grade_totals = df.groupby('Grade')['TOTAL'].sum().reset_index()
    grade_totals = grade_totals.sort_values('Grade')
    
    # Create bar chart
    fig = go.Figure(data=go.Bar(
        x=grade_totals['Grade'],
        y=grade_totals['TOTAL'],
        marker_color='lightblue',
        text=grade_totals['TOTAL'],
        textposition='auto',
        hovertemplate='<b>Grade:</b> %{x}<br><b>Total People:</b> %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="Total People by Grade Level",
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title="Grade Level",
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title="Total People",
            tickfont=dict(size=11)
        ),
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=80, b=60)
    )
    
    return fig

def create_module_summary_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a summary bar chart showing total people per module
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate total people per module
    module_totals = df.groupby('EntityDesc')['TOTAL'].sum().reset_index()
    module_totals = module_totals.sort_values('TOTAL', ascending=True)
    
    # Truncate long module names
    module_totals['Short_Name'] = module_totals['EntityDesc'].apply(
        lambda x: x[:40] + "..." if len(x) > 40 else x
    )
    
    # Create horizontal bar chart
    fig = go.Figure(data=go.Bar(
        x=module_totals['TOTAL'],
        y=module_totals['Short_Name'],
        orientation='h',
        marker_color='lightcoral',
        text=module_totals['TOTAL'],
        textposition='auto',
        hovertemplate='<b>Module:</b> %{customdata}<br><b>Total People:</b> %{x}<extra></extra>',
        customdata=module_totals['EntityDesc']
    ))
    
    fig.update_layout(
        title=dict(
            text="Total People by Module",
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title="Total People",
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title="Modules/Lessons",
            tickfont=dict(size=9)
        ),
        template='plotly_white',
        height=max(600, len(module_totals) * 20 + 150),
        margin=dict(l=200, r=50, t=80, b=60)
    )
    
    return fig