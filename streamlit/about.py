import streamlit as st
import pandas as pd

def app():
    # Header and description
    st.title("DSI CO-OP Connect Project")
    st.write("This project is part of DSI324. It involves creating a database for student internships for the major Data Science and Innovation.")
    st.markdown("---")
    st.subheader("Created by:")
    team_data = [
        (6424650015, "ณัฐวุฒิ", "แช่มชื่น"),
        (6424650247, "กมลลักษณ์", "เหว่ารัมย์"),
        (6424650304, "ณัฐธีร์", "พิมพ์ภสันต์"),
        (6424650486, "เสาวลักษณ์", "ชมชื่น"),
        (6424650551, "เบญฤญา", "คำคงศักดิ์")
    ]
    team_data = pd.DataFrame(team_data, columns=['Student ID', 'First Name', 'Last Name'])
    st.table(team_data)

    st.markdown("---")
