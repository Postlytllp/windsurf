class Filter_Parser_Data:
    """A class for parsing and cleaning data from the ClinicalTrials.gov and Open FDA APIs."""

    @staticmethod
    def filter_parser_clinicaltrials(list_of_dicts):
        """
        Recursively parse and clean nested dictionaries in the given list of dictionaries.

        Args:
            list_of_dicts (list): A list of dictionaries containing nested dictionaries.

        Returns:
            None
        """
        for d in list_of_dicts:
            for key, value in d.items():
                if isinstance(value, dict):
                    Filter_Parser_Data.filter_parser_clinicaltrials(value)
                elif isinstance(value, list):
                    if all(isinstance(subdict, dict) for subdict in value):
                        d[key] = "/".join(
                            "/".join(str(v) for v in subdict.values())
                            for subdict in value
                        )
                    else:
                        d[key] = "/".join(str(v) for v in value)
                else:
                    d[key] = value

    @staticmethod
    def clean_openfda_value(openfda_value):
        """
        Clean and format the given Open FDA value by removing duplicates and joining the values into a single string.

        Args:
            openfda_value (list): A list of values to clean and format.

        Returns:
            str: A cleaned and formatted string of values.
        """
        clean_list = list(set(openfda_value))
        clean_list = [str(item) for item in clean_list]
        temp_values = "/".join(clean_list)
        return temp_values
