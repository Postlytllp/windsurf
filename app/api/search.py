"""
Search module for the Clinical Trials & FDA Data Search App.
Handles search requests for clinical trials and FDA data.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
import sys
import os
from pathlib import Path
import pandas as pd

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the data fetching modules
from clinical_trials_module import get_clinical_trials_data
from openfda import Open_FDA
from app.models.user import User
from app.api.auth import get_current_user

# Initialize router
search_router = APIRouter()

class SearchRequest(BaseModel):
    """Search request model."""
    keyword: str
    searchType: str = "disease"  # 'disease' or 'drug'

class SearchResponse(BaseModel):
    """Search response model."""
    clinical_trials: List[Dict[str, Any]]
    fda_data: List[Dict[str, Any]]
    total_clinical_trials: int
    total_fda_data: int

# Helper function to safely convert data types
def safe_convert_types(df, column_types=None):
    """
    Safely convert DataFrame column types with detailed error reporting.
    
    Args:
        df: pandas DataFrame to convert
        column_types: dictionary mapping column names to their target types
    
    Returns:
        Converted DataFrame
    """
    if df is None or len(df) == 0:
        return df
    
    if column_types is None:
        column_types = {}
    
    # Default type conversions based on schema
    default_conversions = {
        # Clinical trials columns
        'enrollmentCount': 'int',
        'hasExpandedAccess': 'bool',
        'HasResults': 'bool',
        'healthyVolunteers': 'bool',
        
        # FDA columns
        'is_original_packager': 'bool'
    }
    
    # Merge with provided column types
    column_types = {**default_conversions, **column_types}
    
    # Fill NaN values with appropriate defaults
    default_values = {
        'int': 0,
        'bool': False,
        'str': '',
        'float': 0.0
    }
    
    # Process each column
    for column, dtype in column_types.items():
        if column in df.columns:
            try:
                print(f"Converting column '{column}' to {dtype}")
                
                # Fill NaN values with appropriate defaults
                if dtype == 'int':
                    # For integer columns, first convert to float, then to int
                    df[column] = df[column].fillna(default_values['float'])
                    # Check if values are actually integers
                    if df[column].apply(lambda x: x != int(x) if pd.notna(x) else False).any():
                        print(f"WARNING: Column '{column}' contains non-integer values: {df[column].unique()}")
                    df[column] = df[column].astype(float).astype(int)
                elif dtype == 'bool':
                    df[column] = df[column].fillna(default_values['bool']).astype(bool)
                elif dtype == 'str':
                    df[column] = df[column].fillna(default_values['str']).astype(str)
                elif dtype == 'float':
                    df[column] = df[column].fillna(default_values['float']).astype(float)
            except Exception as e:
                print(f"ERROR converting column '{column}' to {dtype}: {str(e)}")
                print(f"Column values: {df[column].unique()}")
                # If conversion fails, convert to string as a fallback
                df[column] = df[column].fillna('').astype(str)
    
    return df

# Helper function to safely convert DataFrames to dictionaries
def safe_dataframe_to_dict(df):
    """
    Safely convert DataFrame to list of dictionaries with proper type handling.
    
    Args:
        df: pandas DataFrame to convert
    
    Returns:
        List of dictionaries
    """
    if df is None or len(df) == 0:
        return []
    
    try:
        # First attempt: convert directly to dict
        records = df.to_dict(orient="records")
        
        # Validate each record
        clean_records = []
        for record in records:
            clean_record = {}
            for key, value in record.items():
                try:
                    # Check if value is JSON serializable
                    import json
                    json.dumps({key: value})
                    clean_record[key] = value
                except (TypeError, OverflowError):
                    # If not serializable, convert to string
                    print(f"Converting non-serializable value in column '{key}' to string: {type(value)}")
                    clean_record[key] = str(value)
            clean_records.append(clean_record)
        
        return clean_records
    except Exception as e:
        print(f"Error in safe_dataframe_to_dict: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Fallback: convert row by row
        clean_records = []
        for _, row in df.iterrows():
            clean_record = {}
            for key, value in row.items():
                try:
                    # Try to use the value as is
                    if pd.isna(value):
                        if key in ['enrollmentCount', 'total_clinical_trials', 'total_fda_data']:
                            clean_record[key] = 0
                        elif key in ['hasExpandedAccess', 'HasResults', 'healthyVolunteers', 'is_original_packager']:
                            clean_record[key] = False
                        else:
                            clean_record[key] = ""
                    elif isinstance(value, float) and key in ['enrollmentCount', 'total_clinical_trials', 'total_fda_data']:
                        clean_record[key] = int(value)
                    else:
                        clean_record[key] = value
                except Exception:
                    # If all else fails, convert to string
                    clean_record[key] = str(value)
            clean_records.append(clean_record)
        
        return clean_records

@search_router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for clinical trials and FDA data based on the provided keyword and domain.
    
    Args:
        request: Search request containing keyword and domain.
        current_user: The authenticated user.
        
    Returns:
        SearchResponse: Clinical trials and FDA data matching the search criteria.
        
    Raises:
        HTTPException: If the search fails.
    """
    # Initialize empty results
    clinical_trials_data = []
    fda_data = []
    clinical_trials_error = None
    fda_error = None
    
    try:
        print(f"Search request received: keyword='{request.keyword}', domain='{request.searchType}'")
        print(f"User: {current_user.email}")
        
        # Fetch clinical trials data
        try:
            print(f"Fetching clinical trials data for keyword: '{request.keyword}'")
            clinical_trials_df = get_clinical_trials_data(request.keyword)
            
            if clinical_trials_df is not None and not clinical_trials_df.empty:
                print(f"Clinical trials data fetched: {len(clinical_trials_df)} records")
                
                # Print DataFrame info for debugging
                print("Clinical trials DataFrame info:")
                clinical_trials_df.info()
                
                # Check for problematic columns
                for col in clinical_trials_df.columns:
                    if clinical_trials_df[col].dtype == 'float64':
                        print(f"Potential problematic column (float): {col}")
                        print(f"Sample values: {clinical_trials_df[col].head()}")
                
                # Convert clinical trials DataFrame to dictionaries with proper type handling
                try:
                    # Apply safe type conversion
                    clinical_trials_df = safe_convert_types(clinical_trials_df)
                    
                    # Convert to dictionaries
                    clinical_trials_data = safe_dataframe_to_dict(clinical_trials_df)
                    print(f"Converted {len(clinical_trials_data)} clinical trials records to dictionaries")
                except Exception as e:
                    print(f"Error converting clinical trials DataFrame to dictionaries: {str(e)}")
                    clinical_trials_error = f"Error processing clinical trials data: {str(e)}"
                    clinical_trials_data = []
            else:
                print("No clinical trials data found or empty DataFrame returned")
                clinical_trials_data = []
        except Exception as e:
            import traceback
            print(f"Error fetching clinical trials data: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            clinical_trials_error = f"Error fetching clinical trials data: {str(e)}"
            clinical_trials_data = []
        
        # Fetch FDA data
        try:
            print(f"Fetching FDA data for keyword: '{request.keyword}', domain: '{request.searchType}'")
            fda_df = Open_FDA.open_fda_main(request.keyword, request.searchType)
            
            if fda_df is not None and not fda_df.empty:
                print(f"FDA data fetched: {len(fda_df)} records")
                
                # Print DataFrame info for debugging
                print("FDA DataFrame info:")
                fda_df.info()
                
                # Convert FDA DataFrame to dictionaries with proper type handling
                try:
                    # Apply safe type conversion
                    fda_df = safe_convert_types(fda_df)
                    
                    # Convert to dictionaries
                    fda_data = safe_dataframe_to_dict(fda_df)
                    print(f"Converted {len(fda_data)} FDA records to dictionaries")
                except Exception as e:
                    print(f"Error converting FDA DataFrame to dictionaries: {str(e)}")
                    fda_error = f"Error processing FDA data: {str(e)}"
                    fda_data = []
            else:
                print("No FDA data found or empty DataFrame returned")
                fda_data = []
        except Exception as e:
            import traceback
            print(f"Error fetching FDA data: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            fda_error = f"Error fetching FDA data: {str(e)}"
            fda_data = []
        
        # Check if both data sources failed
        if clinical_trials_error and fda_error:
            error_message = f"Search failed: {clinical_trials_error}; {fda_error}"
            print(error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )
        
        # Create response
        response = SearchResponse(
            clinical_trials=clinical_trials_data,
            fda_data=fda_data,
            total_clinical_trials=len(clinical_trials_data),
            total_fda_data=len(fda_data)
        )
        
        print(f"Search completed successfully: {len(clinical_trials_data)} clinical trials, {len(fda_data)} FDA records")
        return response
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_message = f"Unexpected error during search: {str(e)}"
        print(error_message)
        print(f"Error trace: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )
