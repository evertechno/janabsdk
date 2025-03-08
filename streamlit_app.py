import streamlit as st
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle

# Define the scope of the access we need (Google Search Console API)
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# Authenticate the user using Streamlit secrets
def authenticate_gsc():
    creds = None
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use credentials stored in Streamlit secrets
            client_id = st.secrets["google"]["client_id"]
            client_secret = st.secrets["google"]["client_secret"]
            
            # Set up OAuth flow using Streamlit secrets for credentials
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    }
                },
                SCOPES,
            )
            
            # Use run_local_server() for a headless authentication flow.
            # Google will redirect to a local server running on your machine after the authentication.
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)

    return creds

# Fetch ranking results from Google Search Console
def get_ranking_results(site_url):
    try:
        # Authenticate and build the service
        creds = authenticate_gsc()
        service = build('searchconsole', 'v1', credentials=creds)
        
        # Get the data from the search console API
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                'startDate': '2023-01-01',
                'endDate': '2023-12-31',
                'dimensions': ['query'],
                'rowLimit': 10
            }
        ).execute()

        if 'rows' in response:
            return response['rows']
        else:
            return "No data found for the given site."

    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit UI
def main():
    st.title('SEO Rank Checker using Google Search Console')
    
    # Let the user input a URL
    site_url = st.text_input('Enter the website URL (e.g., https://www.example.com)')

    if site_url:
        if st.button('Get SEO Ranking'):
            # Fetch ranking data
            result = get_ranking_results(site_url)

            if isinstance(result, list):
                st.write(f"SEO Ranking Data for {site_url}:")
                for row in result:
                    st.write(f"Query: {row['keys'][0]}, Clicks: {row['clicks']}, Impressions: {row['impressions']}, CTR: {row['ctr']:.2f}, Position: {row['position']}")
            else:
                st.error(result)

if __name__ == '__main__':
    main()
