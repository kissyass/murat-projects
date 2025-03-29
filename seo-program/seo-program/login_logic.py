import requests
from requests.auth import HTTPBasicAuth
from translations import load_translations

def log_into_wordpress(domain, username, password, language):
    translations = load_translations(language)

    if not domain.startswith("https://"):
        domain = "https://" + domain
    
    # Remove trailing slash if present
    domain = domain.rstrip("/")

    # Construct the REST API endpoint
    api_endpoint = f"{domain}/wp-json/wp/v2"

    try:
        print(api_endpoint)
        response = requests.get(api_endpoint, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            return True, translations["login_success"]
        else:
            print(f"{response.status_code} - {response.text}")
            return False, f"{translations['error']}: {response.status_code} - {response.text}"
    except Exception as e:
        print(str(e))
        return False, str(e)
