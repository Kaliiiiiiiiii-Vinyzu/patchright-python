#!/bin/bash

set -euo pipefail

PYPI_PLAYWRIGHT_URL="${PYPI_PLAYWRIGHT_URL:-https://pypi.org/pypi/playwright/json}"
PYPI_PATCHRIGHT_URL="${PYPI_PATCHRIGHT_URL:-https://pypi.org/pypi/patchright/json}"
NPM_PACKAGE="${NPM_PACKAGE:-patchright-core}"
EVENT_NAME="${GITHUB_EVENT_NAME:-schedule}"
MANUAL_PATCHRIGHT_VERSION="${MANUAL_PATCHRIGHT_VERSION:-}"

set_output() {
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "$1=$2" >> "$GITHUB_OUTPUT"
  else
    echo "$1=$2"
  fi
}

is_stable_version() {
  [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

version_is_greater() {
  local left=$1
  local right=$2
  local left_major left_minor left_patch
  local right_major right_minor right_patch

  IFS='.' read -r left_major left_minor left_patch <<< "$left"
  IFS='.' read -r right_major right_minor right_patch <<< "$right"

  ((10#$left_major > 10#$right_major)) ||
    ((10#$left_major == 10#$right_major && 10#$left_minor > 10#$right_minor)) ||
    ((10#$left_major == 10#$right_major && 10#$left_minor == 10#$right_minor && 10#$left_patch > 10#$right_patch))
}

if [ -n "${PLAYWRIGHT_JSON:-}" ]; then
  playwright_json=$PLAYWRIGHT_JSON
else
  playwright_json=$(curl -fsSL "$PYPI_PLAYWRIGHT_URL")
fi
if [ -n "${PATCHRIGHT_JSON:-}" ]; then
  patchright_json=$PATCHRIGHT_JSON
else
  patchright_json=$(curl -fsSL "$PYPI_PATCHRIGHT_URL")
fi

playwright_version=$(jq -r '
  [.releases | to_entries[]
    | select(.key | test("^[0-9]+\\.[0-9]+\\.[0-9]+$"))
    | select(.value | length > 0)
    | .key]
  | sort_by(split(".") | map(tonumber))
  | last // empty
' <<< "$playwright_json")

if ! is_stable_version "$playwright_version"; then
  echo "::error::Could not resolve the latest stable Playwright Python version from PyPI."
  exit 1
fi

IFS='.' read -r playwright_major playwright_minor playwright_patch <<< "$playwright_version"
playwright_line="$playwright_major.$playwright_minor"
playwright_tag="v$playwright_version"

latest_patchright_version=$(jq -r '
  [.releases | to_entries[]
    | select(.key | test("^[0-9]+\\.[0-9]+\\.[0-9]+$"))
    | select(.value | length > 0)
    | .key]
  | sort_by(split(".") | map(tonumber))
  | last // empty
' <<< "$patchright_json")

last_playwright_version="0.0.0"
if is_stable_version "$latest_patchright_version"; then
  provenance_url=$(jq -r '.info.project_urls["Playwright source"] // empty' <<< "$patchright_json")
  provenance_version=${provenance_url##*/v}
  if is_stable_version "$provenance_version"; then
    last_playwright_version=$provenance_version
  else
    # Packages published before provenance metadata was added were built from
    # the initial Playwright release in their release line.
    IFS='.' read -r legacy_major legacy_minor _ <<< "$latest_patchright_version"
    last_playwright_version="$legacy_major.$legacy_minor.0"
  fi
fi

echo "Latest stable Playwright Python version: $playwright_version"
echo "Latest Patchright PyPI version: ${latest_patchright_version:-none}"
echo "Last processed Playwright Python version: $last_playwright_version"

if [ "$EVENT_NAME" != "workflow_dispatch" ]; then
  if [ "$last_playwright_version" = "$playwright_version" ]; then
    echo "Playwright Python $playwright_version has already been processed."
    set_output proceed false
    exit 0
  fi
  if version_is_greater "$last_playwright_version" "$playwright_version"; then
    echo "::error::The recorded Playwright version $last_playwright_version is newer than the latest PyPI version $playwright_version."
    exit 1
  fi
fi

if [ -n "${PATCHRIGHT_CORE_VERSIONS_JSON:-}" ]; then
  patchright_core_versions=$PATCHRIGHT_CORE_VERSIONS_JSON
else
  patchright_core_versions=$(npm view "$NPM_PACKAGE" versions --json)
fi
patchright_core_version=$(jq -r \
  --arg line "$playwright_line" \
  --argjson minimum_patch "$playwright_patch" '
    [.[]
      | select(test("^[0-9]+\\.[0-9]+\\.[0-9]+$"))
      | select(startswith($line + "."))
      | select((split(".")[2] | tonumber) >= $minimum_patch)]
    | sort_by(split(".") | map(tonumber))
    | last // empty
  ' <<< "$patchright_core_versions")

if ! is_stable_version "$patchright_core_version"; then
  message="No stable $NPM_PACKAGE release in the $playwright_line line has a patch version greater than or equal to Playwright $playwright_version."
  if [ "$EVENT_NAME" = "workflow_dispatch" ]; then
    echo "::error::$message"
    exit 1
  fi
  echo "$message Skipping release."
  set_output proceed false
  exit 0
fi

if ! git ls-remote --exit-code --tags https://github.com/microsoft/playwright-python.git "refs/tags/$playwright_tag" >/dev/null; then
  echo "::error::Playwright Python tag $playwright_tag does not exist."
  exit 1
fi

latest_line_version=$(jq -r --arg line "$playwright_line" '
  [.releases | to_entries[]
    | select(.key | test("^[0-9]+\\.[0-9]+\\.[0-9]+$"))
    | select(.key | startswith($line + "."))
    | select(.value | length > 0)
    | .key]
  | sort_by(split(".") | map(tonumber))
  | last // empty
' <<< "$patchright_json")

if is_stable_version "$latest_line_version"; then
  IFS='.' read -r _ _ latest_patch <<< "$latest_line_version"
  patchright_version="$playwright_line.$((10#$latest_patch + 1))"
else
  patchright_version=$patchright_core_version
fi

if [ "$EVENT_NAME" = "workflow_dispatch" ]; then
  requested_patchright_version=${MANUAL_PATCHRIGHT_VERSION#v}
  if ! is_stable_version "$requested_patchright_version"; then
    echo "::error::The manual Patchright release version must use the format 1.58.0 or v1.58.0."
    exit 1
  fi
  if [ "$requested_patchright_version" != "$patchright_version" ]; then
    echo "::error::The next Patchright PyPI version is $patchright_version, but $requested_patchright_version was requested."
    exit 1
  fi
  patchright_version=$requested_patchright_version
fi

if jq -e --arg version "$patchright_version" '.releases[$version] | length > 0' <<< "$patchright_json" >/dev/null; then
  echo "::error::Patchright $patchright_version already exists on PyPI."
  exit 1
fi

echo "Selected patchright-core npm version: $patchright_core_version"
echo "Next Patchright PyPI version: $patchright_version"

set_output proceed true
set_output playwright_version "$playwright_tag"
set_output patchright_core_version "$patchright_core_version"
set_output patchright_version "$patchright_version"
