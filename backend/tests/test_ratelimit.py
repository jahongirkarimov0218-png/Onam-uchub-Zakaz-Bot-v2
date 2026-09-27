from app.ratelimit import RateLimiter


def test_hit_allows_up_to_limit_then_blocks():
    limiter = RateLimiter(limit=3, window=60)
    assert limiter.hit("user-1") is True
    assert limiter.hit("user-1") is True
    assert limiter.hit("user-1") is True
    assert limiter.hit("user-1") is False


def test_hit_is_independent_per_key():
    limiter = RateLimiter(limit=1, window=60)
    assert limiter.hit("a") is True
    assert limiter.hit("b") is True
    assert limiter.hit("a") is False


def test_hit_allows_again_after_window_slides_past():
    limiter = RateLimiter(limit=1, window=10)
    assert limiter.hit("a", now=1000.0) is True
    assert limiter.hit("a", now=1005.0) is False
    assert limiter.hit("a", now=1011.0) is True
