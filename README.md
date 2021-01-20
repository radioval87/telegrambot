A telegram bot that welcomes new members of a group talk and bans unwanted ones. 

New participant is welcomed differently depending on the way he/she was invited.
If the new member is invited by link, he/she has 3 tries to mention a person who invited them. They are banned for a period of time if they fail to do so in time.

A person who is asked to confirm a new member can answer with a reply keyboard. If this person doesn't confirm the new member in given time, the candidate is also banned.

A database powered by SQLAlchemy is integrated into this bot to maintain users, number of people they can invite and logging.
