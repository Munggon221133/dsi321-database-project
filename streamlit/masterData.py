import streamlit as st
import psycopg2
import toml
import pandas as pd
from io import StringIO

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

    # Load all tables into DataFrames
    table_names = [ 
        "company",  
        "student_info",
        "professor",
        "officer"
                ]
    
    dataframes = {}
    for table_name in table_names:
        query = f"SELECT * FROM {table_name};"
        dataframes[table_name] = pd.read_sql_query(query, conn)

    return conn, dataframes, table_names

def app():
    st.title("Master Data")
    
    # Load dataframes and establish connection here
    conn, dataframes, table_names = load_dataframes()
    
    # Dropdown table
    st.markdown("---")
    selected_table = st.selectbox("Select a table to show:", list(dataframes.keys()))

    # Show selected table
    st.subheader(f"Table: {selected_table}")
    st.write(dataframes[selected_table])

    # Show Info button
    if st.button("Show Info"):
        st.write(f"{selected_table} Info:")
        with StringIO() as buffer:
            dataframes[selected_table].info(buf=buffer)
            info_str = buffer.getvalue()
        st.text(info_str)

    # Download dropdown
    st.subheader(f"Download📥: {selected_table}")
    download_format = st.radio("Select a format:", ["CSV", "XML", "JSON"], key="download_format_custom")

    if download_format == "CSV":
        csv_data = dataframes[selected_table].to_csv(index=False, encoding='utf-8')
        st.download_button(label="Download CSV", data=csv_data, file_name=f"{selected_table}.csv", mime='text/csv')
    elif download_format == "XML":
        xml_data = dataframes[selected_table].to_xml(index=False, encoding='utf-8')
        st.download_button(label="Download XML", data=xml_data, file_name=f"{selected_table}.xml", mime='text/xml')
    elif download_format == "JSON":
        json_data = dataframes[selected_table].to_json()
        st.download_button(label="Download JSON", data=json_data, file_name=f"{selected_table}.json", mime='application/json')

    # SQL query input
    st.markdown("---")
    st.subheader("Custom SQL Query")
    sql_query = st.text_input("Enter your SQL query:")

    run_query = st.button("Run Query")

    if "custom_df" not in st.session_state or run_query:
        try:
            # Establish a new connection for each query
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                custom_df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

                # Convert JSON columns to strings
                json_columns = ['language_skills', 'workshop', 'work_exp', 'award']
                for column in json_columns:
                    if column in custom_df.columns:
                        custom_df[column] = custom_df[column].astype(str)

                st.session_state.custom_df = custom_df
        except Exception as e:
            st.error(f"An error occurred: {e}")

    # Show custom query result
    if "custom_df" in st.session_state:
        st.subheader("Custom Query Result")
        st.write(st.session_state.custom_df)

        # Download custom query result
        st.subheader("Download📥: Custom Query Result")
        download_format_custom = st.radio("Select a format:", ["CSV", "XML", "JSON"])
        file_name_custom = st.text_input("Enter the file name:")
        
        if st.button("Set file name"):
            if download_format_custom == "CSV":
                csv_data_custom = st.session_state.custom_df.to_csv(index=False, encoding='utf-8')
                st.download_button(label=f"Download {file_name_custom}.csv", data=csv_data_custom, file_name=f"{file_name_custom}.csv", mime='text/csv')
            elif download_format_custom == "XML":
                xml_data_custom = st.session_state.custom_df.to_xml(index=False, encoding='utf-8')
                st.download_button(label=f"Download {file_name_custom}.xml", data=xml_data_custom, file_name=f"{file_name_custom}.xml", mime='text/xml')
            elif download_format_custom == "JSON":
                json_data_custom = st.session_state.custom_df.to_json()
                st.download_button(label=f"Download {file_name_custom}.json", data=json_data_custom, file_name=f"{file_name_custom}.json", mime='application/json')
    st.markdown("---")

if __name__ == "__main__":
    app()
