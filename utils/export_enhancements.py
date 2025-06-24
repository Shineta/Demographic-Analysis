import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import base64
from typing import Dict, List, Any
import streamlit as st
from datetime import datetime
import numpy as np

def create_executive_summary_report(df: pd.DataFrame, demographic_cols: List[str], 
                                  targets: Dict[str, float], analysis_results: Dict[str, Any]) -> pd.DataFrame:
    """Create an executive summary report"""
    
    # Basic statistics
    total_people = df['TOTAL'].sum()
    total_modules = df['EntityDesc'].nunique()
    total_grades = df['Grade'].nunique() if 'Grade' in df.columns else 0
    
    # Demographic summary
    demo_summary = []
    for demo_col in demographic_cols:
        if demo_col in df.columns:
            actual_count = df[demo_col].sum()
            actual_pct = (actual_count / total_people) * 100
            target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10))
            gap = actual_pct - target_pct
            status = "✅ On Target" if abs(gap) <= 2 else ("⚠️ Over" if gap > 0 else "❌ Under")
            
            demo_summary.append({
                'Demographic': demo_col,
                'Count': int(actual_count),
                'Actual_%': f"{actual_pct:.1f}%",
                'Target_%': f"{target_pct:.1f}%",
                'Gap': f"{gap:+.1f}%",
                'Status': status
            })
    
    # Create summary sections
    summary_sections = []
    
    # Overview section
    summary_sections.append({
        'Section': 'DATASET OVERVIEW',
        'Metric': 'Total People',
        'Value': f"{int(total_people):,}",
        'Notes': f"Across {total_modules} modules and {total_grades} grades"
    })
    
    summary_sections.append({
        'Section': 'DATASET OVERVIEW',
        'Metric': 'Total Modules',
        'Value': str(total_modules),
        'Notes': 'Unique educational content modules'
    })
    
    # Key findings
    if demo_summary:
        on_target = len([d for d in demo_summary if "On Target" in d['Status']])
        over_rep = len([d for d in demo_summary if "Over" in d['Status']])
        under_rep = len([d for d in demo_summary if "Under" in d['Status']])
        
        summary_sections.append({
            'Section': 'KEY FINDINGS',
            'Metric': 'Demographics On Target',
            'Value': f"{on_target}/{len(demo_summary)}",
            'Notes': f"{(on_target/len(demo_summary)*100):.0f}% within 2% of target"
        })
        
        summary_sections.append({
            'Section': 'KEY FINDINGS',
            'Metric': 'Over-represented',
            'Value': str(over_rep),
            'Notes': 'Demographics above target by >2%'
        })
        
        summary_sections.append({
            'Section': 'KEY FINDINGS',
            'Metric': 'Under-represented',
            'Value': str(under_rep),
            'Notes': 'Demographics below target by >2%'
        })
    
    return pd.DataFrame(summary_sections)

def create_detailed_module_report(df: pd.DataFrame, demographic_cols: List[str], 
                                targets: Dict[str, float]) -> pd.DataFrame:
    """Create detailed module-by-module report"""
    
    module_reports = []
    
    for entity in df['EntityDesc'].unique():
        entity_data = df[df['EntityDesc'] == entity]
        total_people = entity_data['TOTAL'].sum()
        
        if total_people == 0:
            continue
        
        # Calculate diversity metrics
        demo_counts = []
        for demo_col in demographic_cols:
            if demo_col in entity_data.columns:
                demo_counts.append(entity_data[demo_col].sum())
        
        if demo_counts:
            # Shannon diversity index
            proportions = np.array(demo_counts) / sum(demo_counts)
            proportions = proportions[proportions > 0]
            shannon_diversity = -np.sum(proportions * np.log(proportions)) if len(proportions) > 1 else 0
        else:
            shannon_diversity = 0
        
        # Find biggest gaps with proper division handling
        gaps = {}
        for demo_col in demographic_cols:
            if demo_col in entity_data.columns:
                actual_count = entity_data[demo_col].sum()
                actual_pct = (actual_count / total_people) * 100 if total_people > 0 else 0
                target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10))
                gaps[demo_col] = actual_pct - target_pct
        
        largest_gap = max(gaps.values()) if gaps else 0
        smallest_gap = min(gaps.values()) if gaps else 0
        
        module_reports.append({
            'Module_Name': entity,
            'Total_People': int(total_people),
            'Diversity_Score': f"{shannon_diversity:.2f}",
            'Largest_Overrep': f"{largest_gap:+.1f}%",
            'Largest_Underrep': f"{smallest_gap:+.1f}%",
            'Equity_Risk': 'High' if abs(largest_gap) > 15 or abs(smallest_gap) > 15 else 
                          'Medium' if abs(largest_gap) > 8 or abs(smallest_gap) > 8 else 'Low'
        })
    
    return pd.DataFrame(module_reports).sort_values('Total_People', ascending=False)

