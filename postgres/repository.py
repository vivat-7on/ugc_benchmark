import uuid

from psycopg2.extras import execute_values

ALLOWED_TABLES = {
    "movie_ratings",
    "review_votes",
    "reviews",
    "bookmarks",
    }


class PostgresRepo:
    def __init__(self, connection) -> None:
        self.connection = connection

    def _execute(self, sql: str) -> None:
        with self.connection.cursor() as cur:
            cur.execute(sql)
        self.connection.commit()

    def _fetch_all(self, sql: str, params: tuple = ()) -> list[tuple]:
        with self.connection.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def _create_movie_ratings_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS movie_ratings (
        user_id uuid NOT NULL,
        movie_id uuid NOT NULL,
        score smallint NOT NULL,
        created_at timestamp NOT NULL,
        updated_at timestamp NOT NULL,
        PRIMARY KEY (user_id, movie_id)
        );
        """
        self._execute(sql)

    def _create_review_votes_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS review_votes (
        user_id uuid NOT NULL,
        review_id uuid NOT NULL,
        score smallint NOT NULL,
        created_at timestamp NOT NULL,
        updated_at timestamp NOT NULL,
        PRIMARY KEY (user_id, review_id)
        );
        """
        self._execute(sql)

    def _create_reviews_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS reviews (
        review_id uuid PRIMARY KEY,
        user_id uuid NOT NULL,
        movie_id uuid NOT NULL,
        author text NOT NULL,
        review_text text NOT NULL,
        movie_score smallint NOT NULL,
        review_likes integer NOT NULL,
        review_dislikes integer NOT NULL,
        created_at timestamp NOT NULL,
        updated_at timestamp NOT NULL
        );
        """
        self._execute(sql)

    def _create_bookmarks_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS bookmarks (
        user_id uuid NOT NULL,
        movie_id uuid NOT NULL,
        created_at timestamp NOT NULL,
        PRIMARY KEY (user_id, movie_id)
        );
        """
        self._execute(sql)

    def create_indexes(self) -> None:
        sql = """
        CREATE INDEX IF NOT EXISTS idx_movie_ratings_user_id 
        ON movie_ratings (user_id);
        
        CREATE INDEX IF NOT EXISTS idx_movie_ratings_movie_id_score 
        ON movie_ratings (movie_id, score);
        
        
        CREATE INDEX IF NOT EXISTS idx_review_user_id
        ON reviews (user_id);
        
        CREATE INDEX IF NOT EXISTS idx_review_movie_id_review_likes_desc
        ON reviews (movie_id, review_likes DESC);
        
        CREATE INDEX IF NOT EXISTS idx_review_movie_id_created_at
        ON reviews (movie_id, created_at);
        
        
        CREATE INDEX IF NOT EXISTS idx_review_votes_user_id
        ON review_votes (user_id);
        
        CREATE INDEX IF NOT EXISTS idx_review_votes_review_id_score
        ON review_votes (review_id, score);
        
        
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id_created_at
        ON bookmarks (user_id, created_at);
        """
        self._execute(sql)

    def recreate_tables(self) -> None:
        self._drop_tables()

        self._create_movie_ratings_table()
        self._create_review_votes_table()
        self._create_reviews_table()
        self._create_bookmarks_table()

    def insert_movie_ratings_batch(self, data: list[dict]):
        self._insert_batch(table_name="movie_ratings", data=data)

    def insert_review_votes_batch(self, data: list[dict]):
        self._insert_batch(table_name="review_votes", data=data)

    def insert_reviews_batch(self, data: list[dict]):
        self._insert_batch(table_name="reviews", data=data)

    def insert_bookmarks_batch(self, data: list[dict]):
        self._insert_batch(table_name="bookmarks", data=data)

    def _insert_batch(self, data: list[dict], table_name: str) -> None:
        if not data:
            return

        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Table {table_name} not allowed")

        columns = list(data[0].keys())
        values = [
            tuple(row[column] for column in columns)
            for row in data
            ]
        columns_sql = ", ".join(columns)
        sql = f"""
        INSERT INTO {table_name} ({columns_sql})
        VALUES %s
        ON CONFLICT DO NOTHING;
        """
        with self.connection.cursor() as cur:
            execute_values(cur, sql, values)

        self.connection.commit()

    def get_random_id(
        self,
        id_name: str,
        table_name: str,
        ) -> uuid.UUID:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Table {table_name} not allowed")

        if id_name not in {"user_id", "movie_id", "review_id"}:
            raise ValueError(f"Column {id_name} not allowed")

        sql = f"""
        SELECT {id_name}
        FROM {table_name} 
        ORDER BY RANDOM()
        LIMIT 1;
        """

        return self._fetch_all(sql)[0][0]

    def get_movies_by_user_id(self, user_id: uuid.UUID) -> list[tuple]:
        sql = """
        SELECT * 
        FROM movie_ratings 
        WHERE user_id = %s;
        """
        return self._fetch_all(sql, (user_id,))

    def get_count_likes_and_dislikes_by_movie_id(
        self,
        movie_id: uuid.UUID,
        ) -> list[tuple]:
        sql = """
        SELECT score, COUNT(*) 
        FROM movie_ratings 
        WHERE movie_id = %s
        GROUP BY score;
        """
        return self._fetch_all(sql, (movie_id,))

    def get_avg_movie_rating_by_movie_id(
        self,
        movie_id: uuid.UUID,
        ) -> float | None:
        sql = """
        SELECT AVG(score) 
        FROM movie_ratings 
        WHERE movie_id = %s;
        """
        result = self._fetch_all(sql, (movie_id,))
        return result[0][0] if result else None

    def get_bookmarks_by_user_id(self, user_id: uuid.UUID) -> list[tuple]:
        sql = """
        SELECT *
        FROM bookmarks
        WHERE user_id = %s;
        """
        return self._fetch_all(sql, (user_id,))

    def get_reviews_by_movie_id_ordered_by_likes(
        self,
        movie_id: uuid.UUID,
        ) -> list[tuple]:
        sql = """
        SELECT *
        FROM reviews
        WHERE movie_id = %s
        ORDER BY review_likes DESC;
        """
        return self._fetch_all(sql, (movie_id,))

    def explain_analyze(self, sql: str, params: tuple = ()) -> list[tuple]:
        explain_sql = f"""EXPLAIN ANALYZE {sql};"""

        with self.connection.cursor() as cur:
            cur.execute(explain_sql, params)
            return cur.fetchall()

    def _drop_tables(self) -> None:
        sql = """
        DROP TABLE IF EXISTS 
            movie_ratings,
            review_votes,
            reviews,
            bookmarks
        CASCADE;
        """
        self._execute(sql)
