
import statistics
import time

from database import (
    create_database,
    connect_db,
    view_player_page,
    remove_player,
)


def setup_test_data():
    create_database()

    with connect_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id, username, role)
            VALUES (1, 'test_dm', 'dm'),
                   (2, 'test_player', 'player')
        """)

        conn.execute("""
            INSERT OR IGNORE INTO parties
                (party_id, party_name, dm_user_id)
            VALUES (1, 'Test Party', 1)
        """)

        conn.execute("""
            INSERT OR IGNORE INTO party_members (party_id, user_id)
            VALUES (1, 1), (1, 2)
        """)

        conn.execute("""
            INSERT OR IGNORE INTO characters
                (character_id, user_id, party_id, character_name)
            VALUES (1, 2, 1, 'Test Character')
        """)


def run_test(name, operation, target_seconds, iterations=100):
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        operation()
        times.append(time.perf_counter() - start)

    times.sort()
    within_target = sum(t <= target_seconds for t in times)
    percentage = within_target / iterations * 100

    print(f"\n{name}")
    print(f"Requests: {iterations}")
    print(f"Average: {statistics.mean(times):.6f} seconds")
    print(f"95th percentile: {times[int(0.95 * (iterations - 1))]:.6f} seconds")
    print(f"Within target: {percentage:.1f}%")
    print(f"Requirement met: {percentage >= 95}%")


if __name__ == "__main__":
    setup_test_data()

    run_test(
        "DM views player page",
        lambda: view_player_page(1, 1, 2),
        target_seconds=3.0
    )

    # Re-add membership before each removal test because removal
    # deletes the membership row.
    def remove_and_restore():
        with connect_db() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO party_members (party_id, user_id)
                VALUES (1, 2)
            """)

        remove_player(1, 1, 2)

    run_test(
        "DM removes player",
        remove_and_restore,
        target_seconds=2.0
    )