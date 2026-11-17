import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins" / "sdlc-github" / "skills"
sys.path.insert(0, str(SKILLS / "sdlc-dependabot-remediate" / "scripts"))
