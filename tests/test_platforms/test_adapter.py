from __future__ import annotations
"""Tests for the platform base and adapters."""

from platforms.base import BasePlatformAdapter, ContentPost, PostResult, PlatformStatus


class TestBasePlatformAdapter:
    """Test suite for BasePlatformAdapter."""

    def test_default_attributes(self):
        class ConcreteAdapter(BasePlatformAdapter):
            platform_name = "test"
            def authenticate(self): return True
            def post(self, content): return PostResult(success=True, platform="test")

        adapter = ConcreteAdapter()
        assert adapter.platform_name == "test"
        assert adapter.rate_limit_per_hour == 999
        assert adapter.supports_media is False
        assert adapter._authenticated is False

    def test_validate_content_empty(self):
        class ConcreteAdapter(BasePlatformAdapter):
            platform_name = "test"
            def authenticate(self): return True
            def post(self, content): return PostResult(success=True, platform="test")

        adapter = ConcreteAdapter()
        is_valid, msg = adapter.validate_content(ContentPost(text=""))
        assert not is_valid
        assert "empty" in msg

    def test_validate_content_ok(self):
        class ConcreteAdapter(BasePlatformAdapter):
            platform_name = "test"
            def authenticate(self): return True
            def post(self, content): return PostResult(success=True, platform="test")

        adapter = ConcreteAdapter()
        is_valid, msg = adapter.validate_content(ContentPost(text="Valid content"))
        assert is_valid

    def test_get_status(self):
        class ConcreteAdapter(BasePlatformAdapter):
            platform_name = "test_platform"
            def authenticate(self): return True
            def post(self, content): return PostResult(success=True, platform="test_platform")

        adapter = ConcreteAdapter()
        status = adapter.get_status()
        assert status.platform == "test_platform"
        assert status.is_authenticated is False

    def test_config_passed_to_adapter(self):
        class ConcreteAdapter(BasePlatformAdapter):
            platform_name = "config_test"
            def authenticate(self): return True
            def post(self, content): return PostResult(success=True, platform="config_test")

        config = {"key": "value", "cookie": "abc"}
        adapter = ConcreteAdapter(config)
        assert adapter.config["key"] == "value"
        assert adapter.config["cookie"] == "abc"


class TestContentPost:
    """Test suite for ContentPost dataclass."""

    def test_default_creation(self):
        post = ContentPost(text="Hello")
        assert post.text == "Hello"
        assert post.title is None
        assert post.media_urls == []
        assert post.hashtags == []
        assert post.reply_to_id is None
        assert post.scheduled_at is None

    def test_full_creation(self):
        from datetime import datetime, timedelta
        later = datetime.now() + timedelta(hours=1)
        post = ContentPost(
            text="Full post",
            title="Title",
            media_urls=["https://example.com/img.png"],
            hashtags=["#AI", "#OpenSource"],
            reply_to_id="12345",
            scheduled_at=later,
        )
        assert post.text == "Full post"
        assert post.title == "Title"
        assert len(post.media_urls) == 1
        assert len(post.hashtags) == 2
