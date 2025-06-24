import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List

def create_heatmap(df: pd.DataFrame, demographic_cols: List[str], targets: Dict[str, float]) -> go.Figure:
    """
    Create an interactive heatmap showing demographic representation vs targets
    
    Args:
        df: Input DataFrame
        demographic_cols: List of demographic column names
        targets: Dictionary of target percentages for each demographic
        
    Returns:
        Plotly figure object
    """
    if df.empty or not demographic_cols:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate percentages by EntityDesc
    heatmap_data = []
    
    for entity in df['EntityDesc'].unique():
        entity_data = df[df['EntityDesc'] == entity]
        total_people = entity_data['TOTAL'].sum()
        
        if total_people == 0:
            continue
        
        row_data = {'EntityDesc': entity}
        
        for demo_col in demographic_cols:
            if demo_col in entity_data.columns:
                demo_count = entity_data[demo_col].sum()
                percentage = (demo_count / total_people) * 100
                target = targets.get(demo_col, 0)
                
                # Calculate difference from target
                diff_from_target = percentage - target
                row_data[demo_col] = diff_from_target
            else:
                row_data[demo_col] = -targets.get(demo_col, 0)
        
        heatmap_data.append(row_data)
    
    if not heatmap_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid data for heatmap visualization",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Convert to DataFrame
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Prepare data for heatmap
    entities = heatmap_df['EntityDesc'].tolist()
    demographics = [col for col in demographic_cols if col in heatmap_df.columns]
    
    # Create matrix for heatmap
    z_data = []
    hover_text = []
    
    for entity in entities:
        entity_row = heatmap_df[heatmap_df['EntityDesc'] == entity].iloc[0]
        z_row = []
        hover_row = []
        
        for demo in demographics:
            diff = entity_row[demo] if demo in entity_row else 0
            target = targets.get(demo, 0)
            actual = diff + target
            
            z_row.append(diff)
            # Get actual counts for this demographic in this entity
            entity_data = df[df['EntityDesc'] == entity]
            demo_count = entity_data[demo].sum() if demo in entity_data.columns else 0
            total_people = entity_data['TOTAL'].sum()
            
            hover_row.append(
                f"<b>Module:</b> {entity}<br>"
                f"<b>Demographic:</b> {demo}<br>"
                f"<b>People Count:</b> {demo_count:,.0f}<br>"
                f"<b>Total People:</b> {total_people:,.0f}<br>"
                f"<b>Actual %:</b> {actual:.1f}%<br>"
                f"<b>Target %:</b> {target:.1f}%<br>"
                f"<b>Gap:</b> {diff:+.1f}%"
            )
        
        z_data.append(z_row)
        hover_text.append(hover_row)
    
    # Create heatmap with improved labeling
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=demographics,
        y=entities,
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_text,
        colorscale=[
            [0, '#d62728'],      # Red for under-representation
            [0.5, '#ffffff'],    # White for on-target
            [1, '#2ca02c']       # Green for over-representation
        ],
        zmid=0,  # Center the colorscale at 0
        colorbar=dict(
            title=dict(
                text="Difference from Target (%)",
                side="right"
            ),
            tickmode="linear",
            tick0=-20,
            dtick=10,
            ticksuffix="%"
        ),
        showscale=True,
        # Add text annotations for values
        text=[[f"{val:+.1f}%" for val in row] for row in z_data],
        texttemplate="%{text}",
        textfont={"size": 9, "color": "black"}
    ))
    
    # Update layout with better formatting
    fig.update_layout(
        title=dict(
            text="Demographic Representation Heat Map<br><sub style='font-size:12px;'>Green: Over Target | White: On Target | Red: Under Target</sub>",
            x=0.5,
            font=dict(size=16)
        ),
        xaxis=dict(
            title=dict(text="Demographic Categories", font=dict(size=14)),
            tickfont=dict(size=10),
            side="bottom"
        ),
        yaxis=dict(
            title=dict(text="Educational Modules", font=dict(size=14)),
            tickfont=dict(size=10),
            autorange="reversed"  # Show first module at top
        ),
        height=max(500, len(entities) * 35),  # More space for readability
        margin=dict(l=150, r=100, t=100, b=100),  # More margin for labels
        font=dict(size=11)
    )
    
    # Improve x-axis labels
    fig.update_xaxes(
        tickangle=45,
        tickmode='array',
        tickvals=list(range(len(demographics))),
        ticktext=[f"{demo}<br>({targets.get(demo, 0):.1f}% target)" for demo in demographics]
    )
    
    # Improve y-axis labels - truncate long names
    truncated_entities = [entity[:40] + "..." if len(entity) > 40 else entity for entity in entities]
    fig.update_yaxes(
        tickmode='array',
        tickvals=list(range(len(entities))),
        ticktext=truncated_entities
    )
    
    return fig

