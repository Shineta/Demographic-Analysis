import pandas as pd
from typing import List, Dict, Tuple
from .data_processor import DataProcessor

def validate_modules_with_demographic_data(processor: DataProcessor) -> Dict[str, List[str]]:
    """
    Validate which modules have demographic data available
    
    Args:
        processor: DataProcessor instance
        
    Returns:
        Dictionary with 'with_data' and 'without_data' lists
    """
    entities = processor.get_unique_values('EntityDesc')
    demographic_cols = processor.get_demographic_columns()
    
    modules_with_data = []
    modules_without_data = []
    
    for entity in entities:
        entity_data = processor.df[processor.df['EntityDesc'] == entity]
        has_demo_data = False
        
        # Check if any demographic column has data > 0
        for demo_col in demographic_cols:
            if demo_col in entity_data.columns and entity_data[demo_col].sum() > 0:
                has_demo_data = True
                break
        
        if has_demo_data:
            modules_with_data.append(entity)
        else:
            modules_without_data.append(entity)
    
    return {
        'with_data': modules_with_data,
        'without_data': modules_without_data
    }

def create_enhanced_module_options(modules_status: Dict[str, List[str]]) -> List[str]:
    """
    Create enhanced module options with data availability indicators
    
    Args:
        modules_status: Dictionary from validate_modules_with_demographic_data
        
    Returns:
        List of formatted module options
    """
    options = ["All Modules"]
    
    # Add modules with data (marked with checkmark)
    for module in modules_status['with_data']:
        options.append(f"{module} ✓")
    
    # Add modules without data (marked as unavailable)
    for module in modules_status['without_data']:
        options.append(f"{module} (no data)")
    
    return options

def get_actual_module_name(selected_option: str) -> str:
    """
    Extract the actual module name from a formatted option
    
    Args:
        selected_option: The selected option from the dropdown
        
    Returns:
        Clean module name without indicators
    """
    if selected_option == "All Modules":
        return selected_option
    
    # Remove indicators
    return selected_option.replace(" ✓", "").replace(" (no data)", "")

def check_module_has_data(selected_option: str) -> bool:
    """
    Check if the selected module has demographic data
    
    Args:
        selected_option: The selected option from the dropdown
        
    Returns:
        True if module has data, False otherwise
    """
    return " ✓" in selected_option or selected_option == "All Modules"