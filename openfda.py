import requests
import re
import pandas as pd
from filter_parser import Filter_Parser_Data


class Open_FDA:
    """A class for fetching and processing data from the Open FDA API."""

    @staticmethod
    def total_rows_in_openfda(user_keyword, keyword_domain, timeout=5, max_retries=3):
        """
        Fetch the total number of results matching the given keyword and domain from the Open FDA API.

        Args:
            user_keyword (str): The keyword to search for in the Open FDA API.
            keyword_domain (str): The domain to search within (e.g., "disease" or "drug").
            timeout (int, optional): The maximum number of seconds to wait for the request to complete. Defaults to 5.
            max_retries (int, optional): The maximum number of times to retry the request if it fails. Defaults to 3.

        Returns:
            int: The total number of results found, or None if the request fails.
        """
        api_url = Open_FDA.open_fda_url_selection(user_keyword, keyword_domain)
        for retry in range(max_retries):
            try:
                timeout_occurred = False
                response = requests.get(api_url, timeout=timeout)
                response.raise_for_status()
                if response.status_code == 200:
                    data = response.json()
                    return data["meta"]["results"]["total"]
            except requests.exceptions.Timeout:
                timeout_occurred = True
                print(
                    f"Request timed out (attempt {retry+1}/{max_retries}). Retrying..."
                )
            except requests.exceptions.RequestException as e:
                print("Error:", e)
                break

            if not timeout_occurred:
                break

        return None

    @staticmethod
    def open_fda_url_selection(user_keyword, keyword_domain, limit=1):
        """
        Generate the API URL for fetching data from the Open FDA API based on the given keyword and domain.

        Args:
            user_keyword (str): The keyword to search for in the Open FDA API.
            keyword_domain (str): The domain to search within (e.g., "disease" or "drug").
            limit (int, optional): The maximum number of results to return. Defaults to 1.

        Returns:
            str: The generated API URL.
        """
        if keyword_domain == "disease":
            open_fda_api_url = f'https://api.fda.gov/drug/label.json?search=indications_and_usage:"{user_keyword}"&limit={limit}'
        elif keyword_domain == "drug":
            open_fda_api_url = f'https://api.fda.gov/drug/label.json?search=brand_name.exact"{user_keyword}"+generic_name.exact"{user_keyword}"&limit={limit}'
        return open_fda_api_url

    @staticmethod
    def open_fda_data(user_keyword, keyword_domain, limit, timeout=5, max_retries=3):
        """
        Fetch data from the Open FDA API for the given keyword, domain, and limit, and return a list of dictionaries containing the extracted data.

        Args:
            user_keyword (str): The keyword to search for in the Open FDA API.
            keyword_domain (str): The domain to search within (e.g., "disease" or "drug").
            limit (int): The maximum number of results to return.
            timeout (int, optional): The maximum number of seconds to wait for the request to complete. Defaults to 5.
            max_retries (int, optional): The maximum number of times to retry the request if it fails. Defaults to 3.

        Returns:
            list: A list of dictionaries containing the extracted data, or None if the request fails.
        """
        if limit is not None and limit > 1000:
            limit = 1000

        api_url = Open_FDA.open_fda_url_selection(user_keyword, keyword_domain, limit)
        needed_column_names = {
            'adverse_reactions',
            'application_number',
            'brand_name',
            'clinical_pharmacology',
            'clinical_studies',
            'contraindications',
            'description',
            'dosage_and_administration',
            'drug_interactions',
            'generic_name',
            'how_supplied',
            'indications_and_usage',
            'information_for_patients',
            'is_original_packager',
            'manufacturer_name',
            'mechanism_of_action',
            'pharm_class_cs',
            'pharm_class_epc',
            'pharm_class_moa',
            'pharmacodynamics',
            'pharmacokinetics',
            'product_type',
            'route',
            'substance_name',
            'upc',
            'warnings',
            'warnings_and_cautions',
            'laboratory_tests',
            'drug_interactions',
            'precautions',
            'adverse_reactions'
            }       
        
        for retry in range(max_retries):
            try:
                timeout_occurred = False
                response = requests.get(api_url, timeout=timeout)
                response.raise_for_status()
                if response.status_code == 200:
                    data = response.json()
                    api_data = []
                    for current_data in data["results"]:
                        api_unit_data = {}
                        for key, value in current_data.items():
                            if key == "openfda":
                                for openfda_key, openfda_value in value.items():
                                    if openfda_key in needed_column_names:
                                        api_unit_data[openfda_key] = (
                                            Filter_Parser_Data.clean_openfda_value(
                                                openfda_value
                                            )
                                        )
                            else:
                                if key in needed_column_names:
                                    api_unit_data[key] = (
                                        Filter_Parser_Data.clean_openfda_value(value)
                                    )
                        api_data.append(api_unit_data)
                    return api_data
            except requests.exceptions.Timeout:
                timeout_occurred = True
                print(
                    f"Request timed out (attempt {retry+1}/{max_retries}). Retrying..."
                )
            except requests.exceptions.RequestException as e:
                print("Error:", e)
                break
            if not timeout_occurred:
                break
        return None

    @staticmethod
    def remove_column_headers_from_text(df):
        columns_to_clean = {
            'description': 'Description',
            'clinical_pharmacology': 'Clinical Pharmacology',
            'indications_and_usage': 'Indications and Usage',
            'contraindications': 'Contraindications',
            'information_for_patients': 'Information for Patients',
            'drug_interactions': 'Drug Interactions',
            'adverse_reactions': 'Adverse Reactions',
            'dosage_and_administration': 'Dosage and Administration',
            'how_supplied': 'How Supplied',
            'pharmacokinetics': 'Pharmacokinetics',
            'warnings_and_cautions': 'Warnings and Cautions',
            'clinical_studies': 'Clinical Studies',
            'pharmacodynamics': 'Pharmacodynamic Drug Interaction Studies',
            'precautions' : 'PRECAUTIONS',
            'drug_interactions' : 'Drug Interactions',
            'warnings' : 'WARNINGS',
            'adverse_reactions' : 'ADVERSE REACTIONS'
        }
    
        for column, header in columns_to_clean.items():
            if column in df.columns:
                pattern = r'^((?:\S+\s+){0,2})' + re.escape(header) + r'\s*:?\s*'
                
                def clean_text(text):
                    if isinstance(text, str):
                        match = re.match(pattern, text, flags=re.IGNORECASE)
                        if match:
                            preceding = match.group(1).strip()
                            if len(preceding.split()) <= 2:
                                return text[match.end():].strip()
                    return text  # Return original text if no match or > 2 preceding words
                
                df[column] = df[column].apply(clean_text)
        
        return df

    @staticmethod
    def open_fda_main(user_keyword: str, domain: str):
        """
        Fetch and process data from the Open FDA API for the given keyword and domain, and return a pandas DataFrame containing the extracted data.

        Args:
            user_keyword (str): The keyword to search for in the Open FDA API.
            domain (str): The domain to search within (e.g., "disease" or "drug").

        Returns:
            pd.DataFrame: A pandas DataFrame containing the fetched and processed data, or None if the request fails.
        """
        total_rows = Open_FDA.total_rows_in_openfda(user_keyword, domain)
        open_fda_data = Open_FDA.open_fda_data(user_keyword, domain, total_rows)
        df = pd.DataFrame(open_fda_data)
        if domain == 'drug':
            df = df[
                    df['brand_name'].str.lower().str.contains(user_keyword.lower(), na=False) | 
                    df['generic_name'].str.lower().str.contains(user_keyword.lower(), na=False)
                ]
            
        df = Open_FDA.remove_column_headers_from_text(df)

        df = df.dropna(subset=['brand_name', 'generic_name'], how='all')
        # List the columns you want to move to the front
        columns_to_front = ['brand_name', 'generic_name', 'manufacturer_name', 'application_number', 'indications_and_usage']

        # Reorder the columns by combining the selected columns with the remaining ones
        df = df[columns_to_front + [col for col in df.columns if col not in columns_to_front]]
        
        return df
