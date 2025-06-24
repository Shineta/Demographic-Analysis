import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def create_module_population_bar_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a horizontal bar chart showing total people per module
    
    Args:
        df: Input DataFrame with EntityDesc and TOTAL columns
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'EntityDesc' not in df.columns or 'TOTAL' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for module population chart",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate total people per module
    module_totals = df.groupby('EntityDesc')['TOTAL'].sum().reset_index()
    module_totals = module_totals.sort_values('TOTAL', ascending=True)  # Sort for better visualization
    
    # Truncate long module names for better display
    module_totals['EntityDesc_Display'] = module_totals['EntityDesc'].apply(
        lambda x: x[:40] + "..." if len(x) > 40 else x
    )
    
    # Create color scale based on population size
    max_total = module_totals['TOTAL'].max()
    colors = []
    for total in module_totals['TOTAL']:
        if total > max_total * 0.7:
            colors.append('#22c55e')  # Green for high population
        elif total > max_total * 0.3:
            colors.append('#f59e0b')  # Orange for medium population
        else:
            colors.append('#ef4444')  # Red for low population
    
    fig = go.Figure(data=go.Bar(
        y=module_totals['EntityDesc_Display'],
        x=module_totals['TOTAL'],
        orientation='h',
        marker=dict(color=colors),
        text=module_totals['TOTAL'],
        textposition='outside',
        texttemplate='%{text:,}',
        hovertemplate="<b>%{customdata}</b><br>" +
                     "Total People: %{x:,}<br>" +
                     "<extra></extra>",
        customdata=module_totals['EntityDesc']
    ))
    
    fig.update_layout(
        title=dict(
            text="Module Population Chart - Total People per Module",
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title="Total People",
            tickformat=',',
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="Modules",
            tickfont=dict(size=10)
        ),
        template='plotly_white',
        height=max(400, len(module_totals) * 30 + 100),
        margin=dict(l=200, r=100, t=80, b=60),
        showlegend=False
    )
    
    return fig

def create_module_population_heatmap_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a DataFrame formatted as a heat map table for module populations
    
    Args:
        df: Input DataFrame with EntityDesc and TOTAL columns
        
    Returns:
        Formatted DataFrame for display
    """
    if df.empty or 'EntityDesc' not in df.columns or 'TOTAL' not in df.columns:
        return pd.DataFrame({"Message": ["No data available"]})
    
    # Calculate total people per module
    module_totals = df.groupby('EntityDesc')['TOTAL'].sum().reset_index()
    module_totals = module_totals.sort_values('TOTAL', ascending=False)
    
    # Add heat map categories
    max_total = module_totals['TOTAL'].max()
    categories = []
    heat_scores = []
    
    for total in module_totals['TOTAL']:
        if total > max_total * 0.7:
            categories.append("🔥 High Population")
            heat_scores.append(3)
        elif total > max_total * 0.3:
            categories.append("🟡 Medium Population")
            heat_scores.append(2)
        else:
            categories.append("🔵 Low Population")
            heat_scores.append(1)
    
    module_totals['Population Category'] = categories
    module_totals['Heat Score'] = heat_scores
    module_totals['Total People'] = module_totals['TOTAL'].apply(lambda x: f"{x:,}")
    
    # Calculate percentages
    total_all = module_totals['TOTAL'].sum()
    module_totals['Percentage'] = module_totals['TOTAL'].apply(
        lambda x: f"{(x/total_all)*100:.1f}%"
    )
    
    # Return formatted table
    return module_totals[['EntityDesc', 'Total People', 'Percentage', 'Population Category']].rename(
        columns={'EntityDesc': 'Module Name'}
    )

def create_population_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a pie chart showing distribution of people across modules
    
    Args:
        df: Input DataFrame
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'EntityDesc' not in df.columns or 'TOTAL' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for population distribution",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate module totals
    module_totals = df.groupby('EntityDesc')['TOTAL'].sum().reset_index()
    
    # Keep only top 10 modules for readability, group others as "Others"
    if len(module_totals) > 10:
        top_modules = module_totals.nlargest(9, 'TOTAL')
        others_total = module_totals.nsmallest(len(module_totals) - 9, 'TOTAL')['TOTAL'].sum()
        
        if others_total > 0:
            others_row = pd.DataFrame({
                'EntityDesc': [f'Others ({len(module_totals) - 9} modules)'],
                'TOTAL': [others_total]
            })
            module_totals = pd.concat([top_modules, others_row], ignore_index=True)
        else:
            module_totals = top_modules
    
    # Truncate long names
    module_totals['EntityDesc_Display'] = module_totals['EntityDesc'].apply(
        lambda x: x[:25] + "..." if len(x) > 25 else x
    )
    
    fig = go.Figure(data=go.Pie(
        labels=module_totals['EntityDesc_Display'],
        values=module_totals['TOTAL'],
        hole=0.3,
        textinfo='label+percent',
        textposition='auto',
        hovertemplate="<b>%{customdata}</b><br>" +
                     "People: %{value:,}<br>" +
                     "Percentage: %{percent}<br>" +
                     "<extra></extra>",
        customdata=module_totals['EntityDesc']
    ))
    
    fig.update_layout(
        title=dict(
            text="Population Distribution Across Modules",
            font=dict(size=16),
            x=0.5
        ),
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.05
        )
    )
    
    return fig

def create_module_population_heatmap_plotly(df: pd.DataFrame) -> go.Figure:
    """
    Create a vertical module population heatmap using Plotly
    
    Args:
        df: Input DataFrame with EntityDesc and TOTAL columns
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'EntityDesc' not in df.columns or 'TOTAL' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for module population heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate total people per module
    module_totals = df.groupby('EntityDesc')['TOTAL'].sum().reset_index()
    module_totals = module_totals.sort_values('TOTAL', ascending=True)  # Ascending for better visual flow
    
    # Truncate long module names for better display
    module_totals['EntityDesc_Display'] = module_totals['EntityDesc'].apply(
        lambda x: x[:40] + "..." if len(x) > 40 else x
    )
    
    # Create vertical heatmap data - each module is a row
    z_data = module_totals['TOTAL'].values.reshape(-1, 1)  # Convert to column vector
    
    # Create hover text
    hover_text = []
    for _, row in module_totals.iterrows():
        hover_text.append([f"<b>{row['EntityDesc']}</b><br>Population: {row['TOTAL']:,}"])
    
    # Create the vertical heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        y=module_totals['EntityDesc_Display'],  # Module names on y-axis
        x=['Population Count'],  # Single column
        colorscale='YlOrRd',  # Yellow to Red color scale
        showscale=True,
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_text,
        colorbar=dict(
            title="Population Count",
            thickness=15,
            len=0.8
        )
    ))
    
    fig.update_layout(
        title=dict(
            text="Module Population Heatmap - Vertical Layout",
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title="",
            showticklabels=True,
            tickangle=0
        ),
        yaxis=dict(
            title="",
            showticklabels=True,
            tickfont=dict(size=10)
        ),
        template='plotly_white',
        height=max(500, len(module_totals) * 25),  # Dynamic height based on number of modules
        margin=dict(l=200, r=100, t=80, b=50)  # More left margin for module names
    )
    
    return fig

