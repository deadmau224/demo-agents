import requests


def get_access_token(issuer_url, client_id, client_secret):
    """
    Retrieves a bearer token from the specified token URL using client credentials.
    Args:
        issuer_url (str): The URL to request the bearer token from.
        client_id (str): The client ID for authentication.
        client_secret (str): The client secret for authentication.
    Returns:
        str: The bearer token if the request is successful, None otherwise.
    Raises:
        Exception: If there is an issue with the HTTP request.
    """
    # Prepare the payload for the POST request
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'mlops.deere.com/model-deployments.llm.region-restricted-invocations'
    }
    
    headers = {'Content-type': 'application/x-www-form-urlencoded'}

    try:
        issuer_url = f"{issuer_url}/v1/token"
        response = requests.post(issuer_url, data=payload, headers=headers)
        # Raise an HTTPError for bad responses (4xx and 5xx)
        response.raise_for_status()

        # Parse the JSON response to get the access token
        token_info = response.json()
        bearer_token = token_info.get('access_token')
        return bearer_token

    except Exception as err:
        print(f'An error occurred: {err}')

    return None
