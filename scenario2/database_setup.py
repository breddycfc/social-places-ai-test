"""
Social Places AI Engineer Test - Scenario 2
Database Setup and Sample Data
Author: Branden Reddy
"""

import sqlite3
import random
from datetime import datetime, timedelta

STORES = [
    "Social Places V&A Waterfront",
    "Social Places Canal Walk",
    "Social Places Cavendish Square",
    "Social Places Century City",
    "Social Places Stellenbosch",
    "Social Places Camps Bay",
    "Social Places Sea Point",
    "Social Places Claremont",
    "Social Places Tyger Valley",
    "Social Places Somerset West"
]

PLATFORMS = ["Google", "Facebook", "TripAdvisor"]
STATUSES = ["Resolved", "Open", "Pending"]

POSITIVE_REVIEWS = [
    ("Amazing service from start to finish! The staff were friendly and attentive.", ["Service [Positive]"]),
    ("Food was delicious and the place was spotless. Will definitely come back.", ["Food [Positive]", "Cleanliness [Positive]"]),
    ("Quick service and great atmosphere. Love this spot!", ["Service [Positive]", "Atmosphere [Positive]"]),
    ("The waiter was so helpful and made great recommendations.", ["Service [Positive]"]),
    ("Beautiful location and excellent food quality.", ["Environment [Positive]", "Food [Positive]"]),
    ("Best coffee in Cape Town, hands down. Staff are always smiling.", ["Food [Positive]", "Service [Positive]"]),
]

NEGATIVE_REVIEWS = [
    ("Service was incredibly slow, waited 45 minutes for our food.", ["Service [Negative]"]),
    ("The waiter was rude and seemed annoyed when we asked questions.", ["Service [Negative]"]),
    ("Place was dirty, tables weren't cleaned properly.", ["Cleanliness [Negative]"]),
    ("Staff ignored us for 20 minutes before taking our order.", ["Service [Negative]"]),
    ("Food was cold when it arrived. Very disappointing.", ["Food [Negative]", "Service [Negative]"]),
    ("Manager was unhelpful when we complained about the long wait.", ["Service [Negative]"]),
    ("Rude staff, won't be coming back.", ["Service [Negative]"]),
    ("Terrible experience. The waiter forgot our order twice.", ["Service [Negative]"]),
]

MIXED_REVIEWS = [
    ("Food was good but service could be better.", ["Food [Positive]", "Service [Negative]"]),
    ("Nice atmosphere but staff seemed understaffed.", ["Atmosphere [Positive]", "Service [Negative]"]),
    ("Great location, average food.", ["Environment [Positive]", "Food [Neutral]"]),
]

REVIEWER_NAMES = [
    "John Smith", "Sarah Johnson", "Michael Brown", "Emma Wilson", "David Lee",
    "Lisa Anderson", "James Taylor", "Jennifer Martin", "Robert Garcia", "Michelle Davis",
    "William Miller", "Amanda White", "Christopher Moore", "Ashley Thompson", "Daniel Jackson",
    "Samantha Harris", "Matthew Clark", "Nicole Lewis", "Andrew Walker", "Stephanie Hall",
    "Thabo Molefe", "Lerato Ndlovu", "Sipho Khumalo", "Nomvula Dlamini", "Bongani Nkosi",
    "Zanele Mbeki", "Themba Sithole", "Ayanda Zulu", "Mandla Mahlangu", "Lindiwe Cele"
]

WAITRON_NAMES = ["Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Quinn", "Avery"]
MEALS = ["Burger and Chips", "Fish and Chips", "Steak", "Salad", "Pizza", "Pasta", "Sushi", "Breakfast", "Coffee and Cake"]


