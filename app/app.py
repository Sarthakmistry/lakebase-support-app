import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

st.set_page_config(page_title="Support Tickets", layout="wide")


# database connection
def get_connection():
    return psycopg2.connect(
        host=os.environ["LAKEBASE_HOST"],
        port=os.environ.get("LAKEBASE_PORT", "5432"),
        dbname=os.environ["LAKEBASE_DB"],
        user=os.environ["LAKEBASE_USER"],
        password=os.environ["LAKEBASE_PASSWORD"],
        sslmode="require",
    )


def run_query(query, params=None, fetch=True):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            if fetch:
                return cur.fetchall()
            conn.commit()
    finally:
        conn.close()

# Data access

def get_tickets():
    return run_query("SELECT * FROM tickets ORDER BY created_at DESC")

def get_messages(ticket_id):
    return run_query(
        "SELECT * FROM ticket_messages WHERE ticket_id = %s ORDER BY created_at",
        (ticket_id,),
    )

def create_ticket(title, created_by):
    run_query(
        "INSERT INTO tickets (title, created_by) VALUES (%s, %s)",
        (title, created_by),
        fetch=False,
    )

def add_message(ticket_id, message_text, author):
    run_query(
        "INSERT INTO ticket_messages (ticket_id, message_text, author) VALUES (%s, %s, %s)",
        (ticket_id, message_text, author),
        fetch=False,
    )

def update_status(ticket_id, status):
    run_query(
        "UPDATE tickets SET status = %s WHERE ticket_id = %s",
        (status, ticket_id),
        fetch=False,
    )

# UI 

st.title("Support Ticket System")

tab_view, tab_create = st.tabs(["View Tickets", "Create Ticket"])

with tab_create:
    st.subheader("New Ticket")
    with st.form("new_ticket"):
        title = st.text_input("Title")
        created_by = st.text_input("Your name")
        submitted = st.form_submit_button("Create Ticket")
        if submitted:
            if title.strip() and created_by.strip():
                create_ticket(title.strip(), created_by.strip())
                st.success("Ticket created.")
                st.rerun()
            else:
                st.error("Title and name are required.")

with tab_view:
    tickets = get_tickets()
    if not tickets:
        st.info("No tickets yet.")
    else:
        options = {f"#{t['ticket_id']} — {t['title']} [{t['status']}]": t["ticket_id"] for t in tickets}
        selected_label = st.selectbox("Select a ticket", list(options.keys()))
        ticket_id = options[selected_label]
        ticket = next(t for t in tickets if t["ticket_id"] == ticket_id)

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Created by:** {ticket['created_by']}  |  **Created at:** {ticket['created_at']}")
        with col2:
            new_status = st.selectbox(
                "Status",
                ["open", "in_progress", "resolved"],
                index=["open", "in_progress", "resolved"].index(ticket["status"])
                if ticket["status"] in ["open", "in_progress", "resolved"] else 0,
                key=f"status_{ticket_id}",
            )
            if new_status != ticket["status"]:
                update_status(ticket_id, new_status)
                st.rerun()

        st.divider()
        st.subheader("Messages")
        for m in get_messages(ticket_id):
            st.markdown(f"**{m['author']}** · _{m['created_at']}_")
            st.write(m["message_text"])
            st.markdown("---")

        with st.form("new_message"):
            msg_text = st.text_area("Add a message")
            msg_author = st.text_input("Your name", key="msg_author")
            msg_submitted = st.form_submit_button("Send")
            if msg_submitted:
                if msg_text.strip() and msg_author.strip():
                    add_message(ticket_id, msg_text.strip(), msg_author.strip())
                    st.rerun()
                else:
                    st.error("Message and name are required.")