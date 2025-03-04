#!/usr/bin/python3

import asyncio
import os
import re
import aiohttp
from github_stats import Stats


################################################################################
# Helper Functions
################################################################################

def generate_output_folder() -> None:
    """Create the output folder if it does not already exist"""
    os.makedirs("generated", exist_ok=True)


################################################################################
# Individual Image Generation Functions
################################################################################

async def generate_overview(s: Stats) -> None:
    """Generate an SVG badge with summary statistics"""
    with open("templates/overview.svg", "r", encoding="utf-8") as f:
        output = f.read()

    output = re.sub(r"{{ name }}", await s.name, output)
    output = re.sub(r"{{ stars }}", f"{await s.stargazers:,}", output)
    output = re.sub(r"{{ forks }}", f"{await s.forks:,}", output)
    output = re.sub(r"{{ contributions }}", f"{await s.total_contributions:,}", output)
    
    changed = sum(await s.lines_changed)
    output = re.sub(r"{{ lines_changed }}", f"{changed:,}", output)
    output = re.sub(r"{{ views }}", f"{await s.views:,}", output)
    output = re.sub(r"{{ repos }}", f"{len(await s.all_repos):,}", output)

    generate_output_folder()
    with open("generated/overview.svg", "w", encoding="utf-8") as f:
        f.write(output)


async def generate_languages(s: Stats) -> None:
    """Generate an SVG badge with summary of languages used"""
    with open("templates/languages.svg", "r", encoding="utf-8") as f:
        output = f.read()

    progress = ""
    lang_list = ""
    sorted_languages = sorted(
        (await s.languages).items(),
        reverse=True,
        key=lambda t: t[1].get("size", 0),
    )
    delay_between = 150

    for i, (lang, data) in enumerate(sorted_languages):
        color = data.get("color", "#000000")
        prop = data.get("prop", 0)
        ratio = [0.98, 0.02] if prop <= 50 else [0.99, 0.01]
        if i == len(sorted_languages) - 1:
            ratio = [1, 0]

        progress += (
            f'<span style="background-color: {color};'
            f'width: {(ratio[0] * prop):0.3f}%;'
            f'margin-right: {(ratio[1] * prop):0.3f}%;" '
            f'class="progress-item"></span>'
        )

        lang_list += f"""
<li style="animation-delay: {i * delay_between}ms;">
<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{color};"
viewBox="0 0 16 16" version="1.1" width="16" height="16"><path
d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
<span class="lang">{lang}</span>
<span class="percent">{prop:0.2f}%</span>
</li>
"""

    output = re.sub(r"{{ progress }}", progress, output)
    output = re.sub(r"{{ lang_list }}", lang_list, output)

    generate_output_folder()
    with open("generated/languages.svg", "w", encoding="utf-8") as f:
        f.write(output)


################################################################################
# Main Function
################################################################################

async def main() -> None:
    """Generate all badges"""
    access_token = os.getenv("ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not access_token:
        raise ValueError("A personal access token is required to proceed!")

    user = os.getenv("GITHUB_ACTOR")
    if not user:
        raise ValueError("GITHUB_ACTOR environment variable is missing!")

    exclude_repos = os.getenv("EXCLUDED", "")
    exclude_langs = os.getenv("EXCLUDED_LANGS", "")

    exclude_repos = {x.strip() for x in exclude_repos.split(",") if x.strip()}
    exclude_langs = {x.strip() for x in exclude_langs.split(",") if x.strip()}

    consider_forked_repos = bool(os.getenv("COUNT_STATS_FROM_FORKS", False))

    async with aiohttp.ClientSession() as session:
        s = Stats(
            user, access_token, session,
            exclude_repos=exclude_repos,
            exclude_langs=exclude_langs,
            consider_forked_repos=consider_forked_repos
        )
        await asyncio.gather(generate_languages(s), generate_overview(s))


if __name__ == "__main__":
    asyncio.run(main())
