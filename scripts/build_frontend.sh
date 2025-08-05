#!/usr/bin/env bash
# Builds the React/Tailwind frontend and outputs static assets for serving.
#
# Usage:
#   ./scripts/build_frontend.sh
#
# The script will:
#   1. Install Node dependencies
#   2. Build the production bundle in frontend/dist

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${REPO_ROOT}"
npm ci
npm run build
