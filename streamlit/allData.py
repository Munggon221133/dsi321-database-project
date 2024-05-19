import streamlit as st
import pandas as pd
import psycopg2
import toml
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
        json_columns = ['language_skills', 'workshop', 'work_exp', 'award', 'middle_school_end_year', 'high_school_end_year', 'bachelor_end_year']
        for column in json_columns:
            if column in dataframes[table_name].columns:
                dataframes[table_name][column] = dataframes[table_name][column].astype(str)
    
    return conn, dataframes, table_names

def app():
    st.title("All Data")
    
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

    # Download
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
    st.subheader("Join Tables")

    selected_tables = st.multiselect("Select tables to join (up to 3):", table_names, [], key="selected_tables")

    # Button to run the join query
    if st.button("Join Tables"):
        if len(selected_tables) < 2:
            st.warning("Please select at least two tables to join.")
        elif len(selected_tables) > 3:
            st.warning("Please select up to three tables to join.")
        elif set(selected_tables) == {'student_info', 'professor'}:
            join_query = f"""SELECT s.student_id, s.first_name, s.last_name, s.academic_year, s.tel, s.email, s.gpax, 
                                    p.professor_id, p.professor_firstname, p.professor_lastname, p.email AS professor_email
                            FROM student_info AS s
                            INNER JOIN professor AS p ON s.professor_id = p.professor_id;"""

            try:
                # Execute the join query
                with conn.cursor() as cursor:
                    cursor.execute(join_query)
                    join_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                st.write(join_result)
            except psycopg2.errors.UndefinedColumn as e:
                st.error(f"An error occurred: {e}")
        elif set(selected_tables) == {'student_address', 'address_info'}:
            join_query = f"""SELECT s.student_id, s.address, a.address_id, a.sub_district, a.district, a.province, a.post_no
                             FROM student_address AS s
                             INNER JOIN address_info AS a ON s.address_id = a.address_id;"""

            try:
                # Execute the join query
                with conn.cursor() as cursor:
                    cursor.execute(join_query)
                    join_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                st.write(join_result)
            except psycopg2.errors.UndefinedColumn as e:
                st.error(f"An error occurred: {e}")
        elif set(selected_tables) == {'student_info', 'student_address', 'address_info'}:
            join_query = f"""SELECT 
                                ss.student_id, 
                                ss.first_name, 
                                ss.last_name, 
                                ss.academic_year, 
                                ss.tel, 
                                ss.email, 
                                sa.address, 
                                a.address_id, 
                                a.sub_district, 
                                a.district, 
                                a.province, 
                                a.post_no
                                FROM student_info AS ss
                                INNER JOIN student_address AS sa ON ss.student_id = sa.student_id
                                INNER JOIN address_info AS a ON sa.address_id = a.address_id
                                """

            try:
                # Execute the join query
                with conn.cursor() as cursor:
                    cursor.execute(join_query)
                    join_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                st.write(join_result)
            except psycopg2.errors.UndefinedColumn as e:
                st.error(f"An error occurred: {e}")
        elif set(selected_tables) == {'student_info', 'student_emergency_contact'}:
            join_query = f"""SELECT
                                si.student_id,
                                si.first_name AS student_first_name,
                                si.last_name AS student_last_name,
                                si.academic_year,
                                si.tel AS student_tel,
                                si.email AS student_email,
                                sec.first_name AS emergency_contact_first_name,
                                sec.last_name AS emergency_contact_last_name,
                                sec.address_id AS emergency_contact_address_id,
                                sec.address AS emergency_contact_address,
                                sec.relationship AS emergency_contact_relationship,
                                sec.workplace AS emergency_contact_workplace,
                                sec.tel AS emergency_contact_tel,
                                sec.fax AS emergency_contact_fax
                             FROM
                                student_info AS si
                             INNER JOIN
                                student_emergency_contact AS sec ON si.student_id = sec.student_id;"""

            try:
                # Execute the join query
                with conn.cursor() as cursor:
                    cursor.execute(join_query)
                    join_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                st.write(join_result)
            except psycopg2.errors.UndefinedColumn as e:
                st.error(f"An error occurred: {e}")
        elif set(selected_tables) == {'student_info', 'student_skills'}:
            join_query = f"""SELECT
                                si.student_id,
                                si.first_name AS student_first_name,
                                si.last_name AS student_last_name,
                                si.academic_year,
                                si.tel AS student_tel,
                                si.email AS student_email,
                                sk.technical_skills,
                                sk.sp_muskills,
                                sk.other_skills,
                                sk.language_skills,
                                sk.workshop,
                                sk.work_exp,
                                sk.award
                             FROM
                                student_info AS si
                             INNER JOIN
                                student_skills AS sk ON si.student_id = sk.student_id;"""
            try:
                # Execute the join query
                with conn.cursor() as cursor:
                    cursor.execute(join_query)
                    join_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

                # Convert JSON columns to strings
                json_columns = ['language_skills', 'workshop', 'work_exp', 'award']
                for column in json_columns:
                    if column in join_result.columns:
                        join_result[column] = join_result[column].astype(str)

                # Display the result in Streamlit
                st.write(join_result)

            except psycopg2.errors.UndefinedColumn as e:
                st.error(f"An error occurred: {e}")
        elif set(selected_tables) == {'student_info', 'cooperative_student_questionnaire'}:
            join_query = f"""SELECT
                                si.student_id,
                                si.first_name AS student_first_name,
                                si.last_name AS student_last_name,
                                si.academic_year,
                                si.tel AS student_tel,
                                si.email AS student_email,
                                c.company_id,
                                c.rvfirst_name,
                                c.rvlast_name,
                                c.position,
                                c.quantity_work,
                                c.quality_work,
                                c.acad_ability,
                                c.ability_apply,
                                c.prac_ability,
                                c.judge_decision,
                                c.organ_planning,
                                c.commu_skills,
                                c.foreign_cultural,
                                c.suitability_job,
                                c.respon_depen,
                                c.interest_work,
                                c.initiative,
                                c.supervision_response,
                                c.personality,
                                c.interpersonal_skills,
                                c.discipline_adapt,
                                c.ethics_morality,
                                c.strength,
                                c.need_improvement,
                                c.further_offer,
                                c.comments
                            FROM
                                student_info AS si
                            INNER JOIN
                                cooperative_student_questionnaire AS c ON si.student_id = c.student_id;"""
            try:
                # Execute the join query
                with conn.cursor() as cursor:
                    cursor.execute(join_query)
                    join_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                st.write(join_result)
            except psycopg2.errors.UndefinedColumn as e:
                st.error(f"An error occurred: {e}")
        elif set(selected_tables) == {'cooperative_student_questionnaire', 'company'}:
            join_query = f"""SELECT
                                c.student_id,
                                c.company_id,
                                cc.company_name,
                                cc.province,
                                c.rvfirst_name,
                                c.rvlast_name,
                                c.position,
                                c.quantity_work,
                                c.quality_work,
                                c.acad_ability,
                                c.ability_apply,
                                c.prac_ability,
                                c.judge_decision,
                                c.organ_planning,
                                c.commu_skills,
                                c.foreign_cultural,
                                c.suitability_job,
                                c.respon_depen,
                                c.interest_work,
                                c.initiative,
                                c.supervision_response,
                                c.personality,
                                c.interpersonal_skills,
                                c.discipline_adapt,
                                c.ethics_morality,
                                c.strength,
                                c.need_improvement,
                                c.further_offer,
                                c.comments
                            FROM
                                cooperative_student_questionnaire AS c
                            INNER JOIN
                                company AS cc ON cc.company_id = c.company_id;
                            """
            try:
                # Execute the join query
                with conn.cursor() as cursor:
                    cursor.execute(join_query)
                    join_result = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                st.write(join_result)
            except psycopg2.errors.UndefinedColumn as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("don't have any query")
        join_query = None
if __name__ == "__main__":
    app()
