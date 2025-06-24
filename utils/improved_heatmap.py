import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List

def create_improved_heatmap(df: pd.DataFrame, demographic_cols: List[str], targets: Dict[str, float]) -> go.Figure:
    """
    Create an improved interactive heatmap with rich tooltips and better styling
    
    Args:
        df: Input DataFrame (should already be filtered by module selection)
        demographic_cols: List of demographic column names
        targets: Dictionary of target percentages for each demographic
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available - try selecting different modules or check your filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="red")
        )
        return fig
    
    if not demographic_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No demographic columns found in the data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="orange")
        )
        return fig
    
    # Verify we have the required columns
    required_cols = ['EntityDesc', 'TOTAL'] + demographic_cols
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Missing required columns: {', '.join(missing_cols)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=14, color="red")
        )
        return fig
    
    # Filter to only valid demographic columns from the start
    valid_demographic_cols = [col for col in demographic_cols if col in df.columns]
    
    if not valid_demographic_cols:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid demographic columns found in the data",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="orange")
        )
        return fig
    
    # Calculate detailed data for each module and demographic
    heatmap_data = []
    
    # Group by EntityDesc and aggregate the data properly
    entity_groups = df.groupby('EntityDesc')
    
    for entity_name, entity_data in entity_groups:
        # Calculate total people for this entity/module
        total_people = entity_data['TOTAL'].sum()
        
        if total_people == 0:
            # Skip modules with no people
            continue
        
        row_data = {'EntityDesc': entity_name, 'Total_People': total_people}
        
        # Only process valid demographic columns
        for demo_col in valid_demographic_cols:
            # Check if demographic column exists and has data
            if demo_col in entity_data.columns and not entity_data[demo_col].isna().all():
                demo_count = entity_data[demo_col].sum()
                actual_percentage = (demo_count / total_people) * 100 if total_people > 0 else 0
                target_percentage = targets.get(demo_col.lower(), targets.get(demo_col, 10.0))
                
                # Calculate gap from target
                gap = actual_percentage - target_percentage
                row_data[demo_col] = gap
            else:
                # Missing or zero demographic data
                target_percentage = targets.get(demo_col.lower(), targets.get(demo_col, 10.0))
                gap = -target_percentage  # All gap since actual is 0
                row_data[demo_col] = gap
        
        heatmap_data.append(row_data)
    
    if not heatmap_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Prepare data for plotly heatmap with proper alignment
    z_data = []
    y_labels = []
    custom_data = []
    
    for i, (_, row) in enumerate(heatmap_df.iterrows()):
        entity_name = row['EntityDesc']
        total_people = row['Total_People']
        
        # Truncate long module names for y-axis
        y_label = entity_name[:40] + "..." if len(entity_name) > 40 else entity_name
        y_labels.append(y_label)
        
        row_values = []
        row_hover_data = []
        
        # Use the pre-filtered valid demographic columns
        for demo_col in valid_demographic_cols:
            if demo_col in row:
                gap_value = row[demo_col]
                row_values.append(gap_value)
                
                # Calculate the actual data for this specific cell
                entity_data = df[df['EntityDesc'] == entity_name]
                if demo_col in entity_data.columns and not entity_data[demo_col].isna().all():
                    demo_count = entity_data[demo_col].sum()
                    actual_percentage = (demo_count / total_people) * 100 if total_people > 0 else 0
                else:
                    demo_count = 0
                    actual_percentage = 0.0
                
                target_percentage = targets.get(demo_col.lower(), targets.get(demo_col, 10.0))
                
                # Create hover text for this specific cell
                hover_text = (
                    f"<b>{entity_name[:60]}{'...' if len(entity_name) > 60 else ''}</b><br>"
                    f"<b>Demographic:</b> {demo_col}<br>"
                    f"<b>Actual:</b> {actual_percentage:.1f}% ({int(demo_count)} people)<br>"
                    f"<b>Target:</b> {target_percentage:.1f}%<br>"
                    f"<b>Gap:</b> {gap_value:+.1f}%<br>"
                    f"<b>Total People:</b> {int(total_people)}"
                )
                row_hover_data.append(hover_text)
            else:
                row_values.append(0)
                target_percentage = targets.get(demo_col.lower(), targets.get(demo_col, 10.0))
                hover_text = (
                    f"<b>{entity_name[:60]}{'...' if len(entity_name) > 60 else ''}</b><br>"
                    f"<b>Demographic:</b> {demo_col}<br>"
                    f"<b>Actual:</b> 0.0% (0 people)<br>"
                    f"<b>Target:</b> {target_percentage:.1f}%<br>"
                    f"<b>Gap:</b> {-target_percentage:+.1f}%<br>"
                    f"<b>Total People:</b> {int(total_people)}<br>"
                    f"<i>No data available</i>"
                )
                row_hover_data.append(hover_text)
        
        z_data.append(row_values)
        custom_data.append(row_hover_data)
    
    # Create x-axis labels using the same valid demographic columns
    x_labels = []
    for demo_col in valid_demographic_cols:
        demo_lower = demo_col.lower()
        if demo_lower in ['aam', 'aaf', 'pcm', 'pcf', 'lgbtf', 'other_m', 'other_f']:
            abbrev = demo_col.upper()
        elif 'african american' in demo_lower:
            abbrev = 'AA'
        elif 'hispanic' in demo_lower:
            abbrev = 'H'
        elif 'asian' in demo_lower:
            abbrev = 'AS'
        elif 'caucasian' in demo_lower or 'white' in demo_lower:
            abbrev = 'C'
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
            # Fallback abbreviation - use first 4 characters
            abbrev = demo_col[:4].upper()
        
        x_labels.append(abbrev)
    
    # Create heatmap with improved styling and proper hover alignment
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        customdata=custom_data,
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
        zmid=0,  # Center the colorscale at 0 (on target)
        zmin=-50,  # Set reasonable range
        zmax=50,
        colorbar=dict(
            title="Gap from Target (%)",
            tickmode="array",
            tickvals=[-40, -20, 0, 20, 40],
            ticktext=["-40%", "-20%", "On Target", "+20%", "+40%"],
            x=1.01,
            len=0.8,
            thickness=20,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
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
            autorange='reversed',  # Show first module at top
            tickfont=dict(size=9)
        ),
        template='plotly_white',
        height=max(400, len(y_labels) * 25 + 150),  # Dynamic height based on modules
        margin=dict(l=50, r=120, t=80, b=100),
        font=dict(size=10)
    )
    
    return fig