import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple, Any
import streamlit as st

class AdvancedDemographicAnalytics:
    """Advanced analytics for demographic data"""
    
    def __init__(self, df: pd.DataFrame, demographic_cols: List[str]):
        self.df = df
        self.demographic_cols = demographic_cols
    
    def calculate_diversity_index(self, entity_data: pd.Series) -> Dict[str, float]:
        """Calculate Shannon and Simpson diversity indices"""
        total = entity_data.sum()
        if total == 0:
            return {'shannon': 0, 'simpson': 0}
        
        proportions = entity_data / total
        proportions = proportions[proportions > 0]  # Remove zeros
        
        # Shannon diversity index
        shannon = -np.sum(proportions * np.log(proportions))
        
        # Simpson diversity index
        simpson = 1 - np.sum(proportions ** 2)
        
        return {'shannon': shannon, 'simpson': simpson}
    
    def detect_representation_gaps(self, targets: Dict[str, float]) -> pd.DataFrame:
        """Detect modules with significant representation gaps"""
        gap_analysis = []
        
        for entity in self.df['EntityDesc'].unique():
            entity_data = self.df[self.df['EntityDesc'] == entity]
            total_people = entity_data['TOTAL'].sum()
            
            if total_people == 0:
                continue
            
            gaps = {}
            for demo_col in self.demographic_cols:
                if demo_col in entity_data.columns:
                    actual_count = entity_data[demo_col].sum()
                    actual_pct = (actual_count / total_people) * 100
                    target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10))
                    gap = actual_pct - target_pct
                    gaps[demo_col] = gap
            
            # Find the largest positive and negative gaps
            if gaps:
                largest_gap = max(gaps.values())
                smallest_gap = min(gaps.values())
                largest_gap_demo = max(gaps, key=gaps.get)
                smallest_gap_demo = min(gaps, key=gaps.get)
                
                gap_analysis.append({
                    'Module': entity,
                    'Total_People': int(total_people),
                    'Largest_Overrep': f"{largest_gap_demo}: +{largest_gap:.1f}%",
                    'Largest_Underrep': f"{smallest_gap_demo}: {smallest_gap:.1f}%",
                    'Gap_Range': largest_gap - smallest_gap
                })
        
        return pd.DataFrame(gap_analysis).sort_values('Gap_Range', ascending=False)
    
    def generate_equity_scorecard(self, targets: Dict[str, float]) -> Dict[str, Any]:
        """Generate an equity scorecard for the dataset"""
        total_people = self.df['TOTAL'].sum()
        scorecard = {
            'overall_score': 0,
            'demographic_scores': {},
            'recommendations': []
        }
        
        for demo_col in self.demographic_cols:
            if demo_col in self.df.columns:
                actual_count = self.df[demo_col].sum()
                actual_pct = (actual_count / total_people) * 100
                target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10))
                
                # Calculate equity score (0-100, where 100 is perfect match)
                gap = abs(actual_pct - target_pct)
                score = max(0, 100 - (gap * 5))  # Penalize 5 points per percentage point gap
                
                scorecard['demographic_scores'][demo_col] = {
                    'score': score,
                    'actual': actual_pct,
                    'target': target_pct,
                    'gap': actual_pct - target_pct
                }
                
                # Generate recommendations
                if gap > 10:
                    if actual_pct < target_pct:
                        scorecard['recommendations'].append(
                            f"Increase {demo_col} representation by {target_pct - actual_pct:.1f} percentage points"
                        )
                    else:
                        scorecard['recommendations'].append(
                            f"Consider balancing {demo_col} representation (currently {actual_pct - target_pct:.1f}% above target)"
                        )
        
        # Calculate overall score
        if scorecard['demographic_scores']:
            scorecard['overall_score'] = np.mean([d['score'] for d in scorecard['demographic_scores'].values()])
        
        return scorecard
    
    def create_trend_analysis_chart(self) -> go.Figure:
        """Create a trend analysis chart across grades"""
        if 'Grade' not in self.df.columns:
            return go.Figure().add_annotation(
                text="Grade column not available for trend analysis",
                xref="paper", yref="paper", x=0.5, y=0.5
            )
        
        grade_analysis = []
        for grade in sorted(self.df['Grade'].unique()):
            grade_data = self.df[self.df['Grade'] == grade]
            total_people = grade_data['TOTAL'].sum()
            
            if total_people > 0:
                row = {'Grade': grade, 'Total_People': total_people}
                for demo_col in self.demographic_cols[:6]:  # Limit to first 6 for readability
                    if demo_col in grade_data.columns:
                        demo_count = grade_data[demo_col].sum()
                        percentage = (demo_count / total_people) * 100
                        row[demo_col] = percentage
                grade_analysis.append(row)
        
        if not grade_analysis:
            return go.Figure().add_annotation(
                text="No grade data available for trend analysis",
                xref="paper", yref="paper", x=0.5, y=0.5
            )
        
        df_trends = pd.DataFrame(grade_analysis)
        
        fig = go.Figure()
        colors = px.colors.qualitative.Set3
        
        for i, demo_col in enumerate(self.demographic_cols[:6]):
            if demo_col in df_trends.columns:
                fig.add_trace(go.Scatter(
                    x=df_trends['Grade'],
                    y=df_trends[demo_col],
                    mode='lines+markers',
                    name=demo_col,
                    line=dict(color=colors[i % len(colors)], width=3),
                    marker=dict(size=8)
                ))
        
        fig.update_layout(
            title="Demographic Representation Trends Across Grades",
            xaxis_title="Grade Level",
            yaxis_title="Representation Percentage (%)",
            template='plotly_white',
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        return fig
    
    def create_correlation_heatmap(self) -> go.Figure:
        """Create correlation heatmap between demographics"""
        if len(self.demographic_cols) < 2:
            return go.Figure().add_annotation(
                text="Need at least 2 demographic columns for correlation analysis",
                xref="paper", yref="paper", x=0.5, y=0.5
            )
        
        # Calculate correlation matrix
        demo_data = self.df[self.demographic_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=demo_data.values,
            x=demo_data.columns,
            y=demo_data.columns,
            colorscale='RdBu_r',
            zmid=0,
            text=np.round(demo_data.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Demographic Correlation Matrix",
            template='plotly_white',
            height=500,
            width=600
        )
        
        return fig

def create_benchmark_comparison_chart(df: pd.DataFrame, demographic_cols: List[str], 
                                    targets: Dict[str, float]) -> go.Figure:
    """Create a benchmark comparison chart"""
    total_people = df['TOTAL'].sum()
    
    comparison_data = []
    for demo_col in demographic_cols:
        if demo_col in df.columns:
            actual_count = df[demo_col].sum()
            actual_pct = (actual_count / total_people) * 100
            target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10))
            
            comparison_data.append({
                'Demographic': demo_col,
                'Actual': actual_pct,
                'Target': target_pct,
                'Gap': actual_pct - target_pct
            })
    
    df_comp = pd.DataFrame(comparison_data)
    
    fig = go.Figure()
    
    # Add actual values
    fig.add_trace(go.Bar(
        name='Actual',
        x=df_comp['Demographic'],
        y=df_comp['Actual'],
        marker_color='lightblue',
        text=df_comp['Actual'].round(1),
        textposition='outside'
    ))
    
    # Add target values
    fig.add_trace(go.Bar(
        name='Target',
        x=df_comp['Demographic'],
        y=df_comp['Target'],
        marker_color='orange',
        text=df_comp['Target'].round(1),
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Actual vs Target Demographic Representation",
        xaxis_title="Demographics",
        yaxis_title="Percentage (%)",
        barmode='group',
        template='plotly_white',
        height=500,
        xaxis_tickangle=-45
    )
    
    return fig