def create_module_population_treemap(df: pd.DataFrame) -> go.Figure:
    """
    Create a treemap visualization of module populations
    
    Args:
        df: Input DataFrame with EntityDesc and TOTAL columns
        
    Returns:
        Plotly figure object
    """
    if df.empty or 'EntityDesc' not in df.columns or 'TOTAL' not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for treemap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Calculate module totals
    module_totals = df.groupby('EntityDesc')['TOTAL'].sum().reset_index()
    
    # Truncate long names for better display
    module_totals['EntityDesc_Display'] = module_totals['EntityDesc'].apply(
        lambda x: x[:30] + "..." if len(x) > 30 else x
    )
    
    # Create color scale based on population size
    max_total = module_totals['TOTAL'].max()
    colors = []
    for total in module_totals['TOTAL']:
        if total > max_total * 0.7:
            colors.append('#d32f2f')  # Dark red for high population
        elif total > max_total * 0.4:
            colors.append('#ff9800')  # Orange for medium population  
        elif total > max_total * 0.2:
            colors.append('#ffc107')  # Yellow for low-medium population
        else:
            colors.append('#4caf50')  # Green for low population
    
    fig = go.Figure(go.Treemap(
        labels=module_totals['EntityDesc_Display'],
        values=module_totals['TOTAL'],
        parents=[""] * len(module_totals),
        textinfo="label+value",
        textfont={"size": 12},
        marker=dict(
            colors=module_totals['TOTAL'],
            colorscale='YlOrRd',
            showscale=True,
            colorbar=dict(title="Population Count")
        ),
        hovertemplate="<b>%{customdata}</b><br>" +
                     "Population: %{value:,}<br>" +
                     "Percentage: %{percentParent}<br>" +
                     "<extra></extra>",
        customdata=module_totals['EntityDesc']
    ))
    
    fig.update_layout(
        title=dict(
            text="Module Population Treemap - Proportional View",
            font=dict(size=16),
            x=0.5
        ),
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def get_population_statistics(df: pd.DataFrame) -> Dict[str, any]:
    """
    Calculate population statistics for modules
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with statistics
    """
    if df.empty or 'EntityDesc' not in df.columns or 'TOTAL' not in df.columns:
        return {"error": "No data available"}
    
    module_totals = df.groupby('EntityDesc')['TOTAL'].sum()
    
    stats = {
        'total_modules': len(module_totals),
        'total_people': int(module_totals.sum()),
        'avg_people_per_module': round(module_totals.mean(), 1),
        'largest_module': {
            'name': module_totals.idxmax(),
            'count': int(module_totals.max())
        },
        'smallest_module': {
            'name': module_totals.idxmin(),
            'count': int(module_totals.min())
        },
        'median_population': round(module_totals.median(), 1)
    }
    
    return stats