def create_module_summary_chart(module_totals_df: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing module totals
    
    Args:
        module_totals_df: DataFrame with module totals
        
    Returns:
        Plotly figure object
    """
    if module_totals_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No module data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Limit to top 20 modules for better visualization
    top_modules = module_totals_df.head(20).copy()
    
    # Create combined label for better identification
    top_modules['Display_Label'] = top_modules['EntityDesc'].str[:30] + "... (" + top_modules['Grade'] + ")"
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=top_modules['Total People'],
            y=top_modules['Display_Label'],
            orientation='h',
            text=top_modules['Total People'],
            textposition='auto',
            hovertemplate=(
                "<b>%{y}</b><br>" +
                "Total People: %{x}<br>" +
                "<extra></extra>"
            ),
            marker=dict(
                color=top_modules['Total People'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title="Total People")
            )
        )
    ])
    
    # Update layout
    fig.update_layout(
        title=f"Top {len(top_modules)} Modules by Total People",
        xaxis_title="Total People",
        yaxis_title="Modules",
        height=max(400, len(top_modules) * 25),
        showlegend=False,
        yaxis=dict(autorange="reversed"),  # Show highest values at top
        margin=dict(l=200)  # More space for labels
    )
    
    return fig

def create_demographic_distribution_chart(df: pd.DataFrame, demographic_cols: List[str]) -> go.Figure:
    """
    Create a pie chart showing overall demographic distribution
    
    Args:
        df: Input DataFrame
        demographic_cols: List of demographic column names
        
    Returns:
        Plotly figure object
    """
    if df.empty or not demographic_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No demographic data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate totals for each demographic
    demo_totals = {}
    for col in demographic_cols:
        if col in df.columns:
            total = df[col].sum()
            if total > 0:  # Only include demographics with data
                demo_totals[col] = total
    
    if not demo_totals:
        fig = go.Figure()
        fig.add_annotation(
            text="No demographic data with values > 0",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Create pie chart
    labels = list(demo_totals.keys())
    values = list(demo_totals.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
        textinfo='label+percent'
    )])
    
    fig.update_layout(
        title="Overall Demographic Distribution",
        showlegend=True,
        height=500
    )
    
    return fig

def create_grade_comparison_chart(df: pd.DataFrame, demographic_cols: List[str]) -> go.Figure:
    """
    Create a grouped bar chart comparing demographics across grades
    
    Args:
        df: Input DataFrame
        demographic_cols: List of demographic column names
        
    Returns:
        Plotly figure object
    """
    if df.empty or not demographic_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for grade comparison",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Group by grade and sum demographics
    grade_demo_data = []
    
    for grade in df['Grade'].unique():
        grade_data = df[df['Grade'] == grade]
        total_people = grade_data['TOTAL'].sum()
        
        if total_people == 0:
            continue
        
        row = {'Grade': grade}
        for demo_col in demographic_cols:
            if demo_col in grade_data.columns:
                demo_count = grade_data[demo_col].sum()
                percentage = (demo_count / total_people) * 100
                row[demo_col] = percentage
            else:
                row[demo_col] = 0
        
        grade_demo_data.append(row)
    
    if not grade_demo_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid grade data for comparison",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Convert to DataFrame
    grade_df = pd.DataFrame(grade_demo_data)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    grades = grade_df['Grade'].tolist()
    
    for demo_col in demographic_cols:
        if demo_col in grade_df.columns:
            fig.add_trace(go.Bar(
                name=demo_col,
                x=grades,
                y=grade_df[demo_col],
                hovertemplate=f"<b>{demo_col}</b><br>Grade: %{{x}}<br>Percentage: %{{y:.1f}}%<extra></extra>"
            ))
    
    fig.update_layout(
        title="Demographic Distribution by Grade Level",
        xaxis_title="Grade",
        yaxis_title="Percentage (%)",
        barmode='group',
        height=500,
        showlegend=True
    )
    
    return fig

def create_trend_line_chart(trend_df: pd.DataFrame, demographic_cols: List[str]) -> go.Figure:
    """
    Create a line chart showing demographic trends across modules
    
    Args:
        trend_df: DataFrame with trend data
        demographic_cols: List of demographic column names
        
    Returns:
        Plotly figure object
    """
    if trend_df.empty or not demographic_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No trend data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    fig = go.Figure()
    colors = px.colors.qualitative.Set1[:len(demographic_cols)]
    
    # Sort by grade for better trend visualization
    trend_df_sorted = trend_df.sort_values(['Grade', 'EntityDesc'])
    
    # Create x-axis labels (Grade - Module)
    x_labels = [f"Grade {row['Grade']}" for _, row in trend_df_sorted.iterrows()]
    
    for i, demo_col in enumerate(demographic_cols):
        percentage_col = f'{demo_col}_Percentage'
        if percentage_col in trend_df_sorted.columns:
            fig.add_trace(go.Scatter(
                x=list(range(len(trend_df_sorted))),
                y=trend_df_sorted[percentage_col],
                mode='lines+markers',
                name=demo_col,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8),
                hovertemplate=f'<b>{demo_col}</b><br>' +
                            'Module: %{customdata}<br>' +
                            'Percentage: %{y:.1f}%<extra></extra>',
                customdata=trend_df_sorted['EntityDesc']
            ))
    
    fig.update_layout(
        title="Demographic Trends Across Modules",
        xaxis_title="Modules (by Grade)",
        yaxis_title="Percentage (%)",
        template='plotly_white',
        height=500,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(trend_df_sorted))),
            ticktext=x_labels,
            tickangle=45
        )
    )
    
    return fig

def create_diversity_radar_chart(diversity_metrics: Dict[str, float]) -> go.Figure:
    """
    Create a radar chart showing diversity metrics
    
    Args:
        diversity_metrics: Dictionary with diversity metrics
        
    Returns:
        Plotly figure object
    """
    if not diversity_metrics:
        fig = go.Figure()
        fig.add_annotation(
            text="No diversity metrics available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Normalize metrics to 0-1 scale for radar chart
    metrics_names = []
    metrics_values = []
    
    for metric, value in diversity_metrics.items():
        # Clean up metric names for display
        display_name = metric.replace('_', ' ').title()
        metrics_names.append(display_name)
        
        # Normalize values (most diversity metrics are already 0-1)
        if 'diversity_index' in metric:
            normalized_value = value  # Already 0-1
        elif 'balance' in metric:
            normalized_value = value  # Already 0-1
        else:
            normalized_value = min(value, 1.0)  # Cap at 1.0
        
        metrics_values.append(normalized_value)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=metrics_values,
        theta=metrics_names,
        fill='toself',
        fillcolor='rgba(31, 119, 180, 0.3)',
        line=dict(color='rgb(31, 119, 180)', width=3),
        marker=dict(size=8),
        name='Diversity Metrics'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickmode='linear',
                tick0=0,
                dtick=0.2
            )
        ),
        title="Diversity and Equity Metrics",
        template='plotly_white',
        height=500
    )
    
    return fig

def create_comparative_analysis_chart(comparisons: Dict[str, pd.DataFrame], 
                                    demographic_cols: List[str], 
                                    analysis_type: str = 'grade') -> go.Figure:
    """
    Create comparative analysis charts for different groupings
    
    Args:
        comparisons: Dictionary with comparison DataFrames
        demographic_cols: List of demographic column names
        analysis_type: Type of analysis ('grade' or 'component')
        
    Returns:
        Plotly figure object
    """
    key = f'{analysis_type}_summary'
    if key not in comparisons or comparisons[key].empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No {analysis_type} comparison data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    df = comparisons[key]
    group_col = 'Grade' if analysis_type == 'grade' else 'Component'
    
    fig = go.Figure()
    colors = px.colors.qualitative.Pastel[:len(demographic_cols)]
    
    for i, demo_col in enumerate(demographic_cols):
        percentage_col = f'{demo_col}_Percentage'
        if percentage_col in df.columns:
            fig.add_trace(go.Bar(
                name=demo_col,
                x=df[group_col],
                y=df[percentage_col],
                marker_color=colors[i % len(colors)],
                text=df[percentage_col].round(1),
                textposition='auto',
                hovertemplate=f'<b>{demo_col}</b><br>' +
                            f'{group_col}: %{{x}}<br>' +
                            'Percentage: %{y:.1f}%<br>' +
                            'Count: %{customdata}<extra></extra>',
                customdata=df[f'{demo_col}_Count'] if f'{demo_col}_Count' in df.columns else [0] * len(df)
            ))
    
    fig.update_layout(
        title=f"Demographic Comparison by {group_col}",
        xaxis_title=group_col,
        yaxis_title="Percentage (%)",
        barmode='group',
        template='plotly_white',
        height=500
    )
    
    return fig
