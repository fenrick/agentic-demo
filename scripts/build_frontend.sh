#!/usr/bin/env bash
# Builds the React/Tailwind frontend and copies the static assets for serving.
#
# Usage:
#   ./scripts/build_frontend.sh
#
# The script will:
#   1. Install frontend dependencies
#   2. Build the production bundle
#   3. Copy the built assets to src/web/static

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${REPO_ROOT}/frontend"
npm ci
npm run build

# Copy built assets to backend static directory
mkdir -p "${REPO_ROOT}/src/web/static"
cp -r dist/* "${REPO_ROOT}/src/web/static/"
