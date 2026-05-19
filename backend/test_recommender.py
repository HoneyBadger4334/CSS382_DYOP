"""
Week 9 acceptance smoke test: personalized recommendations switch between
major-seeded, popularity, and collaborative modes as interaction data grows.

Run: python test_recommender.py
"""

from recommender import (
    GLOBAL_ACTIVATION_THRESHOLD,
    USER_ACTIVATION_THRESHOLD,
    store,
)


def run() -> None:
    store.reset(seed_demo=True)

    demo_feed = store.get_recommendations("demo-student-1", major="Computer Science", limit=5)
    assert demo_feed.global_interaction_count >= GLOBAL_ACTIVATION_THRESHOLD
    assert demo_feed.user_interaction_count >= USER_ACTIVATION_THRESHOLD
    assert demo_feed.model_ready is True
    assert demo_feed.mode == "collaborative"
    assert demo_feed.recommendations

    fresh_feed = store.get_recommendations("fresh-user", major=None, limit=5)
    assert fresh_feed.mode == "popularity"
    assert fresh_feed.major_source == "fallback-popularity"
    assert fresh_feed.user_interaction_count == 0
    assert fresh_feed.recommendations

    first_event = demo_feed.recommendations[0].id
    before = store.get_recommendations("fresh-user", major="Business", limit=5)
    store.record_interaction("fresh-user", first_event, "save", major="Business")
    after = store.get_recommendations("fresh-user", major="Business", limit=5)

    assert after.user_interaction_count == before.user_interaction_count + 1
    assert after.recommendations
    assert after.user_token_hash == before.user_token_hash

    print("✓ Personalized recommender smoke test passed")
    print(
        f"  global_interactions={demo_feed.global_interaction_count}, "
        f"demo_mode={demo_feed.mode}, fresh_mode={fresh_feed.mode}"
    )


if __name__ == "__main__":
    run()