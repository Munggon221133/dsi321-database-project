import streamlit as st
import psycopg2
import toml
import pandas as pd
import plotly.express as px

def load_dataframes():
    # Load secrets from the secrets.toml file
    secrets = toml.load(".streamlit/secrets.toml")

    # Extract PostgreSQL connection details
    host = secrets["postgres"]["host"]
    port = int(secrets["postgres"]["port"])
    dbname = secrets["postgres"]["dbname"]
    user = secrets["postgres"]["user"]
    password = secrets["postgres"]["password"]

    # Establish a connection to the database
    conn = psycopg2.connect(dbname=dbname,
                            user=user,
                            password=password,
                            host=host,
                            port=port
                            )

    # Get a list of all table names in the database
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
    table_rows = cursor.fetchall()
    table_names = [row[0] for row in table_rows]

    # Load all tables into DataFrames
    dataframes = {}
    for table_name in table_names:
        query = f"SELECT * FROM {table_name};"
        dataframes[table_name] = pd.read_sql_query(query, conn)
        
        # Convert JSON columns to strings
        json_columns = ['language_skills', 'workshop', 'work_exp', 'award']
        for column in json_columns:
            if column in dataframes[table_name].columns:
                dataframes[table_name][column] = dataframes[table_name][column].astype(str)

    return conn, dataframes, table_names

def app():
    st.title("Visualization")
    st.markdown("---")

    # Load dataframes and establish connection here
    conn, dataframes, table_names = load_dataframes()

    join_query_company = f"""SELECT
                                c.student_id,
                                c.company_id,
                                cc.company_name,
                                s.finish_year
                            FROM
                                cooperative_student_questionnaire AS c
                            INNER JOIN
                                company AS cc ON cc.company_id = c.company_id
                            INNER JOIN
                                student_final_project AS s ON s.student_id = c.student_id;
                            """
    # Execute the join query
    with conn.cursor() as cursor:
        cursor.execute(join_query_company)
        intern_info = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    # Create a dropdown for selecting a year
    years = sorted(intern_info['finish_year'].unique(), reverse=True)
    selected_year = st.selectbox("Select Year", years)

    # Filter data based on the selected year
    filtered_data = intern_info[intern_info['finish_year'] == selected_year]

    # Create a DataFrame with company name counts
    company_counts = filtered_data['company_name'].value_counts().reset_index()
    company_counts.columns = ['company_name', 'count']

    # Create bar chart
    fig = px.bar(company_counts, x='company_name', y='count',
                 title=f'Number of Interns per Company for the Year {selected_year}',
                 labels={'count': 'Number of Interns', 'company_name': 'Company Name'})

    # Update the layout to rotate the x-axis labels for better readability
    fig.update_layout(xaxis_tickangle=-45)

    # Display bar chart in Streamlit
    st.plotly_chart(fig)
    st.markdown("---")

    
# Run the app
if __name__ == '__main__':
    app()