from statistics import mean
from time import perf_counter

from mongo.connection import get_mongo_db
from mongo.repository import MongoRepo
from postgres.connection import get_postgres_connection
from postgres.repository import PostgresRepo

REPEATS = 1000

GET_MOVIES_BY_USER_ID_SQL = """
SELECT * 
FROM movie_ratings 
WHERE user_id = %s;
"""

GET_COUNT_LIKES_AND_DISLIKES_BY_MOVIE_ID_SQL = """
SELECT score, COUNT(*) 
FROM movie_ratings 
WHERE movie_id = %s
GROUP BY score;
"""

GET_AVG_MOVIE_RATING_BY_MOVIE_ID_SQL = """
SELECT AVG(score) 
FROM movie_ratings 
WHERE movie_id = %s;
"""

GET_BOOKMARKS_BY_USER_ID_SQL = """
SELECT *
FROM bookmarks
WHERE user_id = %s;
"""

GET_REVIEWS_BY_MOVIE_ID_ORDERED_BY_LIKES_SQL = """
SELECT *
FROM reviews
WHERE movie_id = %s
ORDER BY review_likes DESC;
"""


def benchmark(func, get_id_func, *args, repeats: int = 100):
    timings = []
    for _ in range(repeats):
        id_ = get_id_func(*args)

        start = perf_counter()

        func(id_)

        timings.append(perf_counter() - start)

    print(f"Function: {func.__name__}")
    print(f"Runs: {repeats}")
    print(f"Avg: {mean(timings) * 1000:.3f} ms")
    print(f"Min: {min(timings) * 1000:.3f} ms")
    print(f"Max: {max(timings) * 1000:.3f} ms")
    print()


def print_postgres_explain_analyze(
    postgres_repo: PostgresRepo,
    sql: str,
    title: str,
    params: tuple,
    ) -> None:
    print(f"POSTGRES EXPLAIN ANALYZE: {title}")

    plan = postgres_repo.explain_analyze(sql, params)

    for row in plan:
        print(row[0])
    print()


def print_mongo_explain_analyze(plan: dict, title: str) -> None:
    print(f"MONGO EXPLAIN ANALYZE: {title}")

    stats = plan["executionStats"]
    winning_plan = plan["queryPlanner"]["winningPlan"]

    input_stage = winning_plan.get("inputStage", {})

    print("executionTimeMillis:", stats["executionTimeMillis"])
    print("totalKeysExamined:", stats["totalKeysExamined"])
    print("totalDocsExamined:", stats["totalDocsExamined"])
    print("stage:", winning_plan.get("stage"))
    print("inputStage:", input_stage.get("stage"))
    print("indexName:", input_stage.get("indexName"))
    print()



def run_postgres_reading() -> None:
    with get_postgres_connection() as connection:
        postgres_repo = PostgresRepo(connection=connection)

        user_id = postgres_repo.get_random_id("user_id", "movie_ratings")
        print_postgres_explain_analyze(
            postgres_repo=postgres_repo,
            sql=GET_MOVIES_BY_USER_ID_SQL,
            title="Movies by user id",
            params=(user_id,),
            )
        benchmark(
            postgres_repo.get_movies_by_user_id,
            postgres_repo.get_random_id,
            "user_id",
            "movie_ratings",
            repeats=REPEATS,
            )

        movie_id = postgres_repo.get_random_id("movie_id", "movie_ratings")
        print_postgres_explain_analyze(
            postgres_repo=postgres_repo,
            sql=GET_COUNT_LIKES_AND_DISLIKES_BY_MOVIE_ID_SQL,
            title="Count likes and dislikes by movie id",
            params=(movie_id,),
            )
        benchmark(
            postgres_repo.get_count_likes_and_dislikes_by_movie_id,
            postgres_repo.get_random_id,
            "movie_id",
            "movie_ratings",
            repeats=REPEATS,
            )

        movie_id = postgres_repo.get_random_id("movie_id", "movie_ratings")
        print_postgres_explain_analyze(
            postgres_repo=postgres_repo,
            sql=GET_AVG_MOVIE_RATING_BY_MOVIE_ID_SQL,
            title="Avg movie ratings by movie id",
            params=(movie_id,),
            )
        benchmark(
            postgres_repo.get_avg_movie_rating_by_movie_id,
            postgres_repo.get_random_id,
            "movie_id",
            "movie_ratings",
            repeats=REPEATS,
            )

        user_id = postgres_repo.get_random_id("user_id", "bookmarks")
        print_postgres_explain_analyze(
            postgres_repo=postgres_repo,
            sql=GET_BOOKMARKS_BY_USER_ID_SQL,
            title="Bookmarks by user id",
            params=(user_id,),
            )
        benchmark(
            postgres_repo.get_bookmarks_by_user_id,
            postgres_repo.get_random_id,
            "user_id",
            "bookmarks",
            repeats=REPEATS,
            )

        movie_id = postgres_repo.get_random_id("movie_id", "reviews")
        print_postgres_explain_analyze(
            postgres_repo=postgres_repo,
            sql=GET_REVIEWS_BY_MOVIE_ID_ORDERED_BY_LIKES_SQL,
            title="Reviews by movie id ordered by likes",
            params=(movie_id,),
            )
        benchmark(
            postgres_repo.get_reviews_by_movie_id_ordered_by_likes,
            postgres_repo.get_random_id,
            "movie_id",
            "reviews",
            repeats=REPEATS,
            )


