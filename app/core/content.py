"""
Content loader module for file-based CMS.

Loads YAML content files and provides them as validated Pydantic models.
Content is cached and can be hot-reloaded in development mode.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


# =============================================================================
# Content Models
# =============================================================================


class SocialLinks(BaseModel):
    """Social media links."""

    twitter: str = ""
    github: str = ""
    linkedin: str = ""
    discord: str = ""


class MetaConfig(BaseModel):
    """SEO and meta configuration."""

    title_suffix: str = ""
    description: str = ""
    keywords: str = ""


class LegalConfig(BaseModel):
    """Legal pages URLs."""

    terms_url: str = "/terms"
    privacy_url: str = "/privacy"
    cookies_url: str = "/cookies"


class ContactConfig(BaseModel):
    """Contact information."""

    email: str = ""
    support_email: str = ""


class SiteContent(BaseModel):
    """Global site configuration."""

    name: str = "SaaS Boilerplate"
    tagline: str = ""
    logo_icon: str = "rocket-takeoff"
    meta: MetaConfig = MetaConfig()
    social: SocialLinks = SocialLinks()
    legal: LegalConfig = LegalConfig()
    contact: ContactConfig = ContactConfig()


class CTAButton(BaseModel):
    """Call-to-action button."""

    text: str
    url: str
    icon: str = ""


class HeroContent(BaseModel):
    """Hero section content."""

    badge: str = ""
    title: str = ""
    highlight: str = ""
    subtitle: str = ""
    cta_primary: CTAButton | None = None
    cta_secondary: CTAButton | None = None
    note: str = ""


class FeatureItem(BaseModel):
    """Single feature item."""

    icon: str
    title: str
    description: str


class FeaturesContent(BaseModel):
    """Features section content."""

    section_badge: str = "Features"
    section_title: str = ""
    section_subtitle: str = ""
    items: list[FeatureItem] = []


class CTAContent(BaseModel):
    """Final CTA section content."""

    title: str = ""
    subtitle: str = ""
    button_text: str = ""
    button_url: str = ""


class LandingContent(BaseModel):
    """Landing page content."""

    hero: HeroContent = HeroContent()
    features: FeaturesContent = FeaturesContent()
    cta: CTAContent = CTAContent()


class PricingTier(BaseModel):
    """Single pricing tier."""

    name: str
    description: str = ""
    price: str
    period: str = ""
    featured: bool = False
    badge: str = ""
    cta_text: str = "Get Started"
    cta_variant: str = "neutral"
    features: list[str] = []


class PricingContent(BaseModel):
    """Pricing section content."""

    section_badge: str = "Pricing"
    section_title: str = ""
    section_subtitle: str = ""
    tiers: list[PricingTier] = []


class NavLink(BaseModel):
    """Navigation link."""

    text: str
    url: str


class HeaderCTA(BaseModel):
    """Header CTA buttons."""

    login: NavLink = NavLink(text="Login", url="/auth/login")
    signup: NavLink = NavLink(text="Get Started", url="/auth/register")


class FooterColumn(BaseModel):
    """Footer link column."""

    title: str
    links: list[NavLink] = []


class FooterContent(BaseModel):
    """Footer links configuration."""

    product: FooterColumn = FooterColumn(title="Product")
    company: FooterColumn = FooterColumn(title="Company")
    legal: FooterColumn = FooterColumn(title="Legal")


class NavigationContent(BaseModel):
    """Navigation configuration."""

    main_menu: list[NavLink] = []
    header_cta: HeaderCTA = HeaderCTA()
    footer: FooterContent = FooterContent()


class Content(BaseModel):
    """
    Aggregated content from all YAML files.

    Access in templates via: {{ content.site.name }}, {{ content.landing.hero.title }}, etc.
    """

    site: SiteContent = SiteContent()
    landing: LandingContent = LandingContent()
    pricing: PricingContent = PricingContent()
    navigation: NavigationContent = NavigationContent()


# =============================================================================
# Content Loader
# =============================================================================

CONTENT_DIR = Path(__file__).parent.parent / "content"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML file from the content directory."""
    filepath = CONTENT_DIR / filename
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_content() -> Content:
    """
    Load and validate all content files.

    Content is cached for performance. Call `reload_content()` to refresh.
    """
    site_data = _load_yaml("site.yaml")
    landing_data = _load_yaml("landing.yaml")
    pricing_data = _load_yaml("pricing.yaml")
    navigation_data = _load_yaml("navigation.yaml")

    return Content(
        site=SiteContent(**site_data) if site_data else SiteContent(),
        landing=LandingContent(**landing_data) if landing_data else LandingContent(),
        pricing=PricingContent(**pricing_data) if pricing_data else PricingContent(),
        navigation=NavigationContent(**navigation_data)
        if navigation_data
        else NavigationContent(),
    )


def reload_content() -> Content:
    """Clear cache and reload all content files."""
    load_content.cache_clear()
    return load_content()


# Pre-load content on module import
content: Content = load_content()
