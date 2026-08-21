#!/usr/bin/env bash
#
# Tier 2 of the converter's MOF support: build the snurr-group `mofid` pipeline
# natively, so the CIF reader can run it as a subprocess without Docker.
#
#   ./install_mofid.sh [target-dir]        # default: /opt/mofid
#   MOFID_REF=<sha> ./install_mofid.sh     # build a different upstream commit
#   ./install_mofid.sh --force [dir]       # rebuild an existing installation
#
# Needs: git, make, a C++ compiler, cmake (<4 preferred), and a JRE (Systre).
# Takes roughly 20 minutes and ~500 MB, almost all of it compiling OpenBabel.
#
# IMPORTANT: the build is not relocatable. RUNPATH and the paths in
# mofid/Python/paths.py are absolute, so the directory must keep this exact path
# on the machine that runs the converter. Do not build here and copy elsewhere.
set -euo pipefail

# Upstream commit to build. Same pin as helper/mofid/Dockerfile and the ELN's
# mof_service, so all three produce identical identifiers.
MOFID_REF="${MOFID_REF:-36873683083c7bc62c1da2062df2833adc35b48a}"
MOFID_REPO="${MOFID_REPO:-https://github.com/snurr-group/mofid.git}"
PYTHON="${PYTHON:-python3}"

FORCE=0
TARGET=""
for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) TARGET="$arg" ;;
    esac
done
TARGET="${TARGET:-${MOFID_HOME:-/opt/mofid}}"

log()  { printf '\033[1m==>\033[0m %s\n' "$*"; }
fail() { printf '\033[31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# --- prerequisites ---------------------------------------------------------
log "Checking prerequisites"
for tool in git make cmake "$PYTHON"; do
    command -v "$tool" >/dev/null 2>&1 || fail "'$tool' not found in PATH"
done
command -v java >/dev/null 2>&1 || fail "'java' not found -- mofid needs a JRE for the Systre topology step"

CC="${CC:-gcc}"; CXX="${CXX:-g++}"
command -v "$CC"  >/dev/null 2>&1 || fail "C compiler '$CC' not found (override with CC=...)"
command -v "$CXX" >/dev/null 2>&1 || fail "C++ compiler '$CXX' not found (override with CXX=...)"
export CC CXX

# OpenBabel vendors RapidJSON 1.1.0, which is a hard compile error on GCC 14.
gcc_major="$("$CXX" -dumpversion 2>/dev/null | cut -d. -f1 || echo 0)"
if [ "$gcc_major" -ge 14 ] 2>/dev/null; then
    printf '\033[33mWARNING:\033[0m %s\n' \
        "$CXX is GCC $gcc_major; OpenBabel's vendored RapidJSON fails on GCC >= 14. Retry with CXX=g++-13 if the build breaks."
fi

# CMake 4 removed compatibility with the minimum version that submodule declares.
cmake_major="$(cmake --version | head -1 | sed -E 's/[^0-9]*([0-9]+).*/\1/')"
if [ "$cmake_major" -ge 4 ] 2>/dev/null; then
    log "CMake $cmake_major detected -- setting CMAKE_POLICY_VERSION_MINIMUM=3.5"
    export CMAKE_POLICY_VERSION_MINIMUM=3.5
fi

# --- fetch -----------------------------------------------------------------
if [ -d "$TARGET/bin" ] && [ "$FORCE" -eq 0 ]; then
    log "$TARGET already contains a build; pass --force to rebuild"
else
    if [ "$FORCE" -eq 1 ] && [ -d "$TARGET" ]; then
        log "Removing previous build in $TARGET"
        rm -rf "$TARGET"
    fi
    mkdir -p "$TARGET" || fail "cannot create $TARGET (run with sudo, or pass a writable directory)"
    [ -w "$TARGET" ] || fail "$TARGET is not writable"

    log "Fetching mofid $MOFID_REF"
    # A SHA rather than a ref name is why this is init+fetch and not clone --branch.
    git init -q "$TARGET"
    git -C "$TARGET" fetch -q --depth 1 "$MOFID_REPO" "$MOFID_REF"
    git -C "$TARGET" checkout -q --detach FETCH_HEAD

    log "Building the C++ helpers and the bundled OpenBabel (this takes a while)"
    ( cd "$TARGET" && make init )

    log "Baking absolute paths into mofid/Python/paths.py"
    ( cd "$TARGET" && "$PYTHON" set_paths.py )
fi

# The package directory in the checkout is called 'Python', not 'mofid', so the
# converter cannot put it on PYTHONPATH directly. This link gives it a directory
# that does contain an importable `mofid` package.
log "Creating the PYTHONPATH link"
mkdir -p "$TARGET/pythonpath"
ln -sfn "$TARGET/Python" "$TARGET/pythonpath/mofid"

# --- self-test -------------------------------------------------------------
# A broken install is silent: sbu fails to start, mofid swallows the error and
# reports the same result a non-MOF CIF produces. So verify against a reference
# structure whose topology is known instead of trusting that the build passed.
log "Running the self-test"
PYTHONPATH="$TARGET/pythonpath" "$PYTHON" - "$TARGET" <<'PYTEST'
import os, sys, tempfile
target = sys.argv[1]
from mofid.run_mofid import cif2mofid
reference = os.path.join(target, 'Resources', 'TestCIFs', 'P1-Cu-BTC.cif')
result = cif2mofid(reference, output_path=os.path.join(tempfile.mkdtemp(), 'Output'))
if result.get('topology') != 'tbo':
    sys.exit(f"self-test FAILED: expected topology 'tbo', got {result.get('topology')!r} "
             f"(mofid={result.get('mofid')!r}) -- the installation is not usable")
print(f"  MOFkey: {result['mofkey']}")
PYTEST

cat <<INFO

$(log "Done")
mofid is installed in $TARGET

Point the converter at it by exporting (or adding to its .env):

    MOFID_HOME=$TARGET

Optional:
    MOFID_TIMEOUT=180     # seconds per CIF
    MOFID_ENABLED=false   # switch MOF metadata off entirely

Remember: this build is tied to the path above. Moving or copying $TARGET
breaks it silently -- rerun this script on the target machine instead.
INFO