def run_mongo_reading() -> None:
    with get_mongo_db() as db:
        mongo = MongoRepo(db=db)

        user_id = mongo.get_random_id("user_id", "movie_ratings")
        plan = mongo.explain_find(
            collection_name="movie_ratings",
            filter_={"user_id": user_id},
            )
        print_mongo_explain_analyze(
            plan=plan,
            title="Movies by user id",
            )

        benchmark(
            mongo.get_movies_by_user_id,
            mongo.get_random_id,
            "user_id",
            "movie_ratings",
            repeats=REPEATS,
            )



        movie_id = mongo.get_random_id("movie_id", "movie_ratings")
        plan = mongo.explain_aggregate(
            collection_name="movie_ratings",
            pipeline=[
                {"$match": {"movie_id": movie_id}},
                {"$group": {"_id": "$score", "count": {"$sum": 1}}},
                ],
            )
        print_mongo_explain_analyze(
            plan=plan,
            title="Count likes and dislikes by movie id",
            )

        benchmark(
            mongo.get_count_likes_and_dislikes_by_movie_id,
            mongo.get_random_id,
            "movie_id",
            "movie_ratings",
            repeats=REPEATS,
            )



        movie_id = mongo.get_random_id("movie_id", "movie_ratings")
        plan = mongo.explain_aggregate(
            collection_name="movie_ratings",
            pipeline=[
                {"$match": {"movie_id": movie_id}},
                {"$group": {"_id": None, "avg": {"$avg": "$score"}}},
                ]
            )
        print_mongo_explain_analyze(
            plan=plan,
            title="Avg movie ratings by movie id",
            )

        benchmark(
            mongo.get_avg_movie_rating_by_movie_id,
            mongo.get_random_id,
            "movie_id",
            "movie_ratings",
            repeats=REPEATS,
            )


        user_id = mongo.get_random_id("user_id", "bookmarks")
        plan = mongo.explain_find(
            collection_name="bookmarks",
            filter_={"user_id": user_id},
            )
        print_mongo_explain_analyze(
            plan=plan,
            title="Bookmarks by user id",
            )

        benchmark(
            mongo.get_bookmarks_by_user_id,
            mongo.get_random_id,
            "user_id",
            "bookmarks",
            repeats=REPEATS,
            )


        movie_id = mongo.get_random_id("movie_id", "reviews")
        plan = mongo.explain_find(
            collection_name="reviews",
            filter_={"movie_id": movie_id},
            sort=[("review_likes", -1)],
            )
        print_mongo_explain_analyze(
            plan=plan,
            title="Reviews by movie id ordered by likes",
            )

        benchmark(
            mongo.get_reviews_by_movie_id_ordered_by_likes,
            mongo.get_random_id,
            "movie_id",
            "reviews",
            repeats=REPEATS,
            )



def main():
    run_postgres_reading()
    run_mongo_reading()


if __name__ == "__main__":
    main()
