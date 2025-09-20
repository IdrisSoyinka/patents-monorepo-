#!/usr/bin/env bash
set -euo pipefail

git init
git commit --allow-empty -m "chore: init patents monorepo (core only)"
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

  echo ">>> Importing $url -> $prefix"
  git remote add "$remote" "$url" || true
  git fetch "$remote" --tags
  mkdir -p "$prefix"; git add "$prefix"; git commit --allow-empty -m "chore: prepare $prefix" || true
  git subtree add --prefix="$prefix" "$remote" "$branch" $SQUASH -m "feat: import $(basename "$url" .git)"
done

cat > .gitignore <<'GIT'
.venv/
__pycache__/
*.pyc
.env
reports/
GIT

git add .gitignore
git commit -m "chore: add .gitignore"
echo "Monorepo ready."
