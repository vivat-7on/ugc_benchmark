import uuid
import random
from datetime import datetime
from time import perf_counter
from typing import Any

from faker import Faker
from tqdm import tqdm

from mongo.connection import get_mongo_db
from mongo.repository import MongoRepo
from postgres.connection import get_postgres_connection
from postgres.repository import PostgresRepo

BATCH_SIZE = 10_000
USERS_COUNT = 1_000_000
MOVIES_COUNT = 10_000
REVIEWS_COUNT = 1_000_000

fake = Faker()


def generate_created_and_updated_at() -> tuple[datetime, datetime]:
    created_at = fake.date_time_between(
        start_date="-30y",
        end_date="now",
        )
    updated_at = fake.date_time_between(
        start_date=created_at,
        end_date="now",
        )
    return created_at, updated_at


def generate_movie_ratings(
    user_id: uuid.UUID,
    movie_ids: list[uuid.UUID],
    ) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for movie_id in movie_ids:
        created_at, updated_at = generate_created_and_updated_at()
        score = random.choice([0, 10])
        results.append(
            {
                "user_id": user_id,
                "movie_id": movie_id,
                "score": score,
                "created_at": created_at,
                "updated_at": updated_at,
                },
            )

    return results


def generate_review(
    review_id: uuid.UUID,
    user_id: uuid.UUID,
    movie_id: uuid.UUID,
    ) -> dict[str, Any]:
    author = fake.user_name()
    review_text = fake.paragraph()
    score = random.choice([0, 10])
    review_likes = random.randint(0, 150)
    review_dislikes = random.randint(0, 150)
    created_at, updated_at = generate_created_and_updated_at()
    return {
        "review_id": review_id,
        "user_id": user_id,
        "movie_id": movie_id,
        "author": author,
        "review_text": review_text,
        "movie_score": score,
        "review_likes": review_likes,
        "review_dislikes": review_dislikes,
        "created_at": created_at,
        "updated_at": updated_at,
        }


def generate_review_votes(
    user_id: uuid.UUID,
    review_ids: list[uuid.UUID],
    ) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for review_id in review_ids:
        created_at, updated_at = generate_created_and_updated_at()
        score = random.choice([0, 10])
        results.append(
            {
                "user_id": user_id,
                "review_id": review_id,
                "score": score,
                "created_at": created_at,
                "updated_at": updated_at,
                },
            )

    return results


def generate_bookmarks(
    user_id: uuid.UUID,
    movie_ids: list[uuid.UUID],
    ) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for movie_id in movie_ids:
        created_at, _ = generate_created_and_updated_at()
        results.append(
            {
                "user_id": user_id,
                "movie_id": movie_id,
                "created_at": created_at,
                },
            )
    return results


def generate_and_insert_data(
    repo: PostgresRepo | MongoRepo,
    user_ids: list[uuid.UUID],
    movie_ids: list[uuid.UUID],
    review_ids: list[uuid.UUID],
    desc: str,
    ) -> None:
    movie_ratings_batch = []
    review_votes_batch = []
    reviews_batch = []
    bookmarks_batch = []
    for index, user_id in enumerate(tqdm(user_ids, desc=desc)):
        if len(movie_ratings_batch) >= BATCH_SIZE:
            repo.insert_movie_ratings_batch(movie_ratings_batch)
            movie_ratings_batch = []

        if len(review_votes_batch) >= BATCH_SIZE:
            repo.insert_review_votes_batch(review_votes_batch)
            review_votes_batch = []

        if len(reviews_batch) >= BATCH_SIZE:
            repo.insert_reviews_batch(reviews_batch)
            reviews_batch = []

        if len(bookmarks_batch) >= BATCH_SIZE:
            repo.insert_bookmarks_batch(bookmarks_batch)
            bookmarks_batch = []

        ten_movie_ids = random.sample(movie_ids, 10)
        movie_ratings_batch.extend(
            generate_movie_ratings(user_id, ten_movie_ids),
            )

        ten_review_ids = random.sample(review_ids, 10)
        review_votes_batch.extend(
            generate_review_votes(user_id, ten_review_ids),
            )

        movie_id = random.choice(movie_ids)
        review_id = review_ids[index]
        reviews_batch.append(generate_review(review_id, user_id, movie_id))

        ten_movie_ids = random.sample(movie_ids, 10)
        bookmarks_batch.extend(generate_bookmarks(user_id, ten_movie_ids))

    if movie_ratings_batch:
        repo.insert_movie_ratings_batch(movie_ratings_batch)

    if review_votes_batch:
        repo.insert_review_votes_batch(review_votes_batch)

    if reviews_batch:
        repo.insert_reviews_batch(reviews_batch)

    if bookmarks_batch:
        repo.insert_bookmarks_batch(bookmarks_batch)


def generate_postgres_data(
    user_ids: list[uuid.UUID],
    movie_ids: list[uuid.UUID],
    review_ids: list[uuid.UUID],
    postgres_repo: PostgresRepo,
    ) -> None:
    postgres_repo.recreate_tables()
    generate_and_insert_data(
        repo=postgres_repo,
        user_ids=user_ids,
        movie_ids=movie_ids,
        review_ids=review_ids,
        desc="Generating PostgreSQL data",
        )


def generate_mongo_data(
    user_ids: list[uuid.UUID],
    movie_ids: list[uuid.UUID],
    review_ids: list[uuid.UUID],
    mongo_repo: MongoRepo,
    ) -> None:
    generate_and_insert_data(
        repo=mongo_repo,
        user_ids=user_ids,
        movie_ids=movie_ids,
        review_ids=review_ids,
        desc="Generating MongoDB data",
        )


def main() -> None:
    user_ids = [uuid.uuid4() for _ in range(USERS_COUNT)]
    movie_ids = [uuid.uuid4() for _ in range(MOVIES_COUNT)]
    review_ids = [uuid.uuid4() for _ in range(REVIEWS_COUNT)]



    with get_postgres_connection() as postgres_connection:
        postgres_repo = PostgresRepo(postgres_connection)

        before_postgres_data = perf_counter()

        generate_postgres_data(
            user_ids=user_ids,
            movie_ids=movie_ids,
            review_ids=review_ids,
            postgres_repo=postgres_repo,
            )

        after_postgres_data = perf_counter()
        print(f"Generated postgres data: {after_postgres_data - before_postgres_data:.2f} seconds")

        before_postgres_index = perf_counter()

        postgres_repo.create_indexes()

        after_postgres_index = perf_counter()
        print(f"Generated postgres index: {after_postgres_index - before_postgres_index:.2f} seconds")



    with get_mongo_db() as db:
        mongo_repo = MongoRepo(db)

        mongo_repo.clear_collections()

        before_mongo_data = perf_counter()

        generate_mongo_data(
            user_ids=user_ids,
            movie_ids=movie_ids,
            review_ids=review_ids,
            mongo_repo=mongo_repo,
            )

        after_mongo_data = perf_counter()
        print(f"Generated mongo data: {after_mongo_data - before_mongo_data:.2f} seconds")

        before_mongo_index = perf_counter()
        mongo_repo.create_indexes()
        after_mongo_index = perf_counter()
        print(f"Generated mongo index: {after_mongo_index - before_mongo_index:.2f} seconds")


if __name__ == "__main__":
    main()
