from conection import connection

async def add_event(title, capacity, event_date):
    conn = await connection()
    try:
        await conn.execute("""
            INSERT INTO events (title, capacity, event_date)
            VALUES ($1, $2, $3)
        """, title, capacity, event_date)
    finally:
        await conn.close()

async def get_events():
    conn = await connection()
    try:
        result = await conn.fetch("""
            SELECT *,(SELECT COUNT(*) FROM registrations
            WHERE event_id = events.events_id and status = 'confirmed') 
            AS confirmed FROM events
        """)
        return result
    finally:
        await conn.close()

async def get_event(event_id):
    conn = await connection()
    try:
        result = await conn.fetchrow("""
            SELECT * FROM events
            WHERE events_id = $1
        """, event_id)
        return result
    finally:
        await conn.close()

async def register_user(telegram_id, event_id):
    conn = await connection()
    try:
        event = await conn.fetchrow("""
            SELECT * FROM events
            WHERE events_id = $1
        """, event_id)

        if event is None:
            return "Event not found"

        registration = await conn.fetchrow("""
            SELECT * FROM registrations
            WHERE telegram_id = $1 and event_id = $2
        """, telegram_id, event_id)

        if registration:
            return "Already registered"

        confirmed = await conn.fetchrow("""
            SELECT COUNT(*) AS count
            FROM registrations
            WHERE event_id = $1
            AND status = 'confirmed'
        """, event_id)

        if confirmed["count"] < event["capacity"]:
            status = "confirmed"
        else:
            status = "waitlist"

        await conn.execute("""
            INSERT INTO registrations
            (telegram_id, event_id, status)
            VALUES ($1, $2, $3)
        """, telegram_id, event_id, status)
        return status

    finally:
        await conn.close()

async def add_from_waitlist(event_id):
    conn = await connection()
    try:
        user = await conn.fetchrow("""
            SELECT * FROM registrations
            WHERE event_id = $1
            AND status = 'waitlist'
            ORDER BY registered_at ASC
            LIMIT 1
        """, event_id)

        if user is None:
            return None

        await conn.execute("""
            UPDATE registrations
            SET status = 'confirmed'
            WHERE registrations_id = $1
        """, user["registrations_id"])
        return user["telegram_id"]

    finally:
        await conn.close()

async def cancel_registration(telegram_id, event_id):
    conn = await connection()
    try:
        registration = await conn.fetchrow("""
            SELECT * FROM registrations
            WHERE telegram_id = $1
            AND event_id = $2
        """, telegram_id, event_id)
        if registration is None:
            return "Not registered", None
        
        status = registration["status"]

        await conn.execute("""
            DELETE FROM registrations
            WHERE registrations_id = $1
        """, registration["registrations_id"])
    finally:
        await conn.close()

    promoted_user = None

    if status == "confirmed":
        promoted_user = await add_from_waitlist(event_id)
    return "Cancelled", promoted_user


async def get_my_events(telegram_id):
    conn = await connection()
    try:
        result = await conn.fetch("""
            SELECT * FROM registrations
            JOIN events ON registrations.event_id = events.events_id
            WHERE registrations.telegram_id = $1
            ORDER BY events.event_date
        """, telegram_id)
        return result

    finally:
        await conn.close()