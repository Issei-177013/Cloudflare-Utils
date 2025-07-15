#!/bin/bash

VERSION_FILE="version.py"

if [ ! -f "$VERSION_FILE" ]; then
  echo "❌ File not found: $VERSION_FILE"
  exit 1
fi

VERSION=$(grep "__version__" "$VERSION_FILE" | sed -E 's/^.*"([^"]+)".*$/\1/')

if [ -z "$VERSION" ]; then
  echo "❌ Could not extract version from $VERSION_FILE"
  exit 1
fi

TAG="v$VERSION"

echo "📦 Extracted version: $VERSION"
echo "🏷️ Tag to be created: $TAG"

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "⚠️ Tag '$TAG' already exists!"
  exit 1
fi

git tag -a "$TAG" -m "Release version $VERSION"
if [ $? -ne 0 ]; then
  echo "❌ Failed to create tag"
  exit 1
fi

git push origin "$TAG"

echo "✅ Git tag '$TAG' created and pushed successfully."