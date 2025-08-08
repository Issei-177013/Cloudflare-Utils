#!/bin/bash

# ================================
# Git Tag Automation Script
# Rules:
# - No tags on feature branches
# - Pre-release tags only on dev branch
# - Stable tags only on main branch
# ================================

VERSION_FILE="version.py"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check version.py exists
if [ ! -f "$VERSION_FILE" ]; then
  echo -e "${RED}❌ File not found: $VERSION_FILE${NC}"
  exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${CYAN}📂 Current branch: ${YELLOW}$CURRENT_BRANCH${NC}"

# Forbid tagging on feature branches
if [[ "$CURRENT_BRANCH" == feature/* ]]; then
  echo -e "${RED}⛔ Tagging not allowed on feature branches.${NC}"
  exit 1
fi

# Extract current version
CURRENT_VERSION=$(grep "__version__" "$VERSION_FILE" | sed -E 's/^.*"([^"]+)".*$/\1/')
if [ -z "$CURRENT_VERSION" ]; then
  echo -e "${RED}❌ Could not extract version from $VERSION_FILE${NC}"
  exit 1
fi

echo -e "${GREEN}📦 Current version in file: $CURRENT_VERSION${NC}"

# Split version numbers
IFS='.' read -r MAJOR MINOR PATCH <<<"${CURRENT_VERSION//[!0-9.]/}"

# Define bump options based on branch
if [[ "$CURRENT_BRANCH" == "main" ]]; then
    echo -e "${CYAN}Select version bump type (Stable releases only):${NC}"
    options=("major" "minor" "patch" "custom")
elif [[ "$CURRENT_BRANCH" == "dev" ]]; then
    echo -e "${CYAN}Select version bump type (Pre-release on dev):${NC}"
    options=("major" "minor" "patch" "alpha" "beta" "rc" "custom")
else
    echo -e "${RED}⛔ Unsupported branch for tagging.${NC}"
    exit 1
fi

select choice in "${options[@]}"; do
    case $choice in
        major)
            ((MAJOR++))
            MINOR=0
            PATCH=0
            NEW_VERSION="$MAJOR.$MINOR.$PATCH"
            break
            ;;
        minor)
            ((MINOR++))
            PATCH=0
            NEW_VERSION="$MAJOR.$MINOR.$PATCH"
            break
            ;;
        patch)
            ((PATCH++))
            NEW_VERSION="$MAJOR.$MINOR.$PATCH"
            break
            ;;
        alpha|beta|rc)
            if [[ "$CURRENT_BRANCH" != "dev" ]]; then
                echo -e "${RED}⛔ Pre-release tags only allowed on dev branch.${NC}"
                exit 1
            fi
            BASE_VERSION="$MAJOR.$MINOR.$PATCH-$choice"
            LAST_TAG=$(git tag --list "v$BASE_VERSION.*" | sort -V | tail -n1)
            if [[ -z "$LAST_TAG" ]]; then
                BUILD_NUM=1
            else
                BUILD_NUM=$(( $(echo "$LAST_TAG" | sed -E "s/.*\.([0-9]+)$/\1/") + 1 ))
            fi
            NEW_VERSION="$MAJOR.$MINOR.$PATCH-$choice.$BUILD_NUM"
            break
            ;;
        custom)
            read -rp "Enter new version manually (without 'v'): " NEW_VERSION
            break
            ;;
        *)
            echo -e "${RED}Invalid choice, try again.${NC}"
            ;;
    esac
done

# Update version.py
sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" "$VERSION_FILE"
echo -e "${GREEN}✅ Updated $VERSION_FILE to version: $NEW_VERSION${NC}"

# Commit version change?
read -rp "Commit version change? (y/n): " commit_confirm
if [[ "$commit_confirm" =~ ^[Yy]$ ]]; then
    git add "$VERSION_FILE"
    git commit -m "Bump version to $NEW_VERSION"
    echo -e "${GREEN}📄 Version change committed.${NC}"
fi

# Create and push tag?
read -rp "Create and push tag 'v$NEW_VERSION'? (y/n): " tag_confirm
if [[ "$tag_confirm" =~ ^[Yy]$ ]]; then
    TAG="v$NEW_VERSION"
    # Check if tag exists
    if git rev-parse "$TAG" >/dev/null 2>&1 || git ls-remote --tags origin | grep -q "refs/tags/$TAG"; then
        echo -e "${YELLOW}⚠️ Tag '$TAG' already exists.${NC}"
        exit 1
    fi
    # Create and push tag
    if git tag -a "$TAG" -m "Release version $NEW_VERSION" && git push origin "$TAG"; then
        echo -e "${GREEN}✅ Tag '$TAG' pushed successfully.${NC}"
    else
        echo -e "${RED}❌ Failed to push tag.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}ℹ️ Tag creation skipped.${NC}"
fi
