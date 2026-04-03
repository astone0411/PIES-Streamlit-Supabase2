import os
import psycopg
import streamlit as st

@st.cache_resource
def get_supabase_connection():
    return psycopg.connect(
        host="aws-1-us-west-1.pooler.supabase.com",
        port=6543,
        dbname="postgres",
        user="postgres.xovmkkshwlluphengwtx",
        password=os.environ["SUPABASE_DB_PASSWORD"],
        sslmode="require",
    )
