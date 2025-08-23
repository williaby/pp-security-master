#!/bin/bash
# Generate requirements.txt with cryptographic hashes for security validation

set -euo pipefail

echo "🔐 Generating requirements.txt with cryptographic hashes..."

# Export requirements with hashes
poetry export \
    --format=requirements.txt \
    --output=requirements.txt \
    --without-hashes \
    --without-urls

echo "✅ Base requirements.txt generated"

# Generate requirements with dev dependencies
poetry export \
    --format=requirements.txt \
    --output=requirements-dev.txt \
    --with=dev \
    --without-hashes \
    --without-urls

echo "✅ Development requirements.txt generated"

# Generate requirements with hashes for production security
poetry export \
    --format=requirements.txt \
    --output=requirements-hashed.txt \
    --with-hashes

echo "✅ Hashed requirements for production generated"

echo "📋 Files generated:"
echo "  - requirements.txt (production)"
echo "  - requirements-dev.txt (development)"
echo "  - requirements-hashed.txt (production with hashes)"