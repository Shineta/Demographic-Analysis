import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import streamlit as st

class DataHealthChecker:
    """
    Comprehensive data health checker for demographic analysis
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.issues = []
        self.warnings = []
        self.info = []
        
    def run_comprehensive_check(self) -> Dict[str, List[str]]:
        """
        Run all data health checks and return categorized results
        
        Returns:
            Dictionary with 'critical', 'warning', and 'info' keys
        """
        self.issues = []
        self.warnings = []
        self.info = []
        
        # Run all checks
        self._check_required_columns()
        self._check_demographic_data_quality()
        self._check_total_consistency()
        self._check_missing_values()
        self._check_data_completeness()
        self._check_demographic_distribution()
        
        return {
            'critical': self.issues,
            'warning': self.warnings,
            'info': self.info
        }
    
    def _check_required_columns(self):
        """Check for required columns"""
        required_cols = ['EntityDesc', 'Grade', 'TOTAL']
        missing_required = [col for col in required_cols if col not in self.df.columns]
        
        if missing_required:
            self.issues.append(f"Missing required columns: {', '.join(missing_required)}")
        else:
            self.info.append("All required columns (EntityDesc, Grade, TOTAL) are present")
    
    def _check_demographic_data_quality(self):
        """Check demographic data quality"""
        from .data_processor import DataProcessor
        processor = DataProcessor(self.df)
        demographic_cols = processor.get_demographic_columns()
        
        if not demographic_cols:
            self.warnings.append("No demographic columns detected in the dataset")
            return
        
        self.info.append(f"Found {len(demographic_cols)} demographic columns: {', '.join(demographic_cols[:5])}")
        if len(demographic_cols) > 5:
            self.info.append(f"...and {len(demographic_cols) - 5} more demographic columns")
        
        # Check for all-zero demographic fields
        zero_demographics = []
        for demo_col in demographic_cols:
            if demo_col in self.df.columns:
                total_count = self.df[demo_col].sum()
                if total_count == 0:
                    zero_demographics.append(demo_col)
        
        if zero_demographics:
            self.warnings.append(f"Demographics with zero values: {', '.join(zero_demographics)}")
        
        # Check for very sparse demographics (less than 1% of total)
        if 'TOTAL' in self.df.columns:
            total_people = self.df['TOTAL'].sum()
            sparse_demographics = []
            
            for demo_col in demographic_cols:
                if demo_col in self.df.columns:
                    demo_count = self.df[demo_col].sum()
                    if demo_count > 0 and demo_count < (total_people * 0.01):
                        sparse_demographics.append(f"{demo_col} ({demo_count} people, {demo_count/total_people*100:.1f}%)")
            
            if sparse_demographics:
                self.info.append(f"Very sparse demographics (< 1%): {', '.join(sparse_demographics)}")
    
    def _check_total_consistency(self):
        """Check if demographic sums match TOTAL column"""
        if 'TOTAL' not in self.df.columns:
            return
        
        from .data_processor import DataProcessor
        processor = DataProcessor(self.df)
        demographic_cols = processor.get_demographic_columns()
        
        if not demographic_cols:
            return
        
        inconsistent_rows = []
        missing_attribution_rows = []
        
        for idx, row in self.df.iterrows():
            total_specified = row.get('TOTAL', 0)
            demo_sum = sum(row.get(col, 0) for col in demographic_cols if col in self.df.columns)
            
            if demo_sum > total_specified and total_specified > 0:
                inconsistent_rows.append(f"Row {idx+1}: Demographic sum ({demo_sum}) > TOTAL ({total_specified})")
            elif demo_sum < total_specified and total_specified > 0:
                gap = total_specified - demo_sum
                if gap > (total_specified * 0.1):  # More than 10% missing
                    missing_attribution_rows.append(f"Row {idx+1}: {gap} people unassigned ({gap/total_specified*100:.1f}%)")
        
        if inconsistent_rows:
            self.issues.extend(inconsistent_rows[:5])  # Show first 5
            if len(inconsistent_rows) > 5:
                self.issues.append(f"...and {len(inconsistent_rows) - 5} more rows with demographic sum > TOTAL")
        
        if missing_attribution_rows:
            self.warnings.extend(missing_attribution_rows[:3])  # Show first 3
            if len(missing_attribution_rows) > 3:
                self.warnings.append(f"...and {len(missing_attribution_rows) - 3} more rows with significant unassigned people")
    
    def _check_missing_values(self):
        """Check for missing values in critical columns"""
        critical_cols = ['EntityDesc', 'Grade']
        
        for col in critical_cols:
            if col in self.df.columns:
                missing_count = self.df[col].isna().sum()
                if missing_count > 0:
                    self.warnings.append(f"{col} has {missing_count} missing values")
    
    def _check_data_completeness(self):
        """Check overall data completeness"""
        total_rows = len(self.df)
        total_modules = self.df['EntityDesc'].nunique() if 'EntityDesc' in self.df.columns else 0
        total_grades = self.df['Grade'].nunique() if 'Grade' in self.df.columns else 0
        
        self.info.append(f"Dataset contains {total_rows} rows across {total_modules} modules and {total_grades} grades")
        
        if 'TOTAL' in self.df.columns:
            total_people = self.df['TOTAL'].sum()
            self.info.append(f"Total people in dataset: {int(total_people):,}")
            
            # Check for modules with very few people
            if 'EntityDesc' in self.df.columns:
                module_totals = self.df.groupby('EntityDesc')['TOTAL'].sum()
                small_modules = module_totals[module_totals < 10]
                if len(small_modules) > 0:
                    self.warnings.append(f"{len(small_modules)} modules have fewer than 10 people")
    
    def _check_demographic_distribution(self):
        """Check demographic distribution patterns"""
        from .data_processor import DataProcessor
        processor = DataProcessor(self.df)
        demographic_cols = processor.get_demographic_columns()
        
        if not demographic_cols or 'TOTAL' not in self.df.columns:
            return
        
        total_people = self.df['TOTAL'].sum()
        if total_people == 0:
            return
        
        # Calculate overall demographic percentages
        demo_percentages = {}
        for demo_col in demographic_cols:
            if demo_col in self.df.columns:
                demo_count = self.df[demo_col].sum()
                percentage = (demo_count / total_people) * 100
                demo_percentages[demo_col] = percentage
        
        # Find dominant demographics (> 50%)
        dominant_demos = [col for col, pct in demo_percentages.items() if pct > 50]
        if dominant_demos:
            self.info.append(f"Dominant demographics (>50%): {', '.join(f'{col} ({demo_percentages[col]:.1f}%)' for col in dominant_demos)}")
        
        # Find underrepresented demographics (< 5%)
        underrep_demos = [col for col, pct in demo_percentages.items() if 0 < pct < 5]
        if underrep_demos:
            self.info.append(f"Underrepresented demographics (<5%): {', '.join(f'{col} ({demo_percentages[col]:.1f}%)' for col in underrep_demos)}")

def display_health_check_results(results: Dict[str, List[str]]):
    """Display health check results in Streamlit"""
    
    # Critical Issues
    if results['critical']:
        st.error("🚫 Critical Issues Found")
        for issue in results['critical']:
            st.error(f"• {issue}")
        st.write("**Action Required:** Please fix these issues before proceeding with analysis.")
        return False
    
    # Warnings
    if results['warning']:
        st.warning("⚠️ Data Quality Warnings")
        for warning in results['warning']:
            st.warning(f"• {warning}")
        st.write("**Recommendation:** Review these warnings - they may affect analysis accuracy.")
    
    # Informational
    if results['info']:
        st.success("📊 Data Summary")
        for info in results['info']:
            st.info(f"• {info}")
    
    # Overall health status
    if not results['critical'] and not results['warning']:
        st.success("✅ Excellent! Your data passed all health checks.")
    elif not results['critical']:
        st.info("✅ Good! Data is usable with minor warnings noted above.")
    
    return True  # Data is usable

def validate_column_headers(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate and suggest column header corrections
    
    Returns:
        Tuple of (is_valid, suggestions)
    """
    suggestions = []
    
    # Expected column patterns
    expected_patterns = {
        'EntityDesc': ['entity', 'entitydesc', 'entity_desc', 'module', 'lesson'],
        'Grade': ['grade', 'level', 'year'],
        'TOTAL': ['total', 'spec_count', 'speccount', 'count', 'sum'],
        'Component Desc': ['component', 'componentdesc', 'component_desc', 'type']
    }
    
    df_columns_lower = [col.lower().strip().replace(' ', '_') for col in df.columns]
    
    for expected_col, patterns in expected_patterns.items():
        if expected_col not in df.columns:
            # Look for similar columns
            matches = [col for col in df.columns if any(pattern in col.lower().replace(' ', '_') for pattern in patterns)]
            if matches:
                suggestions.append(f"Consider renaming '{matches[0]}' to '{expected_col}'")
    
    return len(suggestions) == 0, suggestions