def create_recommendations_report(df: pd.DataFrame, demographic_cols: List[str], 
                                targets: Dict[str, float]) -> List[str]:
    """Generate actionable recommendations"""
    
    recommendations = []
    total_people = df['TOTAL'].sum()
    
    # Analyze overall representation
    underrep_demos = []
    overrep_demos = []
    
    for demo_col in demographic_cols:
        if demo_col in df.columns:
            actual_count = df[demo_col].sum()
            actual_pct = (actual_count / total_people) * 100
            target_pct = targets.get(demo_col.lower(), targets.get(demo_col, 10))
            gap = actual_pct - target_pct
            
            if gap < -5:  # More than 5% under target
                underrep_demos.append((demo_col, gap))
            elif gap > 5:  # More than 5% over target
                overrep_demos.append((demo_col, gap))
    
    # Generate recommendations
    if underrep_demos:
        worst_underrep = min(underrep_demos, key=lambda x: x[1])
        recommendations.append(
            f"PRIORITY: Increase {worst_underrep[0]} representation by {abs(worst_underrep[1]):.1f} percentage points"
        )
    
    if overrep_demos:
        worst_overrep = max(overrep_demos, key=lambda x: x[1])
        recommendations.append(
            f"BALANCE: Consider redistributing {worst_overrep[0]} representation ({worst_overrep[1]:+.1f}% above target)"
        )
    
    # Module-specific recommendations
    module_analysis = create_detailed_module_report(df, demographic_cols, targets)
    high_risk_modules = module_analysis[module_analysis['Equity_Risk'] == 'High']
    
    if len(high_risk_modules) > 0:
        recommendations.append(
            f"MODULES: {len(high_risk_modules)} modules have high equity risk - prioritize review"
        )
    
    # Diversity recommendations
    total_modules = df['EntityDesc'].nunique()
    small_modules = df.groupby('EntityDesc')['TOTAL'].sum()
    very_small = (small_modules < 20).sum()
    
    if very_small > total_modules * 0.3:
        recommendations.append(
            f"SCALE: {very_small} modules have <20 people - consider consolidation for better representation"
        )
    
    if not recommendations:
        recommendations.append("EXCELLENT: Dataset shows good demographic balance across all metrics")
    
    return recommendations

def export_comprehensive_report(df: pd.DataFrame, demographic_cols: List[str], 
                               targets: Dict[str, float], analysis_results: Dict[str, Any] = None) -> bytes:
    """Export comprehensive analysis report to Excel"""
    
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Create formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Executive Summary
        exec_summary = create_executive_summary_report(df, demographic_cols, targets, analysis_results or {})
        exec_summary.to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # Module Details
        module_details = create_detailed_module_report(df, demographic_cols, targets)
        module_details.to_excel(writer, sheet_name='Module Analysis', index=False)
        
        # Recommendations
        recommendations = create_recommendations_report(df, demographic_cols, targets)
        rec_df = pd.DataFrame({'Recommendations': recommendations})
        rec_df.to_excel(writer, sheet_name='Recommendations', index=False)
        
        # Raw Data (filtered)
        df.to_excel(writer, sheet_name='Raw Data', index=False)
        
        # Format headers
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col_num, value in enumerate(exec_summary.columns if sheet_name == 'Executive Summary' else 
                                          module_details.columns if sheet_name == 'Module Analysis' else
                                          rec_df.columns if sheet_name == 'Recommendations' else df.columns):
                worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return output.read()

def create_download_button(data: bytes, filename: str, button_text: str, mime_type: str = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
    """Create a download button for the report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.xlsx"
    
    st.download_button(
        label=button_text,
        data=data,
        file_name=full_filename,
        mime=mime_type,
        help=f"Download {filename} with timestamp {timestamp}"
    )