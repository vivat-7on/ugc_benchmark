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
        
        CREATE INDEX IF NOT EXISTS idx_review_movie_id_review_likes
        ON reviews (movie_id, review_likes);
        
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

    def create_tables(self) -> None:
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
