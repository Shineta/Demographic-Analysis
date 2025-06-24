import pandas as pd
import io
from typing import Dict, List, Any
import xlsxwriter

def export_to_excel(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    """
    Export DataFrame to Excel format in memory
    
    Args:
        df: DataFrame to export
        sheet_name: Name of the Excel sheet
        
    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Write the column headers with formatting
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Auto-adjust column widths
        for i, col in enumerate(df.columns):
            # Get the maximum length in the column
            max_length = max(
                df[col].astype(str).map(len).max(),  # Length of largest item
                len(str(col))  # Length of column name/header
            ) + 2  # Add a little extra space
            
            worksheet.set_column(i, i, min(max_length, 50))  # Cap at 50 characters
    
    output.seek(0)
    return output.getvalue()

def export_multiple_sheets(data_dict: Dict[str, pd.DataFrame]) -> bytes:
    """
    Export multiple DataFrames to different sheets in one Excel file
    
    Args:
        data_dict: Dictionary with sheet names as keys and DataFrames as values
        
    Returns:
        Excel file as bytes
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        number_format = workbook.add_format({'num_format': '#,##0'})
        percentage_format = workbook.add_format({'num_format': '0.00%'})
        
        for sheet_name, df in data_dict.items():
            if df.empty:
                continue
                
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-adjust column widths and apply number formatting
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                ) + 2
                
                worksheet.set_column(i, i, min(max_length, 50))
                
                # Apply specific formatting based on column content
                if 'percentage' in col.lower() or col.endswith('%'):
                    worksheet.set_column(i, i, None, percentage_format)
                elif df[col].dtype in ['int64', 'float64'] and 'total' in col.lower():
                    worksheet.set_column(i, i, None, number_format)
    
    output.seek(0)
    return output.getvalue()

def export_heatmap_data(df: pd.DataFrame, demographic_cols: List[str]) -> pd.DataFrame:
    """
    Prepare heatmap data for export
    
    Args:
        df: Input DataFrame
        demographic_cols: List of demographic column names
        
    Returns:
        DataFrame formatted for heatmap export
    """
    if df.empty or not demographic_cols:
        return pd.DataFrame()
    
    heatmap_export_data = []
    
    for entity in df['EntityDesc'].unique():
        entity_data = df[df['EntityDesc'] == entity]
        total_people = entity_data['TOTAL'].sum()
        
        if total_people == 0:
            continue
        
        # Get grade and component info
        grades = entity_data['Grade'].unique()
        components = entity_data['Component Desc'].unique()
        
        row_data = {
            'EntityDesc': entity,
            'Grades': ', '.join(grades),
            'Components': ', '.join(components),
            'Total_People': total_people
        }
        
        # Add demographic counts and percentages
        for demo_col in demographic_cols:
            if demo_col in entity_data.columns:
                demo_count = entity_data[demo_col].sum()
                demo_percentage = (demo_count / total_people) * 100 if total_people > 0 else 0
                
                row_data[f"{demo_col}_Count"] = demo_count
                row_data[f"{demo_col}_Percentage"] = round(demo_percentage, 2)
            else:
                row_data[f"{demo_col}_Count"] = 0
                row_data[f"{demo_col}_Percentage"] = 0.0
        
        heatmap_export_data.append(row_data)
    
    return pd.DataFrame(heatmap_export_data)

