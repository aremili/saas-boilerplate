"""Tests for the file-based content management system."""

from app.core.content import (
    Content,
    SiteContent,
    LandingContent,
    PricingContent,
    NavigationContent,
    load_content,
    reload_content,
    _load_yaml,
)


class TestContentLoading:
    """Test YAML content loading."""

    def test_load_yaml_returns_dict(self):
        """_load_yaml should return a dictionary."""
        data = _load_yaml("site.yaml")
        assert isinstance(data, dict)

    def test_load_yaml_missing_file_returns_empty(self):
        """_load_yaml should return empty dict for missing files."""
        data = _load_yaml("nonexistent.yaml")
        assert data == {}

    def test_load_content_returns_content_model(self):
        """load_content should return a Content model."""
        content = load_content()
        assert isinstance(content, Content)

    def test_load_content_has_all_sections(self):
        """Content should have all sections populated."""
        content = load_content()
        assert isinstance(content.site, SiteContent)
        assert isinstance(content.landing, LandingContent)
        assert isinstance(content.pricing, PricingContent)
        assert isinstance(content.navigation, NavigationContent)

    def test_reload_content_clears_cache(self):
        """reload_content should clear cache and reload."""
        content1 = load_content()
        content2 = reload_content()
        # Both should be valid Content objects
        assert isinstance(content1, Content)
        assert isinstance(content2, Content)


class TestContentIntegration:
    """Test content values from actual YAML files."""

    def test_site_name_loaded(self):
        """Site name should be loaded from site.yaml."""
        content = reload_content()
        # The name should be a non-empty string
        assert content.site.name
        assert isinstance(content.site.name, str)

    def test_landing_hero_loaded(self):
        """Landing hero content should be loaded."""
        content = reload_content()
        assert content.landing.hero.title
        assert content.landing.hero.highlight

    def test_landing_features_loaded(self):
        """Landing features should be loaded as a list."""
        content = reload_content()
        assert len(content.landing.features.items) > 0
        for feature in content.landing.features.items:
            assert feature.icon
            assert feature.title
            assert feature.description

    def test_pricing_tiers_loaded(self):
        """Pricing tiers should be loaded."""
        content = reload_content()
        assert len(content.pricing.tiers) > 0
        for tier in content.pricing.tiers:
            assert tier.name
            assert tier.price

    def test_pricing_has_featured_tier(self):
        """At least one pricing tier should be featured."""
        content = reload_content()
        featured_tiers = [t for t in content.pricing.tiers if t.featured]
        assert len(featured_tiers) >= 1

    def test_navigation_menu_loaded(self):
        """Navigation menu should be loaded."""
        content = reload_content()
        assert len(content.navigation.main_menu) > 0
        for link in content.navigation.main_menu:
            assert link.text
            assert link.url

    def test_footer_columns_loaded(self):
        """Footer columns should be loaded."""
        content = reload_content()
        assert content.navigation.footer.product.title
        assert len(content.navigation.footer.product.links) > 0
