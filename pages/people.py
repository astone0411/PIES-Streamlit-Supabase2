import streamlit as st
import pandas as pd
from utils.supabase_db import get_supabase_connection

def show():
    st.markdown("## 👤 People Database")

    conn = get_supabase_connection()

    # -------------------------
    # Add person form
    # -------------------------
    with st.form("add_person", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First name")
            age = st.number_input("Age", min_value=0, max_value=120)

        with col2:
            last_name = st.text_input("Last name")
            sex = st.selectbox("Sex", ["F", "M", "Other"])

        submitted = st.form_submit_button("Add person", type="primary")

        if submitted:
            if not first_name or not last_name:
                st.error("First and last name are required.")
            else:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        insert into people (first_name, last_name, age, sex)
                        values (%s, %s, %s, %s);
                        """,
                        (first_name, last_name, age, sex),
                    )
                    conn.commit()
                st.success("✅ Person added")
                st.rerun()

    st.divider()

    # -------------------------
    # Display table
    # -------------------------
    with conn.cursor() as cur:
        cur.execute(
            "select id, first_name, last_name, age, sex from people order by id desc;"
        )
        rows = cur.fetchall()

    df = pd.DataFrame(
        rows, columns=["ID", "First Name", "Last Name", "Age", "Sex"]
    )

    st.dataframe(df, use_container_width=True)