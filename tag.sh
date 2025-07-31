#!/bin/bash

# ================================
# Script to create and push git tag based on __version__ in version.py
# ================================

VERSION_FILE="version.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if version file exists
if [ ! -f "$VERSION_FILE" ]; then
  echo -e "${RED}❌ File not found: $VERSION_FILE${NC}"
  exit 1
fi

# Extract __version__ value using grep and sed
VERSION=$(grep "__version__" "$VERSION_FILE" | sed -E 's/^.*"([^"]+)".*$/\1/')

if [ -z "$VERSION" ]; then
  echo -e "${RED}❌ Could not extract version from $VERSION_FILE${NC}"
  exit 1
fi

# Handle possible '+' in version for git tag compatibility
BASE_VERSION=$(echo "$VERSION" | cut -d+ -f1)
TAG="v$BASE_VERSION"

echo -e "${GREEN}📦 Extracted version: $VERSION${NC}"
echo -e "${GREEN}🏷️ Tag to be created: $TAG${NC}"

# Check if tag already exists locally or remotely
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo -e "${YELLOW}⚠️ Tag '$TAG' already exists locally!${NC}"
  exit 1
fi

if git ls-remote --tags origin | grep -q "refs/tags/$TAG"; then
  echo -e "${YELLOW}⚠️ Tag '$TAG' already exists on remote!${NC}"
  exit 1
fi

# Confirm action with user
read -rp "Are you sure you want to create and push tag '$TAG'? (y/n): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo -e "${RED}❌ Operation aborted by user.${NC}"
  exit 1
fi

# Create annotated git tag
if ! git tag -a "$TAG" -m "Release version $VERSION"; then
  echo -e "${RED}❌ Failed to create git tag '$TAG'.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Tag '$TAG' created successfully.${NC}"

# Push tag to remote origin
if ! git push origin "$TAG"; then
  echo -e "${RED}❌ Failed to push tag '$TAG' to remote.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Git tag '$TAG' pushed to remote successfully.${NC}"
