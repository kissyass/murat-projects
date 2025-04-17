import requests
from requests.auth import HTTPBasicAuth

def log_into_wordpress(domain, username, password):
    if not domain.startswith("https://"):
        domain = "https://" + domain
    
    # Remove trailing slash if present
    domain = domain.rstrip("/")

    # Construct the REST API endpoint
    api_endpoint = f"{domain}/wp-json/wp/v2"

    try:
        response = requests.get(api_endpoint, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            return True, "Logged into Wordpress Successfully"
        else:
            return False, "Error: Failed to Log into Successfully"
    except Exception as e:
        return False, str(e)
