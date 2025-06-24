import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class DataProcessor:
    """
    Handles data processing operations for demographic analysis
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the data processor with a DataFrame
        
        Args:
            df: Input DataFrame containing demographic data
        """
        self.df = df.copy()
        self.original_df = df.copy()
        self._validate_data()
        
    def _validate_data(self):
        """
        Validate that the DataFrame contains required columns with flexible matching
        """
        # Map of required columns to possible variations
        column_mappings = {
            'Grade': ['grade', 'level', 'grade level', 'gradelevel'],
            'EntityDesc': ['entity', 'entitydesc', 'entity desc', 'entity description', 
                          'module', 'lesson', 'title', 'content', 'lesson title'],
            'Component Desc': ['component', 'componentdesc', 'component desc', 
                              'component description', 'activity', 'activity type'],
            'TOTAL': ['total', 'total people', 'people', 'count', 'sum', 'total count']
        }
        
        # Try to map columns
        mapped_columns = {}
        available_columns = [col.lower().strip() for col in self.df.columns]
        
        for required_col, variations in column_mappings.items():
            found = False
            for variation in variations:
                if variation.lower() in available_columns:
                    # Find the actual column name (preserving case)
                    actual_col = next(col for col in self.df.columns 
                                    if col.lower().strip() == variation.lower())
                    mapped_columns[required_col] = actual_col
                    found = True
                    break
            
            if not found:
                # Check for partial matches
                for col in self.df.columns:
                    col_lower = col.lower().strip()
                    if any(var in col_lower for var in variations):
                        mapped_columns[required_col] = col
                        found = True
                        break
        
        # If we couldn't map all required columns, provide helpful suggestions
        missing_required = [col for col in column_mappings.keys() if col not in mapped_columns]
        
        if missing_required:
            available_cols_str = ", ".join(self.df.columns.tolist())
            suggestions = []
            
            for missing_col in missing_required:
                variations = column_mappings[missing_col]
                suggestions.append(f"{missing_col}: looking for columns like {', '.join(variations[:3])}")
            
            error_msg = (f"Could not find required columns: {missing_required}\n\n"
                        f"Available columns in your file: {available_cols_str}\n\n"
                        f"Suggestions:\n" + "\n".join(suggestions))
            raise ValueError(error_msg)
        
        # Rename columns to standard names
        rename_dict = {v: k for k, v in mapped_columns.items()}
        self.df = self.df.rename(columns=rename_dict)
        
        # Convert TOTAL to numeric, handling any non-numeric values
        self.df['TOTAL'] = pd.to_numeric(self.df['TOTAL'], errors='coerce').fillna(0)
        
    def get_unique_values(self, column: str) -> List[Any]:
        """
        Get unique values from a column, sorted
        
        Args:
            column: Column name to get unique values from
            
        Returns:
            List of unique values
        """
        if column not in self.df.columns:
            return []
            
        unique_vals = self.df[column].dropna().unique()
        
        # Sort values, handling mixed types
        try:
            return sorted(unique_vals)
        except TypeError:
            # If sorting fails due to mixed types, convert to string and sort
            return sorted([str(val) for val in unique_vals])
    
    def apply_filters(self, filters: Dict[str, List[Any]]) -> pd.DataFrame:
        """
        Apply multiple filters to the DataFrame
        
        Args:
            filters: Dictionary of column names and their filter values
            
        Returns:
            Filtered DataFrame
        """
        filtered_df = self.df.copy()
        
        for column, values in filters.items():
            if column in filtered_df.columns and values:
                filtered_df = filtered_df[filtered_df[column].isin(values)]
                
        return filtered_df
    
    def get_demographic_columns(self) -> List[str]:
        """
        Identify demographic columns in the dataset
        
        Returns:
            List of demographic column names
        """
        # Approved demographic column patterns (whitelist approach)
        approved_demographic_patterns = [
            # Standard abbreviations
            'AAM', 'AAF', 'PCM', 'PCF', 'LGBTF', 'OTHER_M', 'OTHER_F',
            'ASM', 'ASF', 'HM', 'HF', 'NAM', 'NAF', 'PIM', 'PIF',
            'LEGACY_M', 'LEGACY_F', 'PC_M', 'PC_F',
            
            # Full names
            'african american male', 'african american female', 'african american',
            'asian male', 'asian female', 'asian',
            'caucasian male', 'caucasian female', 'caucasian', 'white',
            'hispanic male', 'hispanic female', 'hispanic', 'latino', 'latina',
            'native american male', 'native american female', 'native american',
            'pacific islander male', 'pacific islander female', 'pacific islander',
            'lgbt', 'lgbtq', 'lgbtf', 'lgbt female', 'lgbt male',
            'legacy', 'legacy male', 'legacy female',
            'physically challenged', 'physically challenged male', 'physically challenged female',
            'other', 'other male', 'other female',
            'male', 'female'
        ]
        
        demographic_cols = []
        
        for col in self.df.columns:
            col_lower = col.lower().strip()
            
            # Strict exclusion of non-demographic columns
            exclude_patterns = [
                'total', 'grade', 'entity', 'component', 'desc', 'description', 
                'id', 'name', 'date', 'time', 'page', 'folio', 'number', 'count',
                'row', 'index', 'file', 'path', 'url', 'link', 'reference',
                'score', 'rating', 'level', 'category', 'type', 'status'
            ]
            
            # Skip if column matches exclusion patterns
            if any(exclude in col_lower for exclude in exclude_patterns):
                continue
            
            # Include only if column matches approved demographic patterns
            for pattern in approved_demographic_patterns:
                if pattern.lower() in col_lower:
                    demographic_cols.append(col)
                    break
        
        return demographic_cols
    
    def get_default_demographic_targets(self) -> Dict[str, float]:
        """
        Get default target percentages for demographics based on equity-driven values
        
        Returns:
            Dictionary with default target percentages
        """
        default_targets = {
            # Gender representation (aim for balanced)
            'male': 50.0,
            'female': 50.0,
            
            # Race/ethnicity (based on US demographic representation goals)
            'african american': 12.0,
            'african american male': 6.0,
            'african american female': 6.0,
            'aam': 6.0,
            'aaf': 6.0,
            
            'hispanic': 18.0,
            'hispanic male': 9.0,
            'hispanic female': 9.0,
            'hm': 9.0,
            'hf': 9.0,
            
            'asian': 6.0,
            'asian male': 3.0,
            'asian female': 3.0,
            'asm': 3.0,
            'asf': 3.0,
            
            'caucasian': 60.0,
            'caucasian male': 30.0,
            'caucasian female': 30.0,
            'pcm': 30.0,
            'pcf': 30.0,
            'white': 60.0,
            
            'native american': 1.0,
            'native american male': 0.5,
            'native american female': 0.5,
            'nam': 0.5,
            'naf': 0.5,
            
            'pacific islander': 0.5,
            'pacific islander male': 0.25,
            'pacific islander female': 0.25,
            'pim': 0.25,
            'pif': 0.25,
            
            # Other categories
            'lgbt': 7.0,
            'lgbtf': 7.0,
            'lgbtq': 7.0,
            
            'legacy': 5.0,
            'legacy male': 2.5,
            'legacy female': 2.5,
            
            'physically challenged': 2.0,
            'pc_m': 1.0,
            'pc_f': 1.0,
            
            'other': 3.0,
            'other male': 1.5,
            'other female': 1.5,
            'other_m': 1.5,
            'other_f': 1.5
        }
        
        return default_targets
    
    def calculate_module_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total people per module (EntityDesc)
        
        Args:
            df: Input DataFrame (usually filtered)
            
        Returns:
            DataFrame with module totals
        """
        if df.empty:
            return pd.DataFrame(columns=['EntityDesc', 'Grade', 'Total People'])
            
        # Group by EntityDesc and Grade, sum the TOTAL column
        module_totals = df.groupby(['EntityDesc', 'Grade'])['TOTAL'].sum().reset_index()
        module_totals.columns = ['EntityDesc', 'Grade', 'Total People']
        
        # Sort by Total People descending
        module_totals = module_totals.sort_values('Total People', ascending=False)
        
        return module_totals
    
    def calculate_demographic_percentages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate demographic percentages for heat map
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with demographic percentages
        """
        demographic_cols = self.get_demographic_columns()
        
        if not demographic_cols or df.empty:
            return pd.DataFrame()
        
        # Calculate percentages for each demographic
        result_data = []
        
        # Group by relevant dimensions
        for entity in df['EntityDesc'].unique():
            entity_data = df[df['EntityDesc'] == entity]
            
            if entity_data.empty:
                continue
                
            total_people = entity_data['TOTAL'].sum()
            
            if total_people == 0:
                continue
                
            row_data = {'EntityDesc': entity}
            
            # Calculate percentage for each demographic
            for demo_col in demographic_cols:
                if demo_col in entity_data.columns:
                    demo_total = entity_data[demo_col].sum()
                    percentage = (demo_total / total_people) * 100 if total_people > 0 else 0
                    row_data[demo_col] = round(percentage, 2)
                else:
                    row_data[demo_col] = 0.0
            
            result_data.append(row_data)
        
        return pd.DataFrame(result_data)
    
    def calculate_demographic_gaps(self, df: pd.DataFrame, targets: Dict[str, float]) -> pd.DataFrame:
        """
        Calculate gaps between actual and target demographic representation
        
        Args:
            df: Input DataFrame
            targets: Dictionary of demographic targets (percentages)
            
        Returns:
            DataFrame showing gaps
        """
        demographic_cols = self.get_demographic_columns()
        
        if not demographic_cols or df.empty:
            return pd.DataFrame()
        
        # Calculate actual percentages
        total_people = df['TOTAL'].sum()
        
        if total_people == 0:
            return pd.DataFrame()
        
        gaps_data = []
        
        for demo_col in demographic_cols:
            if demo_col in df.columns:
                actual_count = df[demo_col].sum()
                actual_percentage = (actual_count / total_people) * 100
                target_percentage = targets.get(demo_col, 0.0)
                gap = actual_percentage - target_percentage
                
                gaps_data.append({
                    'Demographic': demo_col,
                    'Actual Count': actual_count,
                    'Actual %': round(actual_percentage, 2),
                    'Target %': target_percentage,
                    'Gap': round(gap, 2),
                    'Gap Status': 'Over Target' if gap > 0 else 'Under Target' if gap < 0 else 'On Target'
                })
        
        gaps_df = pd.DataFrame(gaps_data)
        return gaps_df.sort_values('Gap')
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary statistics for the dataset
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {}
        
        demographic_cols = self.get_demographic_columns()
        
        stats = {
            'total_rows': len(df),
            'total_people': df['TOTAL'].sum(),
            'unique_grades': df['Grade'].nunique(),
            'unique_entities': df['EntityDesc'].nunique(),
            'unique_components': df['Component Desc'].nunique(),
            'demographic_columns': len(demographic_cols),
            'avg_people_per_row': df['TOTAL'].mean(),
            'median_people_per_row': df['TOTAL'].median()
        }
        
        return stats
    
    def calculate_demographic_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate demographic trends across modules/grades
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with trend analysis
        """
        demographic_cols = self.get_demographic_columns()
        if not demographic_cols:
            return pd.DataFrame()
        
        trend_data = []
        
        # Group by Grade and EntityDesc for trend analysis
        for grade in df['Grade'].unique():
            grade_data = df[df['Grade'] == grade]
            
            for entity in grade_data['EntityDesc'].unique():
                entity_data = grade_data[grade_data['EntityDesc'] == entity]
                total_people = entity_data['TOTAL'].sum()
                
                if total_people == 0:
                    continue
                
                row = {
                    'Grade': grade,
                    'EntityDesc': entity,
                    'Total_People': total_people
                }
                
                # Calculate percentages for each demographic
                for demo_col in demographic_cols:
                    if demo_col in entity_data.columns:
                        demo_count = entity_data[demo_col].sum()
                        percentage = (demo_count / total_people) * 100
                        row[f'{demo_col}_Count'] = demo_count
                        row[f'{demo_col}_Percentage'] = percentage
                
                trend_data.append(row)
        
        return pd.DataFrame(trend_data)
    
    def calculate_grade_comparisons(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Calculate demographic comparisons across grades
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with comparison DataFrames
        """
        demographic_cols = self.get_demographic_columns()
        if not demographic_cols:
            return {}
        
        comparisons = {}
        
        # Grade-level aggregation
        grade_summary = []
        for grade in df['Grade'].unique():
            grade_data = df[df['Grade'] == grade]
            total_people = grade_data['TOTAL'].sum()
            
            if total_people == 0:
                continue
            
            row = {'Grade': grade, 'Total_People': total_people}
            
            for demo_col in demographic_cols:
                if demo_col in grade_data.columns:
                    demo_count = grade_data[demo_col].sum()
                    percentage = (demo_count / total_people) * 100
                    row[f'{demo_col}_Count'] = demo_count
                    row[f'{demo_col}_Percentage'] = percentage
            
            grade_summary.append(row)
        
        comparisons['grade_summary'] = pd.DataFrame(grade_summary)
        
        # Component-level aggregation
        component_summary = []
        for component in df['Component Desc'].unique():
            comp_data = df[df['Component Desc'] == component]
            total_people = comp_data['TOTAL'].sum()
            
            if total_people == 0:
                continue
            
            row = {'Component': component, 'Total_People': total_people}
            
            for demo_col in demographic_cols:
                if demo_col in comp_data.columns:
                    demo_count = comp_data[demo_col].sum()
                    percentage = (demo_count / total_people) * 100
                    row[f'{demo_col}_Count'] = demo_count
                    row[f'{demo_col}_Percentage'] = percentage
            
            component_summary.append(row)
        
        comparisons['component_summary'] = pd.DataFrame(component_summary)
        
        return comparisons
    
    def calculate_diversity_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate diversity and equity metrics
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with diversity metrics
        """
        demographic_cols = self.get_demographic_columns()
        if not demographic_cols:
            return {}
        
        metrics = {}
        total_people = df['TOTAL'].sum()
        
        if total_people == 0:
            return metrics
        
        # Calculate Simpson's Diversity Index
        diversity_sum = 0
        for demo_col in demographic_cols:
            if demo_col in df.columns:
                demo_count = df[demo_col].sum()
                proportion = demo_count / total_people
                diversity_sum += proportion ** 2
        
        simpson_diversity = 1 - diversity_sum
        metrics['simpson_diversity_index'] = simpson_diversity
        
        # Calculate Shannon Diversity Index
        shannon_diversity = 0
        for demo_col in demographic_cols:
            if demo_col in df.columns:
                demo_count = df[demo_col].sum()
                if demo_count > 0:
                    proportion = demo_count / total_people
                    shannon_diversity -= proportion * np.log(proportion)
        
        metrics['shannon_diversity_index'] = shannon_diversity
        
        # Calculate representation balance (coefficient of variation)
        demo_percentages = []
        for demo_col in demographic_cols:
            if demo_col in df.columns:
                demo_count = df[demo_col].sum()
                percentage = (demo_count / total_people) * 100
                demo_percentages.append(percentage)
        
        if demo_percentages:
            mean_percentage = np.mean(demo_percentages)
            std_percentage = np.std(demo_percentages)
            cv = std_percentage / mean_percentage if mean_percentage > 0 else 0
            metrics['representation_balance'] = 1 / (1 + cv)  # Normalized to 0-1
        
        return metrics
