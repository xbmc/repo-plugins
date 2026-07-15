#!/usr/bin/env bash
set -euo pipefail

REMOTE_ID=origin

# ---------------------------------------------------------
# Method: ask_next_release_version
# Get current version from addon.xml and ask for next release version
# based on semantic versioning: major / minor / bugfix.
# Enable override of the incremented version.
# ---------------------------------------------------------
ask_next_release_version() {
    local CURRENT_VERSION
    CURRENT_VERSION=$(grep -oP '<addon\b[^>]*\bversion="\K[0-9]+\.[0-9]+\.[0-9]+' addon.xml)

    local MAJOR MINOR BUGFIX
    MAJOR=$(echo "$CURRENT_VERSION" | cut -d. -f1)
    MINOR=$(echo "$CURRENT_VERSION" | cut -d. -f2)
    BUGFIX=$(echo "$CURRENT_VERSION" | cut -d. -f3)

    echo "Current version is $CURRENT_VERSION"
    echo "Choose semantic version bump:"
    echo "  1) major"
    echo "  2) minor"
    echo "  3) bugfix (default)"
    read -p "Select (1/2/3): " CHOICE

    case "$CHOICE" in
        1)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            BUGFIX=0
            ;;
        2)
            MINOR=$((MINOR + 1))
            BUGFIX=0
            ;;
        *)
            BUGFIX=$((BUGFIX + 1))
            ;;
    esac

    local PRESET_VERSION
    PRESET_VERSION="${MAJOR}.${MINOR}.${BUGFIX}"
    # Allow override
    read -p "Enter the next release version (press ENTER to accept $PRESET_VERSION): " VERSION
    VERSION=${VERSION:-$PRESET_VERSION}
    export VERSION
    echo "Next release version is $VERSION"
}

xml_escape() {
    printf "%s" "$1" | sed \
        -e 's/&/\&amp;/g' \
        -e 's/</\&lt;/g' \
        -e 's/>/\&gt;/g' \
        -e 's/"/\&quot;/g'
}

# ---------------------------------------------------------
# Method: ask_next_release_notes
# Asks for multi-line release notes an ensures it is below 1500 characters
# Uses editor directly (nano or $EDITOR)
# ---------------------------------------------------------
ask_next_release_notes() {
    local TMPFILE
    TMPFILE=$(mktemp)

    echo "Enter release notes below 1500 characters :"
    ${EDITOR:-nano} "$TMPFILE"

    while true; do
        NOTES=$(xml_escape "$(cat "$TMPFILE")")
        local NOTES_LENGTH=${#NOTES}

        if [ "$NOTES_LENGTH" -le 1500 ]; then
            # Next release notes are valid, return them
            export NOTES
            return
        fi

        echo "WARNING: Release notes length is $NOTES_LENGTH characters (after escape)."
        echo "It exceeds Kodi's addon.xml <news> field limit of 1500 characters."
        echo "Please edit the release notes to be under 1500 characters."

        ${EDITOR:-nano} "$TMPFILE"
    done
}

# ---------------------------------------------------------
# Method: compute_current_date
# Export DATE as YYYY-M-D (example: 2023-8-14)
# ---------------------------------------------------------
compute_current_date() {
    local YEAR MONTH DAY

    YEAR=$(date +%Y)
    MONTH=$(date +%-m)   # no leading zero
    DAY=$(date +%-d)     # no leading zero

    export DATE="${YEAR}-${MONTH}-${DAY}"
    echo "Current date is $DATE"
}


echo "=== Create a new release for Kodi extension Arte+7 ==="

# ---------------------------------------------------------
# Parse arguments (only --no-push supported)
# ---------------------------------------------------------
NO_PUSH=false
if [ "$1" == "--no-push" ]; then
    NO_PUSH=true
    echo "[NO-PUSH MODE] Commit and tag created locally but NOT pushed"
fi

# ---------------------------------------------------------
# Pre-requisites: Ensure we are on master branch aligned
# with the remote $REMOTE_ID/master branch.
# ---------------------------------------------------------

# Ensure we are inside a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: Need to be inside a git repository."
    exit 1
fi

# Ensure we are on the master branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "master" ]; then
    echo "ERROR: Releases must be created from the master branch."
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Fetch latest remote state
git fetch $REMOTE_ID master

# Compare local and remote master commit hashes
LOCAL_MASTER_COMMIT=$(git rev-parse master)
REMOTE_MASTER_COMMIT=$(git rev-parse $REMOTE_ID/master)
if [[ "$LOCAL_MASTER_COMMIT" != "$REMOTE_MASTER_COMMIT" ]]; then
    echo "ERROR: Local master and $REMOTE_ID/master need to be the same"
    echo "Local: $LOCAL_MASTER_COMMIT and remote: $REMOTE_MASTER_COMMIT"
    exit 1
fi

# ---------------------------------------------------------
# Run commands from extension root directory
# ---------------------------------------------------------
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR/.." || exit 1

# ---------------------------------------------------------
#  Ask for next version and release notes
# ---------------------------------------------------------
compute_current_date
ask_next_release_version
ask_next_release_notes

echo "=== Updating addon.xml version attribute and <news> field ==="
sed -i "s/version=\"[^\"]*\"/version=\"$VERSION\"/" addon.xml
ADDON_NEWS="<news>${VERSION} (${DATE})
${NOTES}</news>"
awk -v news="$ADDON_NEWS" '
    BEGIN { innews=0 }
    /<news>/ { print news; innews=1; next }
    /<\/news>/ { innews=0; next }
    !innews { print }
' addon.xml > addon.xml.tmp
mv addon.xml.tmp addon.xml

echo "=== Updating CHANGELOG.md ==="
{
    echo "## v$VERSION ($DATE)"
    echo ""
    echo "$NOTES"
    echo ""
    cat CHANGELOG.md
} > CHANGELOG.md.tmp
mv CHANGELOG.md.tmp CHANGELOG.md

echo "=== Creating commit ==="
git add addon.xml CHANGELOG.md
git commit -m "Bump version to $VERSION"

echo "=== Creating annotated tag v$VERSION ==="
git tag -a "v$VERSION" -m "$NOTES"
if [ "$NO_PUSH" = true ]; then
    echo "=== [NO-PUSH MODE] Commit and tag created locally but NOT pushed ==="
else
    echo "=== Pushing commit and tag to $REMOTE_ID ==="
    git push $REMOTE_ID --tags
fi

echo "=== Release v$VERSION created successfully ==="
