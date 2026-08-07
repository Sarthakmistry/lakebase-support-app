import os
import streamlit as st
import psycopg
from psycopg_pool import ConnectionPool
from databricks.sdk import WorkspaceClient

st.set_page_config(page_title="Support Tickets", layout="wide")

w = WorkspaceClient()

# Connection pool with automatic OAuth token rotation

class OAuthConnection(psycopg.Connection):
    @classmethod
    def connect(cls, conninfo="", **kwargs):
        endpoint_name = os.environ["ENDPOINT_NAME"]
        credential = w.postgres.generate_database_credential(endpoint=endpoint_name)
        kwargs["password"] = credential.token
        return super().connect(conninfo, **kwargs)


@st.cache_resource
def get_pool():
    username = os.environ["PGUSER"]
    host = os.environ["PGHOST"]
    port = os.environ.get("PGPORT", "5432")
    database = os.environ["PGDATABASE"]
    sslmode = os.environ.get("PGSSLMODE", "require")
    return ConnectionPool(
        conninfo=f"dbname={database} user={username} host={host} port={port} sslmode={sslmode}",
        connection_class=OAuthConnection,
        min_size=1,
        max_size=10,
        open=True,
    )

def run_query(query, params=None, fetch=True):
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch:
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
            conn.commit()

# --- Data access ----------------------------------------------------------

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

# --- UI --------------------------------------------------------------------

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
            statuses = ["open", "in_progress", "resolved"]
            new_status = st.selectbox(
                "Status",
                statuses,
                index=statuses.index(ticket["status"]) if ticket["status"] in statuses else 0,
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