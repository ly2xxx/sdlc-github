"""Every skill has frontmatter, and every file a skill names beside it exists."""
import json
import re

import pytest

from conftest import ROOT, SKILLS

SKILL_FILES = sorted(SKILLS.glob("*/SKILL.md"))


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_frontmatter_names_the_skill_and_describes_it(path):
    text = path.read_text()
    m = re.match(r"---\nname: (\S+)\ndescription: (.+?)\n---\n", text, flags=re.DOTALL)
    assert m, "SKILL.md must start with name and description frontmatter"
    assert m.group(1) == path.parent.name
    assert 50 < len(m.group(2)) <= 1024


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_files_named_beside_the_skill_exist(path):
    text = path.read_text()
    named = set(re.findall(r"`((?:templates|scripts)/[\w./-]+)`", text))
    missing = [n for n in named if not (path.parent / n).exists()]
    assert missing == []


def test_plugin_and_marketplace_json_parse_and_agree():
    plugin = json.loads((ROOT / "plugins/sdlc-github/.claude-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert plugin["name"] == market["plugins"][0]["name"] == "sdlc-github"
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
