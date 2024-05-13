import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# Web Crawler Functions
# Function to scrape data
@st.cache_data()  # Updated to use the built-in Streamlit caching
def scrape_data_new(pages=10):
    base_url = 'https://dtm.iom.int/reports'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    reports_data = []

    for page in range(pages):
        if page == 0:
            url = base_url
        else:
            url = f'{base_url}?page={page}'

        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        dtm_soup = BeautifulSoup(response.content, 'html.parser')
        dtm_reports = dtm_soup.find_all('div', class_='report-item1')

        for report in dtm_reports:
            title = report.find('a', class_='title').text.strip()
            report_html = str(report)
            links = re.findall(r'href="(/reports/[^"]+)"', report_html)
            report_link = f'https://dtm.iom.int{links[0]}' if links else None
            date_info = report.find('div', class_='date').text.split('·')
            date = pd.to_datetime(date_info[0].strip(), errors='coerce', format='%b %d %Y')
            region = date_info[1].strip() if len(date_info) > 1 else 'Unknown'
            country_name = date_info[2].strip() if len(date_info) > 2 else 'Unknown'
            report_type = date_info[3].strip() if len(date_info) > 3 else 'Unknown'
            summary_content = report.find('div', class_='content').text.strip()

            reports_data.append({
                'Title': title,
                'Summary': summary_content,
                'Link': report_link,
                'Published Date': date,
                'Country Name': country_name,
                'Region': region,
                'Report Type': report_type
            })

    return pd.DataFrame(reports_data)


# Streamlit app setup

# Streamlit app setup
def app():
    st.set_page_config(page_title='DTM Report Dashboard', page_icon='📊', layout="centered")
    df = scrape_data_new(pages=10)  # Adjust the number of pages as needed
    now = datetime.now()
    least_date = df['Published Date'].min().strftime('%Y-%m-%d') if not df['Published Date'].isnull().all() else "No Dates Available"
    last_date = df['Published Date'].max().strftime('%Y-%m-%d') if not df['Published Date'].isnull().all() else "No Dates Available"

    st.image('https://raw.githubusercontent.com/Otomisin/c-practise/main/DTM-Dash/IOMlogo.png', width=70)
    st.title('DTM Report Dashboard')
    st.caption(f'Reports updated as of: {now.strftime("%Y-%m-%d")}')

    # Total number of reports crawled
    total_report_crawled = len(df)

    # Date range for the overall crawled reports
    st.write(f"**Crawled Reports Date Range:** {last_date} - {least_date}")

    # Filter reports published in the last 48 hours
    two_days_ago = now - timedelta(days=2)
    recent_reports = df[df['Published Date'] >= two_days_ago]
    
    # Total number of reports published in the last 48 hours
    total_recent_reports = len(recent_reports)

    # Date range for reports published in the last 48 hours
    least_recent_date = recent_reports['Published Date'].min().strftime('%Y-%m-%d') if not recent_reports['Published Date'].isnull().all() else "No Dates Available"
    last_recent_date = recent_reports['Published Date'].max().strftime('%Y-%m-%d') if not recent_reports['Published Date'].isnull().all() else "No Dates Available"
    
    st.write(f"**Reports in the last 48 hours:** {last_recent_date} - {least_recent_date} | **{total_recent_reports} Reports**")

    # st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.markdown("### DATA POINT - TOOLS")
        with st.expander("**About this App**"):
            st.write("""
                This dashboard provides an interactive way to explore reports published by IOM DTM. 
                Select filters from the sidebar to customize the display. You can download data as CSV.
        
                For more information, visit [DTM](https://dtm.iom.int/).
        
                ### Contact
                For queries, please contact us at [here](https://dtm.iom.int/contact).
                """)
        st.markdown("---")

        if st.sidebar.button('Reload Data'):
            st.experimental_rerun()

        # Date Range Filter
        st.sidebar.markdown("### Date Range Filter")
        min_date = df['Published Date'].min()
        max_date = df['Published Date'].max()
        start_date = st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
        end_date = st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

        # Convert start_date and end_date to datetime objects
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())

        # Country Filter
        country_options = df['Country Name'].unique()
        all_countries = st.sidebar.checkbox("Select All Countries", True)
        if all_countries:
            selected_countries = st.sidebar.multiselect('Select Country:', options=country_options, default=country_options)
        else:
            selected_countries = st.sidebar.multiselect('Select Country:', options=country_options)

    # Filter the data based on date range and selected countries
    filtered_data = df[(df['Published Date'] >= start_date) & (df['Published Date'] <= end_date) & (df['Country Name'].isin(selected_countries))]

    # Display counts based on filters
    st.write(f"**Filtered Reports Count:** {len(filtered_data)}")
    st.markdown("---")

    for index, row in filtered_data.iterrows():
        st.markdown(f"### {row['Title']}")     
        if pd.isna(row['Published Date']):
            formatted_date = "Date Not Available"
        else:
            formatted_date = row['Published Date'].strftime('%d-%b-%Y')
        
        st.markdown(f"**{formatted_date} | {row['Country Name']} | {row['Report Type']}**")
        st.write(row['Summary'])
        st.markdown(f"[Read More]({row['Link']})", unsafe_allow_html=True)    
    
    # Download Data Button
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    csv_filename = f"DTM_Reports_{start_str}-{end_str}.csv"
    csv = filtered_data.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    # st.markdown("### Download Data")
    st.sidebar.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name=csv_filename,
        mime='text/csv',
    )

if __name__ == '__main__':
    app()
