"""
Comprehensive API endpoint test script
"""
import json
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://localhost:8000/api/v1"


def request(method, path, body=None):
    """Send HTTP request with proper URL encoding"""
    if "?" in path:
        base_path, query = path.split("?", 1)
        params = urllib.parse.parse_qs(query)
        encoded_params = urllib.parse.urlencode(params, doseq=True)
        path = f"{base_path}?{encoded_params}"
    url = BASE + urllib.parse.quote(path, safe="/?=&")
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test():
    print("=" * 60)
    print("1. Create 5 users with tags")
    users_data = [
        {"username": "alice", "nickname": "Alice", "tags": ["Python", "ML", "basketball", "photo"]},
        {"username": "bob", "nickname": "Bob", "tags": ["Python", "Java", "basketball", "gaming"]},
        {"username": "carol", "nickname": "Carol", "tags": ["ML", "photo", "travel", "gaming"]},
        {"username": "dave", "nickname": "Dave", "tags": ["Python", "travel", "movie", "food"]},
        {"username": "eve", "nickname": "Eve", "tags": ["Java", "movie", "basketball", "food"]},
    ]
    users = []
    for u in users_data:
        status, resp = request("POST", "/users/", u)
        assert status == 201, f"Create failed: {resp}"
        users.append(resp)
        print(f"  Created: ID={resp['id']} {resp['nickname']} tags={resp['tags']}")
    print("  PASS\n")

    # ========== 2. List and search users ==========
    print("=" * 60)
    print("2. List and search users")
    status, resp = request("GET", "/users/?page=1&page_size=10")
    assert status == 200
    print(f"  Total users: {resp['total']}")
    assert resp['total'] == 5

    # Search by username
    status, resp = request("GET", f"/users/?keyword=bob")
    assert status == 200 and resp["total"] == 1
    print(f"  Search 'bob': found {resp['total']} user(s)")
    # Search by nickname
    status, resp = request("GET", "/users/?keyword=Car")
    assert status == 200 and resp["total"] == 1
    print(f"  Search 'Car': found {resp['total']} user(s) (Carol matched)")
    print("  PASS\n")

    # ========== 3. Get single user ==========
    print("=" * 60)
    print("3. Get user detail")
    status, resp = request("GET", f"/users/{users[0]['id']}")
    assert status == 200
    print(f"  User: {resp['nickname']}, tags={resp['tags']}")
    assert resp['nickname'] == 'Alice'
    print("  PASS\n")

    # ========== 4. Update user ==========
    print("=" * 60)
    print("4. Update user")
    status, resp = request("PUT", f"/users/{users[0]['id']}", {"bio": "I love tech and sports"})
    assert status == 200
    print(f"  Updated bio: {resp['bio']}")
    assert resp['bio'] == "I love tech and sports"
    print("  PASS\n")

    # ========== 5. Add friendships ==========
    print("=" * 60)
    print("5. Add friendships (undirected)")
    # Social graph:
    # Alice -- Bob, Alice -- Carol, Alice -- Dave
    # Bob -- Carol
    # Carol -- Eve
    friendships_to_create = [
        (users[0]["id"], users[1]["id"]),  # Alice-Bob
        (users[0]["id"], users[2]["id"]),  # Alice-Carol
        (users[0]["id"], users[3]["id"]),  # Alice-Dave
        (users[1]["id"], users[2]["id"]),  # Bob-Carol
        (users[2]["id"], users[4]["id"]),  # Carol-Eve
    ]
    friend_ids = []
    for a, b in friendships_to_create:
        status, resp = request("POST", "/friendships/", {"user_id": a, "friend_id": b})
        assert status == 201, f"Friendship failed: {resp}"
        friend_ids.append(resp["id"])
        # Verify user_id < friend_id constraint
        assert resp["user_id"] < resp["friend_id"], "user_id must be < friend_id"
        print(f"  Friendship ID={resp['id']}: {resp['user_id']} <-> {resp['friend_id']}")
    print("  All friend pairs have user_id < friend_id (PASS)\n")

    # ========== 6. Get friend list ==========
    print("=" * 60)
    print("6. Get friend list")
    status, resp = request("GET", f"/users/{users[0]['id']}/friends")
    assert status == 200
    friend_names = [f["nickname"] for f in resp["items"]]
    print(f"  Alice's friends ({resp['total']}): {friend_names}")
    assert resp["total"] == 3, f"Expected 3 friends, got {resp['total']}"
    assert sorted(friend_names) == sorted(["Bob", "Carol", "Dave"])
    print("  PASS\n")

    # ========== 7. Check friendship existence ==========
    print("=" * 60)
    print("7. Check friendship existence")
    status, resp = request("GET", f"/friendships/exists?user_id={users[0]['id']}&other_id={users[1]['id']}")
    assert resp["are_friends"] is True
    print(f"  Alice-Bob are friends: {resp['are_friends']}")

    status, resp = request("GET", f"/friendships/exists?user_id={users[0]['id']}&other_id={users[4]['id']}")
    assert resp["are_friends"] is False
    print(f"  Alice-Eve are friends: {resp['are_friends']}")
    print("  PASS\n")

    # ========== 8. Common friends (INTERSECT) ==========
    print("=" * 60)
    print("8. Common friends (SQL INTERSECT)")
    status, resp = request("GET", f"/users/{users[0]['id']}/common-friends/{users[1]['id']}")
    assert status == 200
    common_names = [f["nickname"] for f in resp["common_friends"]]
    print(f"  Common friends of Alice & Bob ({resp['count']}): {common_names}")
    # Alice friends: Bob, Carol, Dave
    # Bob friends: Alice, Carol
    # Common: Carol (only)
    assert resp['count'] == 1
    assert common_names == ["Carol"]
    print("  PASS\n")

    # ========== 9. Recommendations (CTE + JSON_OVERLAPS) ==========
    print("=" * 60)
    print("9. Friend recommendations (CTE recursive + JSON_OVERLAPS)")
    status, resp = request("GET", f"/users/{users[0]['id']}/recommendations?max_degree=3")
    assert status == 200
    print(f"  Total recommendations: {resp['total']}")
    for i, rec in enumerate(resp["items"]):
        r = rec["reason"]
        print(f"  {i+1}. {rec['user']['nickname']} (score={rec['score']})")
        print(f"     common_friends_cnt: {r['common_friends_count']} {[f['nickname'] for f in r['common_friends']]}")
        print(f"     common_tags: {r['common_tags']}, degree: {r['degree']}")
    # Eve should be recommended (2nd degree via Carol, common tags: movie)
    recommended_names = [r['user']['nickname'] for r in resp['items']]
    assert "Eve" in recommended_names, "Eve should be recommended (2nd degree via Carol)"
    print("  PASS\n")

    # ========== 10. Remove friendship ==========
    print("=" * 60)
    print("10. Remove friendship")
    status, resp = request("DELETE", f"/friendships/{friend_ids[0]}")
    assert status == 200
    print(f"  Result: {resp['message']}")

    # Verify removed
    status, resp = request("GET", f"/users/{users[0]['id']}/friends")
    print(f"  Alice now has {resp['total']} friend(s)")
    assert resp['total'] == 2
    print("  PASS\n")

    # ========== 11. Delete user (cascade) ==========
    print("=" * 60)
    print("11. Delete user (cascade friendships)")
    status, resp = request("DELETE", f"/users/{users[4]['id']}")
    assert status == 200
    print(f"  Delete Eve: {resp['message']}")

    status, resp = request("GET", f"/users/{users[4]['id']}")
    print(f"  Re-query Eve: status={status} (expected 404)")
    assert status == 404
    print("  PASS\n")

    # ========== 12. Error handling tests ==========
    print("=" * 60)
    print("12. Error handling")
    # Duplicate username
    status, resp = request("POST", "/users/", {"username": "alice"})
    print(f"  Duplicate username: status={status}, detail={resp.get('detail')}")
    assert status == 409

    # Add self as friend (Pydantic validation returns 422)
    status, resp = request("POST", "/friendships/", {"user_id": users[0]["id"], "friend_id": users[0]["id"]})
    print(f"  Add self as friend: status={status}")
    assert status in (400, 422)

    # Non-existent user
    status, resp = request("GET", "/users/99999")
    print(f"  Non-existent user: status={status}")
    assert status == 404

    # Invalid username format
    status, resp = request("POST", "/users/", {"username": "ab"})
    print(f"  Invalid username 'ab': status={status}")
    assert status == 422  # Pydantic validation error

    print("  PASS\n")

    print("=" * 60)
    print("All 12 tests PASSED!")


if __name__ == "__main__":
    test()
