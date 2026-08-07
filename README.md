# lakebase-support-app

Part of the bootcamp assignments.

A small internal support-ticket system built as a **Databricks App** (Streamlit) backed by **Lakebase** (Postgres). Users can view tickets, create new ones, add messages to a ticket, and update a ticket's status — all reads and writes go straight to Lakebase.

## App URL

`https://ticketing-system-7474660406884316.aws.databricksapps.com`

## Architecture

- **Frontend / app logic:** Streamlit (`app/app.py`)
- **Backend:** Lakebase (Postgres) accessed via `psycopg` with a connection pool
- **Auth:** OAuth database credentials generated per-connection via the Databricks SDK (`WorkspaceClient.postgres.generate_database_credential`), so no static DB password is stored
- **Deployment:** Databricks Apps (`app/app.yaml`)

## Schema

Two related tables, defined in [`sql/schema.sql`](sql/schema.sql):

```sql
tickets
  ticket_id   SERIAL PRIMARY KEY
  title       TEXT NOT NULL
  status      TEXT NOT NULL DEFAULT 'open'
  created_by  TEXT NOT NULL
  created_at  TIMESTAMP NOT NULL DEFAULT now()

ticket_messages
  message_id    SERIAL PRIMARY KEY
  ticket_id     INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE
  message_text  TEXT NOT NULL
  author        TEXT NOT NULL
  created_at    TIMESTAMP NOT NULL DEFAULT now()
```

Sample data ([`sql/sample_date.sql`](sql/sample_date.sql)) seeds 3 tickets across 3 statuses (`open`, `in_progress`, `resolved`) with 2 messages each.

## Features

- View all support tickets
- Select a ticket and view its messages
- Create a new ticket
- Add a message to an existing ticket
- Update a ticket's status (`open` / `in_progress` / `resolved`)

## Screenshots

### Deployed application

Creating a new ticket:

![Create ticket](screenshots/Screenshot%202026-08-07%20at%204.43.12%20PM.png)

Viewing a ticket, its messages, and updating status:

![View ticket and messages](screenshots/Screenshot%202026-08-07%20at%204.43.34%20PM.png)

### Lakebase tables and sample records

`tickets` table, showing the seeded rows plus a ticket created through the app:

![tickets table](screenshots/Screenshot%202026-08-07%20at%204.44.14%20PM.png)

`ticket_messages` table, showing seeded messages plus one added through the app:

![ticket_messages table](screenshots/Screenshot%202026-08-07%20at%204.45.19%20PM.png)

`tickets` table before app interaction, for reference:

![tickets table initial state](screenshots/Screenshot%202026-08-07%20at%204.25.27%20PM.png)

## Reflection

**What was the most difficult part?** Getting the authentication right — connecting to Lakebase from the app without hardcoding credentials meant wiring up OAuth database credentials through the Databricks SDK and refreshing them per-connection via a custom `psycopg.Connection` subclass, rather than using a static password.

**How is Lakebase different from storing this data in a traditional analytics table?** Lakebase is a transactional Postgres database built for low-latency, row-level reads and writes (OLTP) — exactly what an app needs for creating a ticket or appending a single message. A traditional analytics table (Delta/lakehouse) is optimized for large batch reads and columnar scans, not frequent small transactional writes, so it's a poor fit for backing live application state.

**What feature would you add next?** Ticket priority/category with filtering, since it's a natural extension of the existing status field and would make the ticket list much more useful once volume grows.

## Local development

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

Requires `PGUSER`, `PGHOST`, `PGDATABASE`, and `ENDPOINT_NAME` environment variables pointing at a Lakebase Postgres instance, plus Databricks auth configured for `WorkspaceClient`.