def create_analysis_summary(df: pd.DataFrame, filters_applied: Dict[str, List[Any]], 
                          demographic_cols: List[str], targets: Dict[str, float]) -> pd.DataFrame:
    """
    Create a summary of the analysis for export
    
    Args:
        df: Filtered DataFrame
        filters_applied: Dictionary of applied filters
        demographic_cols: List of demographic columns
        targets: Target percentages for demographics
        
    Returns:
        Summary DataFrame
    """
    summary_data = []
    
    # Basic statistics
    summary_data.append({
        'Metric': 'Total Records',
        'Value': len(df),
        'Description': 'Number of rows in filtered dataset'
    })
    
    summary_data.append({
        'Metric': 'Total People',
        'Value': df['TOTAL'].sum() if not df.empty else 0,
        'Description': 'Sum of all people across filtered records'
    })
    
    summary_data.append({
        'Metric': 'Unique Modules',
        'Value': df['EntityDesc'].nunique() if not df.empty else 0,
        'Description': 'Number of unique modules/entities'
    })
    
    summary_data.append({
        'Metric': 'Unique Grades',
        'Value': df['Grade'].nunique() if not df.empty else 0,
        'Description': 'Number of different grade levels'
    })
    
    # Filter information
    for filter_name, filter_values in filters_applied.items():
        if filter_values:
            summary_data.append({
                'Metric': f'Filter: {filter_name}',
                'Value': len(filter_values),
                'Description': f'Number of selected {filter_name} values'
            })
    
    # Demographic analysis
    if not df.empty and demographic_cols:
        total_people = df['TOTAL'].sum()
        
        for demo_col in demographic_cols:
            if demo_col in df.columns:
                demo_count = df[demo_col].sum()
                demo_percentage = (demo_count / total_people) * 100 if total_people > 0 else 0
                target_percentage = targets.get(demo_col, 0)
                gap = demo_percentage - target_percentage
                
                summary_data.append({
                    'Metric': f'{demo_col} Actual %',
                    'Value': round(demo_percentage, 2),
                    'Description': f'Actual percentage of {demo_col} demographic'
                })
                
                summary_data.append({
                    'Metric': f'{demo_col} Gap',
                    'Value': round(gap, 2),
                    'Description': f'Difference from target ({target_percentage}%)'
                })
    
    return pd.DataFrame(summary_data)

def export_comprehensive_analysis(df: pd.DataFrame, filters_applied: Dict[str, List[Any]], 
                                demographic_cols: List[str], targets: Dict[str, float],
                                module_totals: pd.DataFrame) -> bytes:
    """
    Export a comprehensive analysis with multiple sheets
    
    Args:
        df: Filtered DataFrame
        filters_applied: Applied filters
        demographic_cols: Demographic columns
        targets: Target percentages
        module_totals: Module totals DataFrame
        
    Returns:
        Excel file as bytes
    """
    # Prepare data for different sheets
    sheets_data = {}
    
    # Raw filtered data
    if not df.empty:
        sheets_data['Filtered_Data'] = df
    
    # Module totals
    if not module_totals.empty:
        sheets_data['Module_Totals'] = module_totals
    
    # Heatmap data
    heatmap_data = export_heatmap_data(df, demographic_cols)
    if not heatmap_data.empty:
        sheets_data['Heatmap_Data'] = heatmap_data
    
    # Analysis summary
    summary_data = create_analysis_summary(df, filters_applied, demographic_cols, targets)
    if not summary_data.empty:
        sheets_data['Analysis_Summary'] = summary_data
    
    # Demographic gaps
    if not df.empty and demographic_cols:
        gaps_data = []
        total_people = df['TOTAL'].sum()
        
        for demo_col in demographic_cols:
            if demo_col in df.columns:
                demo_count = df[demo_col].sum()
                demo_percentage = (demo_count / total_people) * 100 if total_people > 0 else 0
                target_percentage = targets.get(demo_col, 0)
                gap = demo_percentage - target_percentage
                
                gaps_data.append({
                    'Demographic': demo_col,
                    'Count': demo_count,
                    'Actual_Percentage': round(demo_percentage, 2),
                    'Target_Percentage': target_percentage,
                    'Gap': round(gap, 2),
                    'Status': 'Over Target' if gap > 0 else 'Under Target' if gap < 0 else 'On Target'
                })
        
        if gaps_data:
            sheets_data['Demographic_Gaps'] = pd.DataFrame(gaps_data)
    
    # Export all sheets
    return export_multiple_sheets(sheets_data)
