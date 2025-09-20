#!/usr/bin/env bash
set -euo pipefail

# Use main as default branch name going forward (optional)
git branch -m main 2>/dev/null || true

SQUASH="--squash"   # set to "" to keep full history per repo

REPOS=(
  "https://github.com/IdrisSoyinka/PriorArt_Search.git::main::apps/priorart-search"
  "https://github.com/IdrisSoyinka/pubmed_parser.git::main::data-pipelines/pubmed-parser"
  "https://github.com/IdrisSoyinka/patents-public-data.git::main::data-pipelines/patents-public-data"
  "https://github.com/IdrisSoyinka/wipo-analytics.github.io.git::main::websites/wipo-analytics"
  "https://github.com/IdrisSoyinka/scholar.py.git::main::libs/scholar-py"
  "https://github.com/IdrisSoyinka/uspto-opendata-python.git::main::data-pipelines/uspto-opendata"
  "https://github.com/IdrisSoyinka/epo_download.git::main::data-pipelines/epo-download"
  "https://github.com/IdrisSoyinka/arxiv-sanity-preserver.git::main::data-pipelines/arxiv-sanity-preserver"
  "https://github.com/IdrisSoyinka/patentscope.git::main::data-pipelines/patentscope"
  "https://github.com/IdrisSoyinka/covid-sanity.git::main::data-pipelines/covid-sanity"
)

i=0
for spec in "${REPOS[@]}"; do
  i=$((i+1))
  url="${spec%%::*}"
  rest="${spec#*::}"
  branch="${rest%%::*}"
  prefix="${rest#*::}"
  remote="src$(printf '%02d' "$i")"

  if [ -d "$prefix" ] && [ -n "$(ls -A "$prefix" 2>/dev/null || true)" ]; then
    echo ">>> SKIP: $prefix already exists (looks imported)"
    continue
  fi

  echo ">>> Importing $url ($branch) -> $prefix"
  git remote add "$remote" "$url" 2>/dev/null || true
  git fetch "$remote" --tags

  # Subtree will create the prefix directory itself; do not pre-create it
  git subtree add --prefix="$prefix" "$remote" "$branch" $SQUASH -m "feat: import $(basename "$url" .git)"
done

# .gitignore (idempotent append)
grep -qxF ".venv/" .gitignore 2>/dev/null || cat >> .gitignore <<'GIT'
.venv/
__pycache__/
*.pyc
.env
reports/
GIT

git add .gitignore
git commit -m "chore: ensure .gitignore" || true

echo "All imports attempted."