def create_database(db_path="reviews.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute("DROP TABLE IF EXISTS review_categories")
    cursor.execute("DROP TABLE IF EXISTS review_ratings")
    cursor.execute("DROP TABLE IF EXISTS review_extras")

    cursor.execute("""
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            brand_name TEXT NOT NULL DEFAULT 'Social Places',
            platform TEXT NOT NULL,
            review_date DATETIME NOT NULL,
            review_comment TEXT,
            reviewer_name TEXT,
            review_status TEXT DEFAULT 'Open',
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE review_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE review_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            rating_value INTEGER CHECK(rating_value >= 1 AND rating_value <= 5),
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE review_extras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            field_value TEXT,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
        )
    """)

    cursor.execute("CREATE INDEX idx_reviews_store ON reviews(store_name)")
    cursor.execute("CREATE INDEX idx_reviews_brand ON reviews(brand_name)")
    cursor.execute("CREATE INDEX idx_reviews_date ON reviews(review_date)")
    cursor.execute("CREATE INDEX idx_reviews_rating ON reviews(rating)")
    cursor.execute("CREATE INDEX idx_reviews_platform ON reviews(platform)")
    cursor.execute("CREATE INDEX idx_categories_review ON review_categories(review_id)")
    cursor.execute("CREATE INDEX idx_categories_name ON review_categories(category_name)")
    cursor.execute("CREATE INDEX idx_categories_sentiment ON review_categories(sentiment)")
    cursor.execute("CREATE INDEX idx_ratings_review ON review_ratings(review_id)")
    cursor.execute("CREATE INDEX idx_extras_review ON review_extras(review_id)")

    conn.commit()
    return conn


def generate_sample_data(conn, num_reviews=5000):
    cursor = conn.cursor()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    for i in range(num_reviews):
        days_offset = random.randint(0, 730)
        review_date = start_date + timedelta(days=days_offset, hours=random.randint(8, 22))

        store = random.choice(STORES)

        if store in ["Social Places Canal Walk", "Social Places Tyger Valley"]:
            review_type = random.choices(
                ["positive", "negative", "mixed"],
                weights=[30, 50, 20]
            )[0]
        else:
            review_type = random.choices(
                ["positive", "negative", "mixed"],
                weights=[60, 25, 15]
            )[0]

        if review_type == "positive":
            comment, categories = random.choice(POSITIVE_REVIEWS)
            rating = random.randint(4, 5)
        elif review_type == "negative":
            comment, categories = random.choice(NEGATIVE_REVIEWS)
            rating = random.randint(1, 3)
        else:
            comment, categories = random.choice(MIXED_REVIEWS)
            rating = random.randint(2, 4)

        cursor.execute("""
            INSERT INTO reviews (store_name, brand_name, platform, review_date,
                               review_comment, reviewer_name, review_status, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            store,
            "Social Places",
            random.choice(PLATFORMS),
            review_date.strftime("%Y-%m-%d %H:%M:%S"),
            comment,
            random.choice(REVIEWER_NAMES),
            random.choice(STATUSES),
            rating
        ))

        review_id = cursor.lastrowid

        for cat in categories:
            cat_name = cat.split(" [")[0]
            sentiment = cat.split("[")[1].replace("]", "")
            cursor.execute("""
                INSERT INTO review_categories (review_id, category_name, sentiment)
                VALUES (?, ?, ?)
            """, (review_id, cat_name, sentiment))

        if random.random() > 0.3:
            service_rating = max(1, min(5, rating + random.randint(-1, 1)))
            cursor.execute("""
                INSERT INTO review_ratings (review_id, field_name, rating_value)
                VALUES (?, ?, ?)
            """, (review_id, "Service", service_rating))

        if random.random() > 0.5:
            cursor.execute("""
                INSERT INTO review_ratings (review_id, field_name, rating_value)
                VALUES (?, ?, ?)
            """, (review_id, "Cleanliness", random.randint(3, 5)))

        if random.random() > 0.6:
            cursor.execute("""
                INSERT INTO review_extras (review_id, field_name, field_value)
                VALUES (?, ?, ?)
            """, (review_id, "Waitron Name", random.choice(WAITRON_NAMES)))

        if random.random() > 0.7:
            cursor.execute("""
                INSERT INTO review_extras (review_id, field_name, field_value)
                VALUES (?, ?, ?)
            """, (review_id, "Meal Ordered", random.choice(MEALS)))

    conn.commit()
    print(f"Generated {num_reviews} sample reviews")


def get_schema_info(conn):
    schema = """
DATABASE SCHEMA:

Table: reviews
    id              INTEGER PRIMARY KEY
    store_name      TEXT (e.g., 'Social Places V&A Waterfront')
    brand_name      TEXT (always 'Social Places' for this database)
    platform        TEXT (Google, Facebook, TripAdvisor)
    review_date     DATETIME
    review_comment  TEXT
    reviewer_name   TEXT
    review_status   TEXT (Resolved, Open, Pending)
    rating          INTEGER (1-5)

Table: review_categories
    id              INTEGER PRIMARY KEY
    review_id       INTEGER (foreign key to reviews.id)
    category_name   TEXT (e.g., 'Service', 'Food', 'Cleanliness')
    sentiment       TEXT (Positive, Negative, Neutral)

Table: review_ratings (dynamic rating fields)
    id              INTEGER PRIMARY KEY
    review_id       INTEGER (foreign key to reviews.id)
    field_name      TEXT (e.g., 'Service', 'Cleanliness')
    rating_value    INTEGER (1-5)

Table: review_extras (dynamic extra fields)
    id              INTEGER PRIMARY KEY
    review_id       INTEGER (foreign key to reviews.id)
    field_name      TEXT (e.g., 'Waitron Name', 'Meal Ordered')
    field_value     TEXT

AVAILABLE STORES:
""" + "\n".join(f"  - {store}" for store in STORES)

    return schema


if __name__ == "__main__":
    print("Setting up database...")
    conn = create_database("reviews.db")
    generate_sample_data(conn, num_reviews=5000)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reviews")
    print(f"Total reviews: {cursor.fetchone()[0]}")

    cursor.execute("""
        SELECT store_name, COUNT(*) as count
        FROM reviews
        GROUP BY store_name
        ORDER BY count DESC
    """)
    print("\nReviews by store:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cursor.execute("""
        SELECT category_name, sentiment, COUNT(*) as count
        FROM review_categories
        WHERE category_name = 'Service'
        GROUP BY sentiment
        ORDER BY count DESC
    """)
    print("\nService category breakdown:")
    for row in cursor.fetchall():
        print(f"  {row[0]} [{row[1]}]: {row[2]}")

    conn.close()
    print("\nDatabase setup complete!")
