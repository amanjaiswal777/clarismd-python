#!/usr/bin/env bash
# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0
#
# Regenerate src/clarismd/_generated from the canonical OpenAPI spec.
#
# The hand-written client and resources in src/clarismd/ are NOT touched by
# this script — only the contents of src/clarismd/_generated, which is
# imported by the public surface for typed model coverage. Re-run after any
# v1.yaml change.
#
# Requires `openapi-python-client>=0.21,<0.22` on PATH:
#   pipx install 'openapi-python-client>=0.21,<0.22'
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPEC="${1:-$SDK_ROOT/../packages/openapi/v1.yaml}"

if [ ! -f "$SPEC" ]; then
  echo "openapi spec not found: $SPEC" >&2
  echo "usage: $0 [path-to-spec]" >&2
  exit 1
fi

cd "$SDK_ROOT"

rm -rf src/clarismd/_generated
mkdir -p src/clarismd/_generated

openapi-python-client generate \
  --path "$SPEC" \
  --config codegen-config.yml \
  --output-path src/clarismd/_generated

# Drop a marker so we can recognize the autogen tree at runtime if needed.
touch src/clarismd/_generated/.generated

echo "regenerated src/clarismd/_generated from $SPEC"
