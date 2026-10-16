#!/usr/bin/env bash
#
# Serve the improved CTT site locally for owner review.
#
# Usage:  scripts/serve_preview.sh [port]
# Default port: 8010
#
set -u

PORT="${1:-8010}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${SITE_ROOT}" || exit 1

echo "Serving Chloe's Travelling Tutors from: ${SITE_ROOT}"
echo "Port: ${PORT}"
echo
echo "Open these in a browser:"
echo "  Homepage:              http://localhost:${PORT}/index.html"
echo "  Tutors page (filter):  http://localhost:${PORT}/tutors.html"
echo "  Contact + assessment:  http://localhost:${PORT}/contact.html"
echo "  Blog:                  http://localhost:${PORT}/blog.html"
echo
echo "Press Ctrl+C to stop."
echo

exec python3 -m http.server "${PORT}" --bind 127.0.0.1
