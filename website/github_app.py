from website.config import Config


def install_url() -> str:
    slug = Config.GITHUB_APP_SLUG
    return f"https://github.com/apps/{slug}/installations/new"
