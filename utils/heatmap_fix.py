import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List

def create_aligned_heatmap(df: pd.DataFrame, demographic_cols: List[str], targets: Dict[str, float]) -> go.Figure:
    """
    Create heatmap with guaranteed tooltip alignment
    """
    if df.empty or not demographic_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Step 1: Filter to only columns that exist in the dataframe
    valid_cols = [col for col in demographic_cols if col in df.columns]
    
    if not valid_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid demographic columns found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Step 2: Process data by entity
    z_matrix = []
    hover_matrix = []
    y_labels = []
    
    entity_groups = df.groupby('EntityDesc')
    
    for entity_name, entity_data in entity_groups:
        total_people = entity_data['TOTAL'].sum()
        
        if total_people == 0:
            continue
            
        # Truncate long names
        y_label = entity_name[:40] + "..." if len(entity_name) > 40 else entity_name
        y_labels.append(y_label)
        
        # Process each demographic column in order
        z_row = []
        hover_row = []
        
        for demo_col in valid_cols:
            # Calculate values for this specific cell
            demo_count = entity_data[demo_col].sum() if demo_col in entity_data.columns else 0
            actual_pct = (demo_count / total_people) * 100 if total_people > 0 else 0
            target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10.0))
            gap = actual_pct - target_pct
            
            # Add to matrices
            z_row.append(gap)
            
            hover_text = (
                f"<b>{entity_name}</b><br>"
                f"<b>Demographic:</b> {demo_col}<br>"
                f"<b>Actual:</b> {actual_pct:.1f}% ({int(demo_count)} people)<br>"
                f"<b>Target:</b> {target_pct:.1f}%<br>"
                f"<b>Gap:</b> {gap:+.1f}%<br>"
                f"<b>Total People:</b> {int(total_people)}"
            )
            hover_row.append(hover_text)
        
        z_matrix.append(z_row)
        hover_matrix.append(hover_row)
    
    if not z_matrix:
        fig = go.Figure()
        fig.add_annotation(
            text="No data to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Step 3: Create abbreviations for x-axis
    x_labels = []
    for i, demo_col in enumerate(valid_cols):
        demo_lower = demo_col.lower()
        if 'african american' in demo_lower:
            abbrev = 'AA'
        elif 'caucasian' in demo_lower or 'white' in demo_lower:
            abbrev = 'C'
        elif 'asian' in demo_lower:
            abbrev = 'AS'
        elif 'hispanic' in demo_lower:
            abbrev = 'H'
        elif 'native american' in demo_lower:
            abbrev = 'NA'
        elif 'pacific islander' in demo_lower:
            abbrev = 'PI'
        elif 'lgbt' in demo_lower:
            abbrev = 'LGBT'
        elif 'legacy' in demo_lower:
            abbrev = 'LEG'
        elif 'physically challenged' in demo_lower:
            abbrev = 'PC'
        elif demo_lower == 'male':
            abbrev = 'M'
        elif demo_lower == 'female':
            abbrev = 'F'
        elif demo_lower == 'other':
            abbrev = 'OTHER'
        else:
            abbrev = demo_col[:4].upper()
        
        x_labels.append(abbrev)
    
    # Step 4: Create heatmap with exact alignment
    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=x_labels,
        y=y_labels,
        customdata=hover_matrix,
        hovertemplate='%{customdata}<extra></extra>',
        colorscale=[
            [0, '#d32f2f'],      # Dark red for significantly under target
            [0.3, '#ff5722'],    # Red for under target
            [0.45, '#ff9800'],   # Orange for slightly under
            [0.48, '#ffc107'],   # Yellow for near target
            [0.5, '#ffffff'],    # White for on target
            [0.52, '#8bc34a'],   # Light green for slightly over
            [0.7, '#4caf50'],    # Green for over target
            [1, '#2e7d32']       # Dark green for significantly over target
        ],
        zmid=0,
        zmin=-50,
        zmax=50,
        colorbar=dict(
            title="Gap from Target (%)",
            tickmode="array",
            tickvals=[-40, -20, 0, 20, 40],
            ticktext=["-40%", "-20%", "On Target", "+20%", "+40%"],
            x=1.01,
            len=0.8,
            thickness=20
        )
    ))
    
    fig.update_layout(
        title=dict(
            text="Demographic Representation Heat Map - Gap Analysis vs Targets",
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title="Demographics (Hover for full names)",
            tickangle=45,
            side='bottom',
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title="Modules/Lessons",
            autorange='reversed',
            tickfont=dict(size=9)
        ),
        template='plotly_white',
        height=max(400, len(y_labels) * 25 + 150),
        margin=dict(l=50, r=120, t=80, b=100),
        font=dict(size=10)
    )
    
    return fig