"""
Test script for clinical trials and FDA data modules.
This script directly tests the data fetching functions to isolate any issues.
"""
import sys
import pandas as pd
from clinical_trials_module import get_clinical_trials_data
from openfda import Open_FDA

def test_clinical_trials(keyword):
    """Test the clinical trials data fetching function."""
    print(f"\n=== Testing Clinical Trials Module with keyword: '{keyword}' ===")
    try:
        print("Fetching clinical trials data...")
        data = get_clinical_trials_data(keyword)
        print(f"Success! Retrieved {len(data)} records")
        
        if len(data) > 0:
            print("\nSample data (first 2 rows):")
            print(data.head(2).to_string())
            
            print("\nColumns:")
            print(data.columns.tolist())
            
            return data
        else:
            print("No data found for this keyword")
            return None
    except Exception as e:
        print(f"Error fetching clinical trials data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def test_fda_data(keyword, domain):
    """Test the FDA data fetching function."""
    print(f"\n=== Testing FDA Module with keyword: '{keyword}', domain: '{domain}' ===")
    try:
        print("Fetching FDA data...")
        data = Open_FDA.open_fda_main(user_keyword=keyword, domain=domain)
        
        if data is not None:
            print(f"Success! Retrieved {len(data)} records")
            
            if len(data) > 0:
                print("\nSample data (first 2 rows):")
                print(data.head(2).to_string())
                
                print("\nColumns:")
                print(data.columns.tolist())
            else:
                print("No data found for this keyword and domain")
            
            return data
        else:
            print("No data returned (None)")
            return None
    except Exception as e:
        print(f"Error fetching FDA data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def test_data_conversion(df, source):
    """Test converting DataFrame to dictionary format."""
    print(f"\n=== Testing Data Conversion for {source} data ===")
    try:
        if df is None or len(df) == 0:
            print("No data to convert")
            return None
        
        print(f"Converting {len(df)} records to dictionary format...")
        data_dict = df.fillna("").to_dict(orient="records")
        print(f"Success! Converted to {len(data_dict)} dictionary records")
        
        if len(data_dict) > 0:
            print("\nSample converted data (first record keys):")
            print(list(data_dict[0].keys())[:10])  # Show first 10 keys
            
            # Check for any very large values that might cause issues
            large_fields = []
            for key, value in data_dict[0].items():
                if isinstance(value, str) and len(value) > 1000:
                    large_fields.append((key, len(value)))
            
            if large_fields:
                print("\nLarge fields that might cause issues:")
                for field, size in large_fields:
                    print(f"  - {field}: {size} characters")
            
            return data_dict
        else:
            print("No dictionary records created")
            return None
    except Exception as e:
        print(f"Error converting data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Test with a single keyword for more focused testing
    keyword = "cosentyx"
    print(f"Testing with keyword: '{keyword}'")
    
    try:
        # Test clinical trials data
        ct_data = test_clinical_trials(keyword)
        
        # Test data conversion for clinical trials
        if ct_data is not None:
            test_data_conversion(ct_data, "clinical trials")
        
        # Test FDA data with disease domain
        domain = "disease"
        fda_data = test_fda_data(keyword, domain)
        
        # Test data conversion for FDA data
        if fda_data is not None:
            test_data_conversion(fda_data, f"FDA ({domain})")
    except Exception as e:
        print(f"Unhandled exception in main test flow: {str(e)}")
        import traceback
        print(traceback.format_exc())
