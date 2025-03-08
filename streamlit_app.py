import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import datetime

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# --- Sidebar Configuration ---
st.sidebar.title("Google Search Console Setup")
credentials_json = st.sidebar.text_area("Paste your service account credentials JSON here:")

if credentials_json:
    try:
        creds = service_account.Credentials.from_service_account_info(
            eval(credentials_json), scopes=SCOPES
        )
        service = build('webmasters', 'v3', credentials=creds)
        site_list = service.sites().list().execute()

        if 'siteEntry' in site_list:
            sites = [site['siteUrl'] for site in site_list['siteEntry']]
            selected_site = st.sidebar.selectbox("Select your website:", sites)
        else:
            st.sidebar.error("No websites found in your Search Console account.")
            selected_site = None

    except Exception as e:
        st.sidebar.error(f"Error loading credentials: {e}")
        selected_site = None
else:
    selected_site = None

# --- Main App ---
st.title("SEO Ranking Tool")

if selected_site:
    url_to_check = st.text_input("Enter URL to check ranking for (relative to your domain):")

    if st.button("Get Ranking Data"):
        if url_to_check:
            try:
                today = datetime.date.today()
                start_date = today - datetime.timedelta(days=28)  # Last 28 days

                request = {
                    'startDate': start_date.strftime('%Y-%m-%d'),
                    'endDate': today.strftime('%Y-%m-%d'),
                    'dimensions': ['page'],
                    'rowLimit': 1000,
                    'aggregationType': 'byPage',
                    'searchType': 'web',
                    'dataState': 'final'
                }

                results = service.searchanalytics().query(
                    siteUrl=selected_site, body=request).execute()

                if 'rows' in results:
                    data = []
                    for row in results['rows']:
                        if url_to_check in row['keys'][0]:
                            data.append({
                                'Page': row['keys'][0],
                                'Clicks': row['clicks'],
                                'Impressions': row['impressions'],
                                'CTR': row['ctr'],
                                'Position': row['position']
                            })

                    if data:
                        df = pd.DataFrame(data)
                        st.dataframe(df)
                        st.write("Average Position:", df['Position'].mean())
                    else:
                        st.write("No data found for the specified URL within the last 28 days.")
                else:
                    st.write("No data found in Search Console.")

            except Exception as e:
                st.error(f"Error fetching data: {e}")

        else:
            st.warning("Please enter a URL.")

else:
    st.warning("Please configure your Google Search Console credentials in the sidebar.")
