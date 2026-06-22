import os
import socket
import time
import argparse
from urllib.parse import urlparse

def wait_for_db():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='Database URL')
    args = parser.parse_args()

    db_url = args.url or os.environ.get('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL found. Skipping wait.")
        return

    url = urlparse(db_url)
    host = url.hostname
    port = url.port or 5432

    print(f"Waiting for database at {host}:{port}...")
    
    start_time = time.time()
    timeout = 60
    
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                print("Database is up!")
                break
        except (socket.error, socket.timeout):
            if time.time() - start_time > timeout:
                print("Timeout waiting for database.")
                exit(1)
            time.sleep(1)

if __name__ == "__main__":
    wait_for_db()
