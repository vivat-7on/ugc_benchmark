import uuid
from datetime import datetime
from typing import Any

from pymongo.database import Database

ALLOWED_COLLECTIONS = {
    "movie_ratings",
    "review_votes",
    "reviews",
    "bookmarks",
    }


class MongoRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _convert_for_mongo(self, value: Any) -> Any:
        if isinstance(value, uuid.UUID):
            return str(value)

        if isinstance(value, datetime):
            return value

        if isinstance(value, dict):
            return {
                key: self._convert_for_mongo(item)
                for key, item in value.items()
                }

        if isinstance(value, list):
            return [self._convert_for_mongo(item) for item in value]

        return value

    def create_indexes(self) -> None:
        print("Creating movie_ratings indexes")
        self.db.movie_ratings.create_index("user_id")

        print("Creating movie_ratings indexes")
        self.db.movie_ratings.create_index([("movie_id", 1), ("score", 1)])

        print("Creating movie_ratings indexes")
        self.db.movie_ratings.create_index(
            [("user_id", 1), ("movie_id", 1)],
            unique=True,
            )

        print("Creating reviews indexes")
        self.db.reviews.create_index("user_id")
        print("Creating reviews indexes")
        self.db.reviews.create_index([("movie_id", 1), ("review_likes", 1)])
        print("Creating reviews indexes")
        self.db.reviews.create_index([("movie_id", 1), ("created_at", 1)])

        print("Creating review_votes indexes")
        self.db.review_votes.create_index("user_id")
        print("Creating review_votes indexes")
        self.db.review_votes.create_index([("review_id", 1), ("score", 1)])
        print("Creating review_votes indexes")
        self.db.review_votes.create_index(
            [("user_id", 1), ("review_id", 1)],
            unique=True,
            )

        print("Creating bookmarks indexes")
        self.db.bookmarks.create_index([("user_id", 1), ("created_at", 1)])
        print("Creating bookmarks indexes")
        self.db.bookmarks.create_index(
            [("user_id", 1), ("movie_id", 1)],
            unique=True,
            )

    def insert_movie_ratings_batch(self, data: list[dict]):
        self._insert_batch(collection_name="movie_ratings", data=data)

    def insert_review_votes_batch(self, data: list[dict]):
        self._insert_batch(collection_name="review_votes", data=data)

    def insert_reviews_batch(self, data: list[dict]):
        self._insert_batch(collection_name="reviews", data=data)

    def insert_bookmarks_batch(self, data: list[dict]):
        self._insert_batch(collection_name="bookmarks", data=data)

    def _insert_batch(self, collection_name: str, data: list[dict]) -> None:
        if not data:
            return

        if collection_name not in ALLOWED_COLLECTIONS:
            raise ValueError(f"Collection {collection_name} not allowed")

        prepared_data = [
            self._convert_for_mongo(item)
            for item in data
            ]

        self.db[collection_name].insert_many(prepared_data, ordered=False)

    def clear_collections(self) -> None:
        for collection_name in ALLOWED_COLLECTIONS:
            self.db[collection_name].drop()

    def get_random_id(
        self,
        id_name: str,
        collection_name: str,
        ) -> str:
        if collection_name not in ALLOWED_COLLECTIONS:
            raise ValueError(f"Collection {collection_name} not allowed")

        if id_name not in {"user_id", "movie_id", "review_id"}:
            raise ValueError(f"Id name {id_name} not allowed")

        pipeline = [
            {"$sample": {"size": 1}},
            {"$project": {id_name: 1, "_id": 0}},
            ]
        result = list(self.db[collection_name].aggregate(pipeline))
        return result[0][id_name]

    def get_movies_by_user_id(self, user_id: str) -> list[dict]:
        return list(
            self.db.movie_ratings.find({"user_id": user_id}),
            )

    def get_count_likes_and_dislikes_by_movie_id(
        self,
        movie_id: str,
        ) -> list[dict]:
        pipeline = [
            {"$match": {"movie_id": movie_id}},
            {"$group": {"_id": "$score", "count": {"$sum": 1}}},
            ]
        return list(self.db.movie_ratings.aggregate(pipeline))

    def get_avg_movie_rating_by_movie_id(self, movie_id: str) -> float | None:
        pipeline = [
            {"$match": {"movie_id": movie_id}},
            {"$group": {"_id": None, "avg": {"$avg": "$score"}}},
            ]
        result = list(self.db.movie_ratings.aggregate(pipeline))

        if not result:
            return None
        return result[0]["avg"]

    def get_bookmarks_by_user_id(self, user_id: str) -> list[dict]:
        return list(self.db.bookmarks.find({"user_id": user_id}))

    def get_reviews_by_movie_id_ordered_by_likes(self, movie_id: str) -> list[
        dict]:
        return list(
            self.db.reviews
            .find({"movie_id": movie_id})
            .sort("review_likes", -1),
            )

    def explain_find(
        self,
        collection_name: str,
        filter_: dict,
        sort: list[tuple] | None = None,
        ) -> dict:
        if collection_name not in ALLOWED_COLLECTIONS:
            raise ValueError(f"Collection {collection_name} not allowed")

        cursor = self.db[collection_name].find(filter_)

        if sort:
            cursor = cursor.sort(sort)

        return cursor.explain()

    def explain_aggregate(
        self,
        collection_name: str,
        pipeline: list[dict],
        ) -> dict:
        if collection_name not in ALLOWED_COLLECTIONS:
            raise ValueError(f"Collection {collection_name} not allowed")

        return self.db.command(
            "explain",
            {
                "aggregate": collection_name,
                "pipeline": pipeline,
                "cursor": {},
                },
            verbosity="executionStats",
            )
