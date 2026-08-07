INSERT INTO tickets (title, status, created_by) VALUES
    ('Cannot log into dashboard', 'open', 'alice'),
    ('Export button not working', 'in_progress', 'bob'),
    ('Feature request: dark mode', 'resolved', 'carol');

INSERT INTO ticket_messages (ticket_id, message_text, author) VALUES
    (1, 'I keep getting a 403 error when logging in.', 'alice'),
    (1, 'Can you try clearing your cache and retrying?', 'support_agent'),
    (2, 'The export button just spins forever.', 'bob'),
    (2, 'Looking into this — seems related to a recent deploy.', 'support_agent'),
    (3, 'Would love a dark mode option!', 'carol'),
    (3, 'Added in the latest release, please check it out.', 'support_agent');