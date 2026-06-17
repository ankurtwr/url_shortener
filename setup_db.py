"""
Database Setup Script
Creates the 'url_shortner_db' database and required tables.
Run this once before starting the application.
"""

import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'url_shortner_db')


def setup_database():
    """Create the database if it doesn't exist."""
    print(f"Connecting to MySQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")

    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    try:
        with connection.cursor() as cursor:
            # Create database
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"Database '{DB_NAME}' is ready.")

            # Switch to the database
            cursor.execute(f"USE `{DB_NAME}`")

            # Create urls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    short_code VARCHAR(30) NOT NULL,
                    original_url TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME DEFAULT NULL,
                    click_count INT DEFAULT 0,
                    is_custom BOOLEAN DEFAULT FALSE,
                    UNIQUE INDEX idx_short_code (short_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("Table 'urls' is ready.")

        connection.commit()
        print("\nDatabase setup complete!")
        print(f"Connection string: mysql+pymysql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    finally:
        connection.close()


if __name__ == '__main__':
    setup_database()
