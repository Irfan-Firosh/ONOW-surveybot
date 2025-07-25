import requests
import sqlite3
import os
from contextlib import contextmanager

SURVEY_API_USERNAME = os.getenv("SURVEY_API_USERNAME")
SURVEY_API_PASSWORD = os.getenv("SURVEY_API_PASSWORD")


@contextmanager
def get_db_connection(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        yield conn
    finally:
        conn.commit()
        conn.close()


def sanitize_column_name(text):
    return (
        text.strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("?", "")
        .replace("/", "_")
        .lower()
    )


def ensure_table_exists(cursor, survey_id, questions):
    table_name = f"survey_{survey_id}"

    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    exists = cursor.fetchone()

    if not exists:
        columns = ['contact_id TEXT PRIMARY KEY', 'name TEXT', 'is_anonymous BOOLEAN']
        for question in questions:
            col = sanitize_column_name(question)
            columns.append(f'"{col}" TEXT')
        create_stmt = f'CREATE TABLE {table_name} ({", ".join(columns)});'
        cursor.execute(create_stmt)
    else:
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = set(row[1] for row in cursor.fetchall())
        for question in questions:
            col = sanitize_column_name(question)
            if col not in existing_columns:
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col}" TEXT')


def fetch_all_survey_responses(auth_headers, survey_id, db_path):
    try:
        anon_counter = 1
        url = f"https://testing.survey.api.crm.onowenable.com/api/surveys/responses/all?surveyId={survey_id}&page=1"
        resp = requests.get(url, headers=auth_headers)
        resp.raise_for_status()
        data = resp.json()
        last_page = data["data"]["meta"]["lastPage"]

        all_entries = []

        for page in range(1, last_page + 1):
            url = f"https://testing.survey.api.crm.onowenable.com/api/surveys/responses/all?surveyId={survey_id}&page={page}"
            resp = requests.get(url, headers=auth_headers)
            resp.raise_for_status()
            page_data = resp.json()["data"]["data"]
            all_entries.extend(page_data)

        questions = set(entry["question"] for entry in all_entries if entry.get("question"))

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            ensure_table_exists(cursor, survey_id, questions)

            responses = {}

            for entry in all_entries:
                contact_id = entry.get("contactId")
                name = entry.get("name")
                question = entry.get("question")
                answer = entry.get("surAnswer")

                if not contact_id:
                    contact_id = f"anon_{anon_counter}"
                    name = "Anonymous"
                    is_anonymous = True
                    anon_counter += 1
                else:
                    is_anonymous = False

                key = contact_id
                if key not in responses:
                    responses[key] = {
                        "contact_id": contact_id,
                        "name": name,
                        "is_anonymous": is_anonymous
                    }

                if question:
                    responses[key][sanitize_column_name(question)] = answer

            table_name = f"survey_{survey_id}"
            for data in responses.values():
                columns = ', '.join([f'"{k}"' for k in data])
                placeholders = ', '.join(['?' for _ in data])
                update_clause = ', '.join([f'"{k}" = excluded."{k}"' for k in data if k != "contact_id"])

                sql = f'''
                    INSERT INTO {table_name} ({columns})
                    VALUES ({placeholders})
                    ON CONFLICT(contact_id) DO UPDATE SET {update_clause}
                '''
                cursor.execute(sql, tuple(data.values()))

    except Exception as e:
        raise


def get_data_from_api(survey_id):
    try:
        # Set database path based on survey ID
        db_path = os.getenv("DB_PATH", f"survey_{survey_id}.db")
        
        url = "https://testing.scale1.api.crm.onowenable.com/api/login"
        payload = {
            "username": SURVEY_API_USERNAME,
            "password": SURVEY_API_PASSWORD
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        token = response.json().get("access_token")

        if not token:
            return None

        auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if not os.path.exists(db_path):
            fetch_all_survey_responses(auth_headers, survey_id, db_path)
            return db_path, f"survey_{survey_id}"

        return db_path, f"survey_{survey_id}"

    except Exception as e:
        return None


if __name__ == "__main__":
    survey_id = 3200079
    db_path, table_name = get_data_from_api(survey_id)
    print(f"Survey {survey_id} imported successfully to {db_path} as {table_name}")
