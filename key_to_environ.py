import os

def load_keys_to_env(file_path):
    """
    Load keys from a file and set them as environment variables.
    Each line should be in the format: KEY= "value" or KEY="value"
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as file:
        for line in file:
            # Remove leading/trailing spaces and newlines
            line = line.strip()
            if line and '=' in line:  # Ensure the line has a key-value pair
                # Split the line into key and value
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().strip('"\'')
                    
                    # Set as environment variable
                    os.environ[key] = value
                    print(f"Set environment variable: {key}")

if __name__ == "__main__":
    # Path to the API_KEYS.txt file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "API_KEYS.txt")
    
    # Load the keys
    try:
        load_keys_to_env(file_path)
        print("API keys loaded successfully!")
        
        # Verify the OpenAI API key was loaded
        if "OPENAI_API_KEY" in os.environ:
            print(f"OpenAI API key is set: {os.environ['OPENAI_API_KEY'][:10]}...")
        else:
            print("Warning: OpenAI API key was not found in the file!")
    except Exception as e:
        print(f"Error loading API keys: {str(e)}")
