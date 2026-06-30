#!/bin/bash
# SOL Unified Coding Standards Validator
# Version: 3.2.0
# Single source of truth - STRICTER than pre-commit hook
#
# ALL RULES ARE BLOCKING (24 total):
# - File organization (no root folder files)
# - File size (max 450 lines)
# - Security (no hardcoded secrets, dangerous commands)
# - Naming conventions (constants with approved domains, test naming)
# - Code quality (no var keyword, no magic numbers)
# - Logging standards (no print(), use LoggerMixin)
# - Error handling (no silent failures, exception chaining, exc_info=True)
# - Fail-fast (no silent fallbacks, no catch-all exceptions)
# - Performance (no bottleneck patterns, efficient algorithms required)
# - Documentation (no inline comments - use docstrings instead)
# - Type hints (required for all function parameters and returns)
# - Docstrings (required for all public functions and classes)
# - Import order (isort --check-only, stricter than pre-commit)
# - Mypy type checking (--strict mode, stricter than pre-commit)
# - Helper functions (naming conventions, single responsibility, max params)
# - Memory leak prevention (bounded caches, cleanup functions)
# - State key registry (use StateKey enum, no hardcoded state keys)
# - SSOT enforcement (no duplicated logic across steps, extract to shared utils)
#
# Dependencies: isort, mypy (optional but recommended)

set -e

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool information
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Extract common fields directly from INPUT
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Tracking
BLOCKED=false
declare -a VIOLATIONS=()

# ============================================================================
# APPROVED DOMAINS (for sol-next2 reader: backend API + data model)
# ============================================================================
APPROVED_DOMAINS=(
    "API"
    "AUTH"
    "BOOK"
    "CACHE"
    "CATEGORY"
    "CORE"
    "DAILY"
    "DATABASE"
    "DB"
    "DOMAIN"
    "HADITH"
    "HTTP"
    "IDS"
    "INGEST"
    "LOGGING"
    "NARRATOR"
    "OBSERVABILITY"
    "PAGE"
    "PAGINATION"
    "READER"
    "REQUEST"
    "RESPONSE"
    "SCHEMA"
    "SEARCH"
    "SECURITY"
    "SETTINGS"
    "TOC"
    "TRANSLATION"
    "VALIDATION"
    "VERSE"
)

# ============================================================================
# RULE 1: FILE ORGANIZATION - No files in project root
# ============================================================================
validate_file_organization() {
    [ -z "$FILE_PATH" ] && return 0

    local filename=$(basename "$FILE_PATH")
    local dirname=$(dirname "$FILE_PATH")

    # Check if writing to root
    if [[ "$dirname" == "." || "$dirname" == "/" || "$dirname" =~ ^/home/.*/code/sol$ ]]; then
        # Allowed root files
        local allowed_files="package.json|tsconfig.json|.gitignore|.env|.env.example|README.md|LICENSE|CLAUDE.md|pyproject.toml|setup.py|setup.cfg|.python-version|.nvmrc|Makefile|Dockerfile|docker-compose.yml|.dockerignore|.pre-commit-config.yaml|poetry.lock|uv.lock"

        if ! echo "$filename" | grep -qE "^($allowed_files)$"; then
            VIOLATIONS+=("FILE ORGANIZATION: Cannot create '$filename' in project root")
            VIOLATIONS+=("  -> Move to: src/, tests/, docs/, scripts/, or config/")
            BLOCKED=true
        fi
    fi
}

# ============================================================================
# RULE 2: FILE SIZE - Max 600 lines (BLOCKING)
# ============================================================================
validate_file_size() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Skip non-code files
    [[ "$FILE_PATH" != *.py && "$FILE_PATH" != *.js && "$FILE_PATH" != *.ts && "$FILE_PATH" != *.jsx && "$FILE_PATH" != *.tsx ]] && return 0

    # PRE-EDIT CHECK: Block Edit operations on files ≥400 lines if adding content
    if [ "$TOOL_NAME" = "Edit" ]; then
        local old_string=$(echo "$INPUT" | jq -r '.tool_input.old_string // empty')
        local new_string=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')

        if [ -f "$FILE_PATH" ]; then
            local current_lines=$(wc -l < "$FILE_PATH" 2>/dev/null || echo "0")

            local old_lines=$(echo "$old_string" | wc -l)
            local new_lines=$(echo "$new_string" | wc -l)
            local net_change=$((new_lines - old_lines))

            if [ "$current_lines" -ge 400 ] && [ "$net_change" -gt 0 ]; then
                VIOLATIONS+=("FILE SIZE: File already at $current_lines lines (≥400 threshold)")
                VIOLATIONS+=("  -> Cannot add $net_change more lines via Edit operation")
                VIOLATIONS+=("  -> Split into smaller modules first, then apply edits")
                VIOLATIONS+=("  -> Reference: docs/standards/14_coding_standards.md")
                BLOCKED=true
                return
            fi
        fi
    fi

    # FINAL SIZE CHECK: Validate total file size after Write/Edit
    local line_count=$(echo "$CONTENT" | wc -l)

    if [ "$line_count" -gt 450 ]; then
        VIOLATIONS+=("FILE SIZE: File has $line_count lines (max allowed: 450)")
        VIOLATIONS+=("  -> Split into smaller modules")
        VIOLATIONS+=("  -> Extract classes/functions to separate files")
        VIOLATIONS+=("  -> Reference: docs/standards/14_coding_standards.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 3: SECURITY - No hardcoded secrets
# ============================================================================
validate_security() {
    [ -z "$CONTENT" ] && return 0

    # Exempt .env files from hardcoded secret checks (they're meant to store secrets)
    if [[ "$FILE_PATH" =~ \.env(\.example)?$ ]]; then
        return 0
    fi

    # Secret patterns (API keys, passwords, tokens)
    local secret_patterns=(
        'sk-[a-zA-Z0-9]{20,}'                    # OpenAI keys
        'pk_live_[a-zA-Z0-9]+'                   # Stripe live keys
        'pk_test_[a-zA-Z0-9]+'                   # Stripe test keys
        'ghp_[a-zA-Z0-9]{36}'                    # GitHub tokens
        'gho_[a-zA-Z0-9]{36}'                    # GitHub OAuth
        'github_pat_[a-zA-Z0-9_]{22,}'           # GitHub PAT
        'xox[baprs]-[a-zA-Z0-9-]+'               # Slack tokens
        'AKIA[0-9A-Z]{16}'                       # AWS access keys
        'password["\x27]?\s*[:=]\s*["\x27][^"\x27]{8,}' # Password assignments
        'api[_-]?key["\x27]?\s*[:=]\s*["\x27][^"\x27]{16,}' # API key assignments
        'secret["\x27]?\s*[:=]\s*["\x27][^"\x27]{16,}'     # Secret assignments
        'token["\x27]?\s*[:=]\s*["\x27][^"\x27]{16,}'      # Token assignments
    )

    for pattern in "${secret_patterns[@]}"; do
        if echo "$CONTENT" | grep -qiE "$pattern"; then
            # Skip if it's referencing env vars
            if echo "$CONTENT" | grep -q "process.env\|os.environ\|os.getenv\|\.env"; then
                continue
            fi
            VIOLATIONS+=("SECURITY: Potential hardcoded secret detected")
            VIOLATIONS+=("  -> Use environment variables instead")
            VIOLATIONS+=("  -> Store in .env file (add to .gitignore)")
            BLOCKED=true
            break
        fi
    done
}

# ============================================================================
# RULE 4: SECURITY - No dangerous commands
# ============================================================================
validate_dangerous_commands() {
    [ -z "$COMMAND" ] && return 0

    # Dangerous command patterns
    local dangerous_patterns=(
        'rm -rf /'
        'rm -rf /\*'
        'rm -rf \*'
        'dd if=/dev/zero'
        'dd if=/dev/random'
        '> /dev/sd'
        'mkfs\.'
        'curl.*\|.*sh'
        'curl.*\|.*bash'
        'wget.*\|.*sh'
        'wget.*\|.*bash'
        ':(){.*};:'          # Fork bomb
    )

    for pattern in "${dangerous_patterns[@]}"; do
        if echo "$COMMAND" | grep -qE "$pattern"; then
            VIOLATIONS+=("SECURITY: Dangerous command blocked: $pattern")
            VIOLATIONS+=("  -> This command could cause system damage")
            BLOCKED=true
            return
        fi
    done
}

# ============================================================================
# RULE 5: NAMING - Python constants (DOMAIN__CONTEXT__THING pattern)
# Pattern: ^[A-Z][A-Z0-9]*(_[A-Z0-9]+)?(__[A-Z][A-Z0-9]*(_[A-Z0-9]+)?)+$
# ============================================================================
validate_python_constants() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    # Skip test files, conftest, and __init__
    local filename=$(basename "$FILE_PATH")
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py || "$filename" == __init__.py ]] && return 0

    # Only enforce in settings/constants files
    [[ "$FILE_PATH" != *settings* && "$FILE_PATH" != *constants* && "$FILE_PATH" != *config* ]] && return 0

    # Find module-level constants (start of line, uppercase, with = or :)
    local constants=$(echo "$CONTENT" | grep -E "^[A-Z][A-Z0-9_]*[[:space:]]*[:=]" | grep -v "^#" | sed 's/[[:space:]]*[:=].*//')

    if [ -z "$constants" ]; then
        return 0
    fi

    # Validate each constant
    while IFS= read -r const_name; do
        [ -z "$const_name" ] && continue

        # Check if it has double underscores (required for hierarchy)
        if ! echo "$const_name" | grep -q "__"; then
            VIOLATIONS+=("NAMING: Constant '$const_name' missing hierarchical pattern")
            VIOLATIONS+=("  -> Required: DOMAIN__CONTEXT__THING__UNIT__QUALIFIER")
            VIOLATIONS+=("  -> Example: SIGNAL__CONFIDENCE__ISNAD__MIN")
            BLOCKED=true
            continue
        fi

        # Extract domain (first segment before __)
        local domain=$(echo "$const_name" | sed 's/__.*//')

        # Check if domain is approved
        local is_approved=false
        for approved in "${APPROVED_DOMAINS[@]}"; do
            if [[ "$domain" == "$approved" ]]; then
                is_approved=true
                break
            fi
        done

        if [ "$is_approved" = false ]; then
            VIOLATIONS+=("NAMING: Constant '$const_name' uses unapproved domain '$domain'")
            VIOLATIONS+=("  -> Approved domains: ${APPROVED_DOMAINS[*]}")
            VIOLATIONS+=("  -> Reference: docs/standards/11_constants_naming.md")
            BLOCKED=true
        fi
    done <<< "$constants"
}

# ============================================================================
# RULE 6: NAMING - Test functions (test_should_* pattern)
# ============================================================================
validate_test_naming() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check test files
    local filename=$(basename "$FILE_PATH")
    [[ "$filename" != test_* && "$filename" != *_test.py && "$FILE_PATH" != */tests/* ]] && return 0
    [[ "$filename" == conftest.py ]] && return 0

    # Find test functions not following test_should_* pattern
    local bad_tests=$(echo "$CONTENT" | grep -oE "def test_[a-zA-Z0-9_]+" | grep -v "test_should_" | head -3)

    if [ -n "$bad_tests" ]; then
        VIOLATIONS+=("TEST NAMING: Tests must follow 'test_should_<action>_when_<condition>' pattern")
        VIOLATIONS+=("  Found: $(echo "$bad_tests" | head -1)")
        VIOLATIONS+=("  -> Example: test_should_detect_signals_when_input_valid")
        VIOLATIONS+=("  -> Reference: docs/standards/15_test_naming_convention.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 7: CODE QUALITY - No var keyword (JavaScript/TypeScript)
# ============================================================================
validate_no_var() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check JS/TS files
    [[ "$FILE_PATH" != *.js && "$FILE_PATH" != *.ts && "$FILE_PATH" != *.jsx && "$FILE_PATH" != *.tsx ]] && return 0

    # Check for var keyword at start of line (not in comments/strings)
    if echo "$CONTENT" | grep -qE "^[[:space:]]*var "; then
        VIOLATIONS+=("CODE QUALITY: 'var' keyword is prohibited")
        VIOLATIONS+=("  -> Use 'const' for constants, 'let' for variables")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 8: CODE QUALITY - Magic numbers (BLOCKING)
# Allowed: 0, 1, -1, 2 (for halving/doubling)
# Now suggests existing constants to reuse before creating new ones
# ============================================================================
validate_magic_numbers() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check code files
    [[ "$FILE_PATH" != *.py && "$FILE_PATH" != *.js && "$FILE_PATH" != *.ts && "$FILE_PATH" != *.jsx && "$FILE_PATH" != *.tsx ]] && return 0

    # Skip config/settings/constants/cli/scripts files where numbers are expected
    [[ "$FILE_PATH" == *config* || "$FILE_PATH" == *settings* || "$FILE_PATH" == *constants* || "$FILE_PATH" == */cli/* || "$FILE_PATH" == */scripts/* ]] && return 0

    # Skip test files (assertions often need specific numbers)
    local filename=$(basename "$FILE_PATH")
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == *.test.* || "$filename" == *.spec.* ]] && return 0

    # Filter out comments, strings, imports, docstrings, and common patterns
    # Use awk to properly remove multi-line docstrings and comments
    local code_only=$(echo "$CONTENT" | \
        awk '
            /^[[:space:]]*"""/ { in_doc=1; next }
            in_doc && /"""[[:space:]]*$/ { in_doc=0; next }
            in_doc { next }
            /^[[:space:]]*'\'''\'''\''/ { in_doc=1; next }
            in_doc && /'\'''\'''\''[[:space:]]*$/ { in_doc=0; next }
            { gsub(/#.*$/, ""); print }
        ' | \
        # Filter out Tailwind CSS class lines BEFORE removing strings
        grep -vE 'className|class=' | \
        sed "s/'[^']*'//g" | \
        sed 's/"[^"]*"//g' | \
        sed 's/[0-9]\+-[a-zA-Z0-9]//g' | \
        sed 's/Step [0-9]\+//gi' | \
        sed 's/(Step [0-9]\+)//gi' | \
        sed 's/Steps [0-9]\+-[0-9]\+//gi' | \
        sed 's/Step [0-9]\+\/[0-9]\+//gi' | \
        sed 's/Section [0-9]\+//gi' | \
        sed 's/SHA-[0-9]\+//gi' | \
        sed 's/Layer [A-C]//gi' | \
        grep -v "^[[:space:]]*import\|^[[:space:]]*from\|version\|port\|0x\|0b\|0o\|range\|enumerate\|zip" | \
        grep -v '├\|└\|│\|===\|---')

    # Check for magic numbers (3 or greater, or negative numbers other than -1)
    # Pattern: standalone numbers that aren't 0, 1, 2, -1
    # Exclude: Python f-string format specifiers (:05d, :10.2f, etc.) and unit IDs (:atom:00001)
    local magic=$(echo "$code_only" | grep -oE '([^a-zA-Z0-9_]|^)(-?[0-9]+)([^a-zA-Z0-9_.]|$)' | \
        grep -vE '([^0-9]|^)(0|1|2|-1)([^0-9]|$)' | \
        grep -vE ':[0-9]+[dxobXef]|:[0-9]+\.[0-9]+f|:atom:[0-9]+|:[0-9]{2,}[df]' | \
        grep -E '[3-9]|[0-9]{2,}' | \
        head -1)

    if [ -n "$magic" ]; then
        # Extract the numeric value
        local magic_value=$(echo "$magic" | grep -oE '[0-9]+' | head -1)

        # Search for existing constants with this value in src/settings/constants_*.py
        local existing_constants=""
        if [ -n "$magic_value" ]; then
            existing_constants=$(find src/settings -name "constants_*.py" 2>/dev/null | \
                xargs grep -h "Final\[.*\] = $magic_value" 2>/dev/null | \
                grep -oE "[A-Z][A-Z0-9_]*__[A-Z0-9_]+__[A-Z0-9_]+" | \
                head -5)
        fi

        VIOLATIONS+=("MAGIC NUMBER: Numeric literal detected in code")
        VIOLATIONS+=("  Found: $magic")

        if [ -n "$existing_constants" ]; then
            VIOLATIONS+=("  ")
            VIOLATIONS+=("  ⚠️  REUSE EXISTING CONSTANTS (do NOT create new ones):")
            while IFS= read -r const; do
                VIOLATIONS+=("     • $const")
            done <<< "$existing_constants"
            VIOLATIONS+=("  ")
            VIOLATIONS+=("  -> Import and use one of the above constants")
            VIOLATIONS+=("  -> Only create NEW constant if none of these fit semantically")
        else
            VIOLATIONS+=("  -> Extract to named constant in src/settings/constants_*.py")
            VIOLATIONS+=("  -> Use DOMAIN__CONTEXT__THING__UNIT pattern")
        fi

        VIOLATIONS+=("  -> Allowed without constant: 0, 1, 2, -1")
        VIOLATIONS+=("  -> Reference: docs/standards/14_coding_standards.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 9: LOGGING - No print() statements (BLOCKING)
# ============================================================================
validate_no_print() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files and conftest (print allowed for debugging)
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Skip CLI entry points (console output expected)
    [[ "$FILE_PATH" == *cli* && "$filename" == "__main__.py" ]] && return 0

    # Skip walker scripts (use rich Console.print())
    [[ "$FILE_PATH" == *scripts/walker* ]] && return 0

    # Check for print( statements (not in comments or strings)
    local code_only=$(echo "$CONTENT" | \
        sed 's/#.*$//' | \
        sed "s/'''.*'''//g" | \
        sed 's/""".*"""//g')

    # Look for print( at start of line or after whitespace, but exclude console.print()
    local prints=$(echo "$code_only" | grep -E "^[[:space:]]*print\(|[^a-zA-Z_]print\(" | grep -vE "console\.print\(" | head -1)

    if [ -n "$prints" ]; then
        VIOLATIONS+=("LOGGING: print() statement detected")
        VIOLATIONS+=("  Found: $(echo "$prints" | head -1 | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use logger instead: self.logger.info() or logger.info()")
        VIOLATIONS+=("  -> For classes: inherit from LoggerMixin")
        VIOLATIONS+=("  -> For modules: logger = logging.getLogger(__name__)")
        VIOLATIONS+=("  -> Reference: docs/standards/13_logging_standards.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 10: LOGGING - Use LoggerMixin for classes (BLOCKING)
# ============================================================================
validate_logger_mixin() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files, conftest, and __init__
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py || "$filename" == __init__.py ]] && return 0

    # Skip base_logger.py itself
    [[ "$filename" == "base_logger.py" ]] && return 0

    # Check for manual logger creation in classes
    # Pattern: self.logger = logging.getLogger or self._logger = logging.getLogger
    local manual_logger=$(echo "$CONTENT" | grep -E "self\.(logger|_logger)[[:space:]]*=[[:space:]]*logging\.getLogger" | head -1)

    if [ -n "$manual_logger" ]; then
        VIOLATIONS+=("LOGGING: Manual logger creation in class detected")
        VIOLATIONS+=("  Found: $(echo "$manual_logger" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use LoggerMixin instead: class MyClass(LoggerMixin):")
        VIOLATIONS+=("  -> Import: from src.utils.base_logger import LoggerMixin")
        VIOLATIONS+=("  -> Reference: docs/standards/13_logging_standards.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 11: ERROR HANDLING - No silent failures (BLOCKING)
# ============================================================================
validate_no_silent_failures() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    # Pattern 1: except: pass or except Exception: pass
    local silent_except=$(echo "$CONTENT" | grep -E "except[[:space:]]*(Exception)?[[:space:]]*:[[:space:]]*(#.*)?$" | head -1)

    # Check if next non-empty line is just 'pass'
    if [ -n "$silent_except" ]; then
        # Look for except followed by pass on next line
        local except_pass=$(echo "$CONTENT" | grep -A1 -E "except[[:space:]]*(Exception)?[[:space:]]*:" | grep -E "^[[:space:]]*pass[[:space:]]*(#.*)?$" | head -1)

        if [ -n "$except_pass" ]; then
            VIOLATIONS+=("ERROR HANDLING: Silent failure detected (except: pass)")
            VIOLATIONS+=("  -> Never swallow exceptions silently")
            VIOLATIONS+=("  -> Log the error: logger.error(..., exc_info=True)")
            VIOLATIONS+=("  -> Or re-raise: raise")
            VIOLATIONS+=("  -> Reference: docs/standards/04_error_handling.md")
            BLOCKED=true
        fi
    fi
}

# ============================================================================
# RULE 12: ERROR HANDLING - Exception chaining required (BLOCKING)
# ============================================================================
validate_exception_chaining() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Look for raise inside except blocks without 'from e' or 'from None'
    # This is a simplified check - looks for 'raise SomeError(' without 'from'

    # First, find except blocks that have raise statements
    local in_except=false
    local bad_raise=""

    while IFS= read -r line; do
        # Check if we're entering an except block
        if echo "$line" | grep -qE "^[[:space:]]*except.*:"; then
            in_except=true
            continue
        fi

        # Check if we're exiting (new block at same or lower indentation)
        if [ "$in_except" = true ]; then
            if echo "$line" | grep -qE "^[[:space:]]*(def |class |except |else:|finally:|elif |if |try:)"; then
                in_except=false
                continue
            fi

            # Look for raise NewError(...) without 'from'
            if echo "$line" | grep -qE "raise[[:space:]]+[A-Z][a-zA-Z]*Error\(" && ! echo "$line" | grep -qE "from[[:space:]]+(e|err|error|exc|exception|None)"; then
                # This might be a re-raise or a new error - check if it's wrapping
                if ! echo "$line" | grep -qE "^[[:space:]]*raise[[:space:]]*$"; then
                    bad_raise="$line"
                    break
                fi
            fi
        fi
    done <<< "$CONTENT"

    if [ -n "$bad_raise" ]; then
        VIOLATIONS+=("ERROR HANDLING: Exception chaining missing")
        VIOLATIONS+=("  Found: $(echo "$bad_raise" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use: raise NewError(...) from e")
        VIOLATIONS+=("  -> Preserves original stack trace for debugging")
        VIOLATIONS+=("  -> Reference: docs/standards/04_error_handling.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 13: ERROR HANDLING - exc_info=True for logged exceptions (BLOCKING)
# ============================================================================
validate_exc_info() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Look for logger.error in except blocks without exc_info=True
    local in_except=false
    local bad_log=""

    while IFS= read -r line; do
        # Check if we're entering an except block
        if echo "$line" | grep -qE "^[[:space:]]*except.*:"; then
            in_except=true
            continue
        fi

        # Check if we're exiting
        if [ "$in_except" = true ]; then
            if echo "$line" | grep -qE "^[[:space:]]*(def |class |except |else:|finally:|elif |if |try:)" && ! echo "$line" | grep -qE "^[[:space:]]*(else:|finally:)"; then
                in_except=false
                continue
            fi

            # Look for logger.error without exc_info
            if echo "$line" | grep -qE "logger\.error\(" && ! echo "$line" | grep -qE "exc_info[[:space:]]*=[[:space:]]*True"; then
                bad_log="$line"
                break
            fi

            # Also check self.logger.error
            if echo "$line" | grep -qE "self\.logger\.error\(" && ! echo "$line" | grep -qE "exc_info[[:space:]]*=[[:space:]]*True"; then
                bad_log="$line"
                break
            fi
        fi
    done <<< "$CONTENT"

    if [ -n "$bad_log" ]; then
        VIOLATIONS+=("ERROR HANDLING: Missing exc_info=True in exception handler")
        VIOLATIONS+=("  Found: $(echo "$bad_log" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Add exc_info=True: logger.error('...', exc_info=True)")
        VIOLATIONS+=("  -> Captures full stack trace for debugging")
        VIOLATIONS+=("  -> Reference: docs/standards/04_error_handling.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 14: FAIL-FAST - No silent fallbacks (BLOCKING)
# ============================================================================
validate_fail_fast() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Pattern 1: return None in except block without logging
    local in_except=false
    local bad_return=""

    local has_logging=false
    while IFS= read -r line; do
        if echo "$line" | grep -qE "^[[:space:]]*except.*:"; then
            in_except=true
            has_logging=false
            continue
        fi

        if [ "$in_except" = true ]; then
            if echo "$line" | grep -qE "^[[:space:]]*(def |class |except |try:)"; then
                in_except=false
                has_logging=false
                continue
            fi

            if echo "$line" | grep -qE "logger\.(warning|info|error|debug|critical)\("; then
                has_logging=true
            fi

            if echo "$line" | grep -qE "^[[:space:]]*return[[:space:]]+(None|\{\})"; then
                if [ "$has_logging" = false ]; then
                    bad_return="$line"
                    break
                fi
            fi
        fi
    done <<< "$CONTENT"

    if [ -n "$bad_return" ]; then
        VIOLATIONS+=("FAIL-FAST: Silent fallback detected (return None/empty in except)")
        VIOLATIONS+=("  Found: $(echo "$bad_return" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Don't hide failures with fallback returns")
        VIOLATIONS+=("  -> Log the error and re-raise, or handle explicitly")
        VIOLATIONS+=("  -> Reference: docs/standards/04_error_handling.md")
        BLOCKED=true
    fi

    # Pattern 2: Catching Exception and continuing without action
    local catch_all=$(echo "$CONTENT" | grep -E "except[[:space:]]+Exception[[:space:]]*:" | head -1)
    if [ -n "$catch_all" ]; then
        # Check if followed by just continue or pass
        local next_line=$(echo "$CONTENT" | grep -A1 -E "except[[:space:]]+Exception[[:space:]]*:" | tail -1)
        if echo "$next_line" | grep -qE "^[[:space:]]*(continue|pass)[[:space:]]*(#.*)?$"; then
            VIOLATIONS+=("FAIL-FAST: Catching all exceptions and ignoring")
            VIOLATIONS+=("  -> Catch specific exceptions, not Exception")
            VIOLATIONS+=("  -> Log errors before continuing")
            VIOLATIONS+=("  -> Reference: docs/standards/04_error_handling.md")
            BLOCKED=true
        fi
    fi
}

# ============================================================================
# RULE 15: PERFORMANCE - Detect common bottlenecks (BLOCKING)
# ============================================================================
validate_performance() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Pattern 1: String concatenation in loop (use join instead)
    local string_concat=$(echo "$CONTENT" | grep -E "for[[:space:]]+" | head -1)
    if [ -n "$string_concat" ]; then
        # Check if there's += with string in the loop body
        local concat_in_loop=$(echo "$CONTENT" | grep -E "[a-zA-Z_]+[[:space:]]*\+=[[:space:]]*['\"]" | head -1)
        if [ -n "$concat_in_loop" ]; then
            VIOLATIONS+=("PERFORMANCE: String concatenation in loop detected")
            VIOLATIONS+=("  Found: $(echo "$concat_in_loop" | sed 's/^[[:space:]]*//' | cut -c1-60)")
            VIOLATIONS+=("  -> Use ''.join(list) instead of += for strings")
            VIOLATIONS+=("  -> Build list and join at end for O(n) instead of O(n²)")
            BLOCKED=true
        fi
    fi

    # Pattern 2: Repeated regex compilation (should compile once)
    local re_search_count=$(echo "$CONTENT" | grep -c "re\.search\|re\.match\|re\.findall\|re\.sub" || true)
    if [ "$re_search_count" -gt 2 ]; then
        # Check if there's no re.compile
        local has_compile=$(echo "$CONTENT" | grep -c "re\.compile" || true)
        if [ "$has_compile" -eq 0 ]; then
            VIOLATIONS+=("PERFORMANCE: Multiple regex operations without pre-compilation")
            VIOLATIONS+=("  -> Use: pattern = re.compile(r'...') once")
            VIOLATIONS+=("  -> Then: pattern.search(), pattern.match(), etc.")
            VIOLATIONS+=("  -> Pre-compilation is faster for repeated use")
            BLOCKED=true
        fi
    fi

    # Pattern 3: Reading entire file when streaming would work
    local read_all=$(echo "$CONTENT" | grep -E "\.read\(\)[[:space:]]*$|\.readlines\(\)" | head -1)
    if [ -n "$read_all" ]; then
        # Check file size context - if processing large files
        if echo "$CONTENT" | grep -qE "for.*in.*file|process.*file|large|bulk|batch"; then
            VIOLATIONS+=("PERFORMANCE: Reading entire file into memory")
            VIOLATIONS+=("  Found: $(echo "$read_all" | sed 's/^[[:space:]]*//' | cut -c1-60)")
            VIOLATIONS+=("  -> For large files, iterate line by line: for line in file:")
            VIOLATIONS+=("  -> Or use chunked reading for binary files")
            BLOCKED=true
        fi
    fi

    # Pattern 4: List concatenation in loop (use extend)
    local list_concat=$(echo "$CONTENT" | grep -E "=[[:space:]]*[a-zA-Z_]+[[:space:]]*\+[[:space:]]*\[" | head -1)
    if [ -n "$list_concat" ]; then
        VIOLATIONS+=("PERFORMANCE: List concatenation creates new list each time")
        VIOLATIONS+=("  Found: $(echo "$list_concat" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use list.extend() or list.append() instead")
        VIOLATIONS+=("  -> Avoids creating intermediate lists")
        BLOCKED=true
    fi

    # Pattern 5: Using .keys() unnecessarily in dict iteration
    local dict_keys=$(echo "$CONTENT" | grep -E "for[[:space:]]+[a-zA-Z_]+[[:space:]]+in[[:space:]]+[a-zA-Z_]+\.keys\(\)" | head -1)
    if [ -n "$dict_keys" ]; then
        VIOLATIONS+=("PERFORMANCE: Unnecessary .keys() in dict iteration")
        VIOLATIONS+=("  Found: $(echo "$dict_keys" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use: for key in dict: (iterates keys by default)")
        VIOLATIONS+=("  -> .keys() creates unnecessary view object")
        BLOCKED=true
    fi

    # Pattern 6: Nested loops that could be optimized
    local nested_for=$(echo "$CONTENT" | grep -c "^[[:space:]]*for[[:space:]]" || true)
    if [ "$nested_for" -gt 3 ]; then
        local deep_nest=$(echo "$CONTENT" | awk '
            BEGIN { d0=-1; d1=-1 }
            /^[[:space:]]*for[[:space:]]/ {
                match($0, /^[[:space:]]*/); cur = RLENGTH
                if (d0 < 0) { d0 = cur }
                else if (cur > d0 && d1 < 0) { d1 = cur }
                else if (d1 >= 0 && cur > d1) { print NR ":" $0; exit }
                else if (cur <= d0) { d0 = cur; d1 = -1 }
            }
        ' | head -1)
        if [ -n "$deep_nest" ]; then
            VIOLATIONS+=("PERFORMANCE: Deeply nested loops detected (potential O(n³)+)")
            VIOLATIONS+=("  -> Consider using dict lookups for O(1) access")
            VIOLATIONS+=("  -> Or use itertools for efficient iteration")
            VIOLATIONS+=("  -> Review algorithm complexity")
            BLOCKED=true
        fi
    fi
}

# ============================================================================
# RULE 16: DOCUMENTATION - No inline comments (use docstrings instead)
# ============================================================================
validate_no_inline_comments() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files and conftest (comments allowed for test clarity)
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Skip __init__.py files
    [[ "$filename" == __init__.py ]] && return 0

    # Look for inline comments on code lines (code followed by #comment)
    # Pattern: line has code (=, :, ), etc.) followed by # comment
    # Skip: docstring content, special directives, unicode explanations, type annotations
    local inline_comments=$(echo "$CONTENT" | \
        grep -E "^[[:space:]]*(if|elif|else|for|while|def|class|return|yield|raise|import|from|with|try|except|finally|assert|[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*[=:,\)]|[)\]}])[^#]*#" | \
        grep -v "# type:" | \
        grep -v "# noqa" | \
        grep -v "# pragma" | \
        grep -v "# fmt:" | \
        grep -v "# pylint:" | \
        grep -v "# mypy:" | \
        grep -v '"""' | \
        grep -v "'''" | \
        grep -v '\\u[0-9A-Fa-f]' | \
        grep -v ': str.*#' | \
        grep -v ': int.*#' | \
        grep -v ': float.*#' | \
        grep -v ': bool.*#' | \
        grep -v ': list\[' | \
        grep -v ': dict\[' | \
        grep -v ': tuple\[' | \
        grep -v ': Optional\[' | \
        grep -v ': Literal\[' | \
        head -1)

    if [ -n "$inline_comments" ]; then
        VIOLATIONS+=("DOCUMENTATION: Inline comments are prohibited")
        VIOLATIONS+=("  Found: $(echo "$inline_comments" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use docstrings for function/class/module documentation")
        VIOLATIONS+=("  -> Use descriptive variable names instead of comments")
        VIOLATIONS+=("  -> If logic is complex, extract to well-named function")
        VIOLATIONS+=("  -> Allowed: # type:, # noqa, # pragma, # fmt:, # pylint:")
        VIOLATIONS+=("  -> Reference: docs/standards/14_coding_standards.md")
        BLOCKED=true
    fi

    # Check for standalone comment lines (lines starting with #)
    # Skip: shebang, encoding, inside docstrings (heuristic: skip common docstring patterns)
    local standalone_comments=$(echo "$CONTENT" | \
        grep -E "^[[:space:]]*#[^!]" | \
        grep -v "# type:" | \
        grep -v "# noqa" | \
        grep -v "# pragma" | \
        grep -v "# fmt:" | \
        grep -v "# pylint:" | \
        grep -v "# mypy:" | \
        grep -v "^#!" | \
        grep -v "^# -\*-" | \
        grep -v "^# =\+$" | \
        head -1)

    if [ -n "$standalone_comments" ]; then
        VIOLATIONS+=("DOCUMENTATION: Standalone comments are prohibited")
        VIOLATIONS+=("  Found: $(echo "$standalone_comments" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Move explanation to docstring of nearest function/class")
        VIOLATIONS+=("  -> Or extract complex logic to a well-named function")
        VIOLATIONS+=("  -> Code should be self-documenting with clear names")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 17: TYPE HINTS - Required for all function parameters and returns
# ============================================================================
validate_type_hints() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files (type hints optional in tests)
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Skip __init__.py files
    [[ "$filename" == __init__.py ]] && return 0

    # Find function definitions without return type hints
    # Match simple single-line function defs without ->
    local missing_return=$(echo "$CONTENT" | grep -E "^[[:space:]]*def [a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)[[:space:]]*:" | \
        grep -v "\->" | \
        grep -v "def __" | \
        head -1)

    if [ -n "$missing_return" ]; then
        VIOLATIONS+=("TYPE HINTS: Function missing return type annotation")
        VIOLATIONS+=("  Found: $(echo "$missing_return" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Add return type: def func(...) -> ReturnType:")
        VIOLATIONS+=("  -> Use -> None for functions that don't return")
        VIOLATIONS+=("  -> Reference: docs/standards/14_coding_standards.md")
        BLOCKED=true
    fi

    # Find function parameters without type hints
    # Only check simple function signatures (single line, no complex nested types)
    local func_defs=$(echo "$CONTENT" | grep -E "^[[:space:]]*def [a-zA-Z_][a-zA-Z0-9_]*\([^][]*\)" | grep -v "def __")

    while IFS= read -r line; do
        [ -z "$line" ] && continue

        # Extract parameters part (content between first ( and matching ))
        local params=$(echo "$line" | sed 's/.*(\([^)]*\)).*/\1/')

        # Skip if no parameters or only self/cls
        [ -z "$params" ] && continue
        [[ "$params" == "self" || "$params" == "cls" ]] && continue

        # Skip lines with complex type hints containing brackets (Dict[], List[], etc.)
        # These are too complex to parse with simple comma splitting
        if echo "$params" | grep -qE '\[.*,.*\]'; then
            # Has nested brackets with commas - assume properly typed, skip
            continue
        fi

        # Check each parameter (split by comma - safe now since we filtered complex types)
        local has_untyped=false
        IFS=',' read -ra PARAM_ARRAY <<< "$params"
        for param in "${PARAM_ARRAY[@]}"; do
            # Trim whitespace
            param=$(echo "$param" | xargs)

            # Skip self, cls, *args, **kwargs
            [[ "$param" == "self" || "$param" == "cls" ]] && continue
            [[ "$param" == \*args* || "$param" == \*\*kwargs* ]] && continue
            [[ "$param" == \** ]] && continue

            # Skip if it has a type annotation (contains :)
            if ! echo "$param" | grep -q ":"; then
                # Has parameter without type hint
                has_untyped=true
                break
            fi
        done

        if [ "$has_untyped" = true ]; then
            VIOLATIONS+=("TYPE HINTS: Function parameter missing type annotation")
            VIOLATIONS+=("  Found: $(echo "$line" | sed 's/^[[:space:]]*//' | cut -c1-60)")
            VIOLATIONS+=("  -> Add types: def func(param: Type, other: Type) -> Return:")
            VIOLATIONS+=("  -> All parameters except self/cls need type hints")
            BLOCKED=true
            break
        fi
    done <<< "$func_defs"
}

# ============================================================================
# RULE 18: DOCSTRINGS - Required for all public functions and classes
# ============================================================================
validate_docstrings() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Skip __init__.py files
    [[ "$filename" == __init__.py ]] && return 0

    # Check for public functions without docstrings
    # Handle multi-line function signatures
    local in_function=false
    local in_signature=false
    local func_line=""
    local line_num=0

    while IFS= read -r line; do
        line_num=$((line_num + 1))

        # Check for function definition (public = doesn't start with _)
        if echo "$line" | grep -qE "^[[:space:]]*def [a-zA-Z][a-zA-Z0-9_]*\("; then
            func_line="$line"
            # Check if signature ends on this line (has ):)
            if echo "$line" | grep -qE "\)[[:space:]]*(->[^:]*)?:"; then
                in_function=true
                in_signature=false
            else
                in_signature=true
                in_function=false
            fi
            continue
        fi

        # Check for class definition
        if echo "$line" | grep -qE "^[[:space:]]*class [a-zA-Z][a-zA-Z0-9_]*"; then
            in_function=true
            in_signature=false
            func_line="$line"
            continue
        fi

        # If we're in a multi-line signature, check if it ends
        if [ "$in_signature" = true ]; then
            if echo "$line" | grep -qE "\)[[:space:]]*(->[^:]*)?:"; then
                in_signature=false
                in_function=true
            fi
            continue
        fi

        # If we just finished a function/class definition, check for docstring
        if [ "$in_function" = true ]; then
            in_function=false
            # Skip empty lines
            if echo "$line" | grep -qE "^[[:space:]]*$"; then
                continue
            fi
            # Check if this line starts a docstring
            if ! echo "$line" | grep -qE '^[[:space:]]*("""|'"'''"')'; then
                VIOLATIONS+=("DOCSTRINGS: Public function/class missing docstring")
                VIOLATIONS+=("  Found: $(echo "$func_line" | sed 's/^[[:space:]]*//' | cut -c1-60)")
                VIOLATIONS+=("  -> Add docstring immediately after def/class line")
                VIOLATIONS+=("  -> Use Google-style docstrings")
                VIOLATIONS+=("  -> Reference: docs/standards/14_coding_standards.md")
                BLOCKED=true
                break
            fi
        fi
    done <<< "$CONTENT"
}

# ============================================================================
# RULE 19: IMPORT ORDER - isort validation (BLOCKING)
# Stricter than pre-commit: runs on every file edit
# ============================================================================
validate_import_order() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip __init__.py files (import order is often intentional)
    [[ "$filename" == __init__.py ]] && return 0

    # Check if isort is available
    if ! command -v isort &> /dev/null; then
        # isort not installed, skip check but warn
        return 0
    fi

    # Create temp file for isort check
    local temp_file=$(mktemp --suffix=.py)
    echo "$CONTENT" > "$temp_file"

    # Run isort check (--check-only returns non-zero if changes needed)
    # Use project settings if available (look for pyproject.toml or .isort.cfg)
    local settings_arg=""
    local project_root=$(dirname "$(dirname "$FILE_PATH")")
    while [ "$project_root" != "/" ]; do
        if [ -f "$project_root/pyproject.toml" ] || [ -f "$project_root/.isort.cfg" ]; then
            settings_arg="--settings-path $project_root"
            break
        fi
        project_root=$(dirname "$project_root")
    done

    if ! isort --check-only --quiet $settings_arg "$temp_file" 2>/dev/null; then
        # Get the diff to show what's wrong
        local isort_diff=$(isort --diff $settings_arg "$temp_file" 2>/dev/null | head -20)

        VIOLATIONS+=("IMPORT ORDER: Imports are not properly sorted (isort)")
        VIOLATIONS+=("  -> Run: isort $FILE_PATH")
        VIOLATIONS+=("  -> Or configure editor to auto-sort on save")
        if [ -n "$isort_diff" ]; then
            VIOLATIONS+=("  Diff preview:")
            while IFS= read -r line; do
                VIOLATIONS+=("    $line")
            done <<< "$(echo "$isort_diff" | head -10)"
        fi
        BLOCKED=true
    fi

    # Cleanup
    rm -f "$temp_file"
}

# ============================================================================
# RULE 20: MYPY TYPE CHECKING - Strict mode (BLOCKING)
# Stricter than pre-commit: uses --strict flag
# NOTE: Only runs on Write operations (full file writes), not Edit operations
# ============================================================================
validate_mypy_types() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only run mypy on Write operations (full file content)
    # Edit operations only provide the replacement string fragment, not valid Python
    [ "$TOOL_NAME" != "Write" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files (type hints less strict in tests)
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Skip __init__.py files
    [[ "$filename" == __init__.py ]] && return 0

    # Skip files with relative imports that go up multiple levels (can't be checked in isolation)
    # Pattern: from ... (3+ dots) - these require project context
    if echo "$CONTENT" | grep -qE "^from \.\.\. import|^from \.\.\."; then
        return 0
    fi

    # Check if mypy is available
    if ! command -v mypy &> /dev/null; then
        # mypy not installed, skip check
        return 0
    fi

    # Create temp file for mypy check
    local temp_file=$(mktemp --suffix=.py)
    echo "$CONTENT" > "$temp_file"

    # Run mypy with strict settings
    # --no-error-summary suppresses the summary line
    # --no-color for clean output
    local mypy_output=$(mypy "$temp_file" \
        --strict \
        --no-error-summary \
        --no-color \
        --ignore-missing-imports \
        2>/dev/null | head -20)

    local file_errors=$(echo "$mypy_output" | grep "^$temp_file:" | head -10)
    if [ -n "$file_errors" ]; then
        VIOLATIONS+=("MYPY TYPE CHECK: Type errors detected (strict mode)")
        VIOLATIONS+=("  File: $FILE_PATH")
        VIOLATIONS+=("  -> Fix all type annotations to satisfy mypy --strict")
        VIOLATIONS+=("  Errors:")
        while IFS= read -r line; do
            local cleaned_line=$(echo "$line" | sed "s|$temp_file|$FILE_PATH|g")
            VIOLATIONS+=("    $cleaned_line")
        done <<< "$file_errors"
        BLOCKED=true
    fi

    # Cleanup
    rm -f "$temp_file"
}

# ============================================================================
# RULE 21: HELPER FUNCTIONS - Naming and design conventions
# Reference: config/helper_function_conventions.yaml
# ============================================================================
validate_helper_functions() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files and conftest
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Skip __init__.py files
    [[ "$filename" == __init__.py ]] && return 0

    # -------------------------------------------------------------------------
    # Check 1: Prohibited/vague function names
    # -------------------------------------------------------------------------
    local prohibited_names="helper|do_stuff|do_things|process|handle|execute|run|perform|util|utils|misc|common|general|wrapper|inner|temp|tmp|foo|bar|baz|func|function"

    # Find function definitions with prohibited names (exact match after def)
    local vague_funcs=$(echo "$CONTENT" | grep -oE "def (_?)($prohibited_names)[[:space:]]*\(" | head -1)

    if [ -n "$vague_funcs" ]; then
        VIOLATIONS+=("HELPER FUNCTION: Vague/prohibited function name detected")
        VIOLATIONS+=("  Found: $(echo "$vague_funcs" | sed 's/^[[:space:]]*//')")
        VIOLATIONS+=("  -> Function names should describe WHAT they do, not THAT they help")
        VIOLATIONS+=("  -> Good: parse_user_id(), normalize_email(), validate_payload()")
        VIOLATIONS+=("  -> Bad: helper(), do_stuff(), process(), utils()")
        VIOLATIONS+=("  -> Reference: config/helper_function_conventions.yaml")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 2: Functions doing too much (multiple actions in name)
    # -------------------------------------------------------------------------
    local overloaded_funcs=$(echo "$CONTENT" | grep -oE "def [a-zA-Z_]+(_and_|_then_|_or_)[a-zA-Z_]+\(" | head -1)

    if [ -n "$overloaded_funcs" ]; then
        VIOLATIONS+=("HELPER FUNCTION: Function name suggests multiple responsibilities")
        VIOLATIONS+=("  Found: $(echo "$overloaded_funcs" | sed 's/^[[:space:]]*//')")
        VIOLATIONS+=("  -> Split into separate functions, each doing ONE thing")
        VIOLATIONS+=("  -> Example: 'parse_and_validate' -> 'parse_input()' + 'validate_input()'")
        VIOLATIONS+=("  -> Helpers should be composable building blocks, not mini-systems")
        VIOLATIONS+=("  -> Reference: config/helper_function_conventions.yaml")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 3: Very long function names (likely doing too much)
    # -------------------------------------------------------------------------
    local long_names=$(echo "$CONTENT" | grep -oE "def [a-zA-Z_]{41,}\(" | head -1)

    if [ -n "$long_names" ]; then
        VIOLATIONS+=("HELPER FUNCTION: Function name too long (>40 chars)")
        VIOLATIONS+=("  Found: $(echo "$long_names" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Long names often indicate too many responsibilities")
        VIOLATIONS+=("  -> Consider splitting into smaller, focused functions")
        VIOLATIONS+=("  -> Reference: config/helper_function_conventions.yaml")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 4: Too many parameters (helper doing too much)
    # Only check simple single-line function defs
    # -------------------------------------------------------------------------
    local func_defs=$(echo "$CONTENT" | grep -E "^[[:space:]]*def [a-zA-Z_][a-zA-Z0-9_]*\([^)]+\)[[:space:]]*(->[^:]*)?:")

    while IFS= read -r line; do
        [ -z "$line" ] && continue

        # Extract parameters part
        local params=$(echo "$line" | sed 's/.*(\([^)]*\)).*/\1/')

        # Skip if no parameters
        [ -z "$params" ] && continue

        # Count parameters (split by comma, but skip complex nested types)
        if echo "$params" | grep -qE '\[.*,.*\]'; then
            continue
        fi

        # Count commas to estimate parameter count (rough heuristic)
        local comma_count=$(echo "$params" | grep -o "," | wc -l)
        local param_count=$((comma_count + 1))

        # Subtract 1 if self/cls is present
        if echo "$params" | grep -qE "^[[:space:]]*(self|cls)[[:space:]]*,"; then
            param_count=$((param_count - 1))
        fi

        if [ "$param_count" -gt 5 ]; then
            VIOLATIONS+=("HELPER FUNCTION: Too many parameters ($param_count > 5)")
            VIOLATIONS+=("  Found: $(echo "$line" | sed 's/^[[:space:]]*//' | cut -c1-70)")
            VIOLATIONS+=("  -> Consider using a dataclass or TypedDict for grouped parameters")
            VIOLATIONS+=("  -> Or split the function into smaller pieces")
            VIOLATIONS+=("  -> Reference: config/helper_function_conventions.yaml")
            BLOCKED=true
            break
        fi
    done <<< "$func_defs"

    # -------------------------------------------------------------------------
    # Check 5: Internal helpers without underscore prefix
    # Look for functions that are only called within the same module
    # This is a heuristic: functions not in __all__ and not starting with _
    # -------------------------------------------------------------------------
    # Skip this check if file has __all__ defined (explicit API)
    if echo "$CONTENT" | grep -qE "^__all__[[:space:]]*="; then
        return 0
    fi

    # Check for functions that look like they should be private
    # Pattern: functions that are called only as internal utilities (called with _-like patterns)
    # This is intentionally conservative to avoid false positives
}

# ============================================================================
# RULE 22: MEMORY LEAK PREVENTION - Bounded caches and cleanup functions
# Reference: docs/standards/memory_management.md
# ============================================================================
validate_memory_leak_prevention() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files
    [[ "$FILE_PATH" != *.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files and conftest
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # Skip settings/constants files (config, not runtime)
    [[ "$FILE_PATH" == *settings/constants_*.py ]] && return 0

    # -------------------------------------------------------------------------
    # Check 1: @lru_cache without maxsize parameter
    # -------------------------------------------------------------------------
    # Pattern: @lru_cache or @lru_cache() without maxsize=
    local unbounded_lru=$(echo "$CONTENT" | grep -E "^[[:space:]]*@lru_cache[[:space:]]*$|^[[:space:]]*@lru_cache\(\)[[:space:]]*$" | head -1)

    if [ -n "$unbounded_lru" ]; then
        VIOLATIONS+=("MEMORY LEAK: @lru_cache without maxsize parameter")
        VIOLATIONS+=("  Found: $(echo "$unbounded_lru" | sed 's/^[[:space:]]*//')")
        VIOLATIONS+=("  -> Use: @lru_cache(maxsize=N) where N is a reasonable bound")
        VIOLATIONS+=("  -> Without maxsize, cache grows unboundedly")
        VIOLATIONS+=("  -> Example: @lru_cache(maxsize=100)")
        VIOLATIONS+=("  -> Reference: docs/standards/memory_management.md")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 2: @cache decorator (functools.cache has no maxsize control)
    # -------------------------------------------------------------------------
    local functools_cache=$(echo "$CONTENT" | grep -E "^[[:space:]]*@cache[[:space:]]*$" | head -1)

    if [ -n "$functools_cache" ]; then
        VIOLATIONS+=("MEMORY LEAK: @cache decorator has no size limit")
        VIOLATIONS+=("  Found: $(echo "$functools_cache" | sed 's/^[[:space:]]*//')")
        VIOLATIONS+=("  -> Use @lru_cache(maxsize=N) instead of @cache")
        VIOLATIONS+=("  -> functools.cache is equivalent to lru_cache(maxsize=None)")
        VIOLATIONS+=("  -> This causes unbounded memory growth")
        VIOLATIONS+=("  -> Reference: docs/standards/memory_management.md")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 3: Unbounded module-level cache dicts without clear function
    # -------------------------------------------------------------------------
    # Pattern: module-level dict named *CACHE* or *_cache* = {} or : dict
    local cache_patterns=$(echo "$CONTENT" | grep -nE "^[A-Z_]*CACHE[A-Z_]*[[:space:]]*[:=]|^_[a-z_]*cache[a-z_]*[[:space:]]*[:=]" | grep -E "dict|= *\{\}" | head -3)

    if [ -n "$cache_patterns" ]; then
        # Check if there's a corresponding clear/reset function in the file
        local has_clear=false

        # Look for clear_cache, reset_cache, clear_*, or *.clear() patterns
        if echo "$CONTENT" | grep -qE "def (clear_|reset_)[a-z_]*cache|def clear_cache|\.clear\(\)"; then
            has_clear=true
        fi

        if [ "$has_clear" = false ]; then
            while IFS= read -r cache_line; do
                [ -z "$cache_line" ] && continue
                local cache_name=$(echo "$cache_line" | sed 's/^[0-9]*://' | sed 's/[[:space:]]*[:=].*//')

                VIOLATIONS+=("MEMORY LEAK: Unbounded module-level cache without cleanup")
                VIOLATIONS+=("  Found: $(echo "$cache_line" | sed 's/^[0-9]*://' | sed 's/^[[:space:]]*//' | cut -c1-60)")
                VIOLATIONS+=("  -> Add a clear function: def clear_${cache_name,,}(): ${cache_name}.clear()")
                VIOLATIONS+=("  -> Or use @lru_cache(maxsize=N) instead of manual dict cache")
                VIOLATIONS+=("  -> Reference: docs/standards/memory_management.md")
                BLOCKED=true
                break
            done <<< "$cache_patterns"
        fi
    fi

    # -------------------------------------------------------------------------
    # Check 4: Global singleton pattern without cleanup function
    # -------------------------------------------------------------------------
    # Pattern: _var: Optional[...] = None at module level with global _var in getter
    local singleton_vars=$(echo "$CONTENT" | grep -oE "^_[a-z_]+[[:space:]]*:[[:space:]]*Optional\[" | sed 's/[[:space:]]*:.*//')

    if [ -n "$singleton_vars" ]; then
        while IFS= read -r var_name; do
            [ -z "$var_name" ] && continue

            # Check if there's a global statement for this variable (getter function)
            if echo "$CONTENT" | grep -qE "global[[:space:]]+$var_name"; then
                # Check if there's a reset/clear/close function for this singleton
                local cleanup_pattern="def (reset_|clear_|close_).*$var_name|def .*reset.*:|def .*close.*:|def .*cleanup.*:"

                # More specific: look for function that sets the singleton to None
                local has_cleanup=false
                if echo "$CONTENT" | grep -qE "def (reset|clear|close)_"; then
                    # Check if any cleanup function references this variable
                    if echo "$CONTENT" | grep -A5 -E "def (reset|clear|close)_" | grep -qE "$var_name[[:space:]]*=[[:space:]]*None"; then
                        has_cleanup=true
                    fi
                fi

                if [ "$has_cleanup" = false ]; then
                    VIOLATIONS+=("MEMORY LEAK: Global singleton without cleanup function")
                    VIOLATIONS+=("  Found: $var_name (with global statement in getter)")
                    VIOLATIONS+=("  -> Add cleanup: def reset_${var_name#_}(): global $var_name; $var_name = None")
                    VIOLATIONS+=("  -> Or def close_${var_name#_}() for resources that need closing")
                    VIOLATIONS+=("  -> Singletons without cleanup prevent garbage collection")
                    VIOLATIONS+=("  -> Reference: docs/standards/memory_management.md")
                    BLOCKED=true
                    break
                fi
            fi
        done <<< "$singleton_vars"
    fi
}

# ============================================================================
# RULE 23: STATE KEY REGISTRY - Use StateKey enum (BLOCKING)
# Reference: docs/dev-guides/STATE-REGISTRY-DESIGN.md
# ============================================================================
validate_state_key_usage() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files in src/ (not settings/constants files)
    [[ "$FILE_PATH" != *.py ]] && return 0
    [[ "$FILE_PATH" != */src/* ]] && return 0
    [[ "$FILE_PATH" == *settings/constants_pipeline_state.py ]] && return 0
    [[ "$FILE_PATH" == *core/pipeline_contracts.py ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files and __init__
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py || "$filename" == __init__.py ]] && return 0

    # -------------------------------------------------------------------------
    # Check 1: Hardcoded state keys with state["key"] pattern
    # -------------------------------------------------------------------------
    local hardcoded_state=$(echo "$CONTENT" | grep -E 'state\["[a-z_]+"\]' | head -1)

    if [ -n "$hardcoded_state" ]; then
        VIOLATIONS+=("STATE KEY REGISTRY: Hardcoded state key detected")
        VIOLATIONS+=("  Found: $(echo "$hardcoded_state" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Import StateKey enum: from src.settings.constants_pipeline_state import StateKey")
        VIOLATIONS+=("  -> Use: state[StateKey.SPANS.value] not state['spans']")
        VIOLATIONS+=("  -> Reference: docs/dev-guides/STATE-REGISTRY-DESIGN.md")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 2: Hardcoded state.get("key") pattern
    # -------------------------------------------------------------------------
    local hardcoded_get=$(echo "$CONTENT" | grep -E 'state\.get\("[a-z_]+"\)' | head -1)

    if [ -n "$hardcoded_get" ]; then
        VIOLATIONS+=("STATE KEY REGISTRY: Hardcoded state.get() detected")
        VIOLATIONS+=("  Found: $(echo "$hardcoded_get" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Import StateKey enum: from src.settings.constants_pipeline_state import StateKey")
        VIOLATIONS+=("  -> Use: state.get(StateKey.SPANS.value) not state.get('spans')")
        VIOLATIONS+=("  -> Reference: docs/dev-guides/STATE-REGISTRY-DESIGN.md")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 3: Deprecated state keys (legacy naming)
    # -------------------------------------------------------------------------
    local deprecated_keys="behaviors|signals|hierarchy"
    local deprecated_usage=$(echo "$CONTENT" | grep -E "state\[\"($deprecated_keys)\"\]" | head -1)

    if [ -n "$deprecated_usage" ]; then
        VIOLATIONS+=("STATE KEY REGISTRY: Deprecated state key detected")
        VIOLATIONS+=("  Found: $(echo "$deprecated_usage" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> 'behaviors' → StateKey.SPANS_WITH_BEHAVIORS")
        VIOLATIONS+=("  -> 'signals' → StateKey.SPANS_WITH_SIGNALS")
        VIOLATIONS+=("  -> 'hierarchy' → StateKey.HIERARCHY_NODES or StateKey.SPANS_WITH_HIERARCHY_PATHS")
        VIOLATIONS+=("  -> Reference: docs/dev-guides/NAMING-CONVENTIONS.md")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 4: camelCase in state keys (should be snake_case)
    # -------------------------------------------------------------------------
    local camel_case=$(echo "$CONTENT" | grep -E 'state\["[a-z]+[A-Z]' | head -1)

    if [ -n "$camel_case" ]; then
        VIOLATIONS+=("STATE KEY REGISTRY: State keys must use snake_case")
        VIOLATIONS+=("  Found: $(echo "$camel_case" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use snake_case: 'atomic_units' not 'atomicUnits'")
        VIOLATIONS+=("  -> Reference: docs/dev-guides/NAMING-CONVENTIONS.md")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 5: Wrong enrichment pattern (_enriched instead of _with_)
    # -------------------------------------------------------------------------
    local wrong_enrichment=$(echo "$CONTENT" | grep -E 'state\["[a-z_]*_enriched[a-z_]*"\]' | head -1)

    if [ -n "$wrong_enrichment" ]; then
        VIOLATIONS+=("STATE KEY REGISTRY: Use '_with_' pattern for augmented collections")
        VIOLATIONS+=("  Found: $(echo "$wrong_enrichment" | sed 's/^[[:space:]]*//' | cut -c1-60)")
        VIOLATIONS+=("  -> Use: 'spans_with_signals' not 'spans_enriched' or 'enriched_spans'")
        VIOLATIONS+=("  -> Pattern: <collection>_with_<addition>")
        VIOLATIONS+=("  -> Reference: docs/dev-guides/NAMING-CONVENTIONS.md")
        BLOCKED=true
    fi
}

# ============================================================================
# RULE 24: SSOT - No Duplicated Logic (BLOCKING)
# Reference: Analysis of steps 9-15 duplication patterns
# ============================================================================
validate_ssot_no_duplication() {
    [ -z "$CONTENT" ] && return 0
    [ -z "$FILE_PATH" ] && return 0

    # Only check Python files in src/steps (not utils or shared)
    [[ "$FILE_PATH" != *.py ]] && return 0
    [[ "$FILE_PATH" != */src/steps/* ]] && return 0

    local filename=$(basename "$FILE_PATH")

    # Skip test files
    [[ "$filename" == test_* || "$filename" == *_test.py || "$filename" == conftest.py ]] && return 0

    # -------------------------------------------------------------------------
    # Check 1: Validation functions that should be in shared utils
    # Pattern: validate_step{N}_input* functions with field checking loops
    # -------------------------------------------------------------------------
    local validation_funcs=$(echo "$CONTENT" | grep -E "def validate_step[0-9]+_(input|output)" | head -1)

    if [ -n "$validation_funcs" ]; then
        # Check if it uses the generic validation pattern
        local has_required_fields=$(echo "$CONTENT" | grep -E "required_fields[[:space:]]*=[[:space:]]*\{" | head -1)
        local has_field_loop=$(echo "$CONTENT" | grep -E "for field_name.*in required_fields" | head -1)

        if [ -n "$has_required_fields" ] && [ -n "$has_field_loop" ]; then
            VIOLATIONS+=("SSOT: Step-specific validation using generic pattern")
            VIOLATIONS+=("  Found: $(echo "$validation_funcs" | sed 's/^[[:space:]]*//')")
            VIOLATIONS+=("  -> This validation pattern is duplicated across steps 9, 11, 13, 14")
            VIOLATIONS+=("  -> Extract to: src/utils/validation_common.py")
            VIOLATIONS+=("  -> Use: validate_required_fields(obj, schema)")
            VIOLATIONS+=("  -> Reference: Analysis of SSOT violations in steps 9-15")
            BLOCKED=true
        fi
    fi

    # -------------------------------------------------------------------------
    # Check 2: Lookup builder functions (_build_*_lookup pattern)
    # -------------------------------------------------------------------------
    local lookup_builders=$(echo "$CONTENT" | grep -oE "def _build_[a-z_]+_lookup\(" | head -2)

    if [ -n "$lookup_builders" ]; then
        local count=$(echo "$lookup_builders" | wc -l)
        if [ "$count" -gt 1 ]; then
            VIOLATIONS+=("SSOT: Multiple lookup builder functions in same file")
            VIOLATIONS+=("  Found: $(echo "$lookup_builders" | tr '\n' ', ')")
            VIOLATIONS+=("  -> These follow the same pattern: dict[key] = value")
            VIOLATIONS+=("  -> Extract to: src/utils/lookup_builders.py")
            VIOLATIONS+=("  -> Use: build_lookup(items, key_field, group_by=False)")
            VIOLATIONS+=("  -> Reference: Steps 9 and 12 have duplicated lookup patterns")
            BLOCKED=true
        fi
    fi

    # -------------------------------------------------------------------------
    # Check 3: Fingerprint computation functions
    # -------------------------------------------------------------------------
    local fingerprint_funcs=$(echo "$CONTENT" | grep -E "def.*compute.*fingerprint|hashlib\.sha256" | head -1)

    if [ -n "$fingerprint_funcs" ] && [[ "$FILE_PATH" != */step_09/* ]]; then
        # Only step 9 should have fingerprint implementation
        VIOLATIONS+=("SSOT: Fingerprint computation outside step_09")
        VIOLATIONS+=("  Found in: $FILE_PATH")
        VIOLATIONS+=("  -> Step 9 is the SSOT for fingerprint computation")
        VIOLATIONS+=("  -> Import from: src.steps.step_09.helpers.compute_fingerprint")
        VIOLATIONS+=("  -> Don't reimplement this logic elsewhere")
        VIOLATIONS+=("  -> Reference: Step 9 and 14 have duplicate fingerprinting")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 4: JSON serialization patterns (should use shared utility)
    # -------------------------------------------------------------------------
    local jsonl_pattern=$(echo "$CONTENT" | grep -E "with open.*'w'.*as f:" | grep -A3 "json.dumps.*asdict" | head -1)

    if [ -n "$jsonl_pattern" ]; then
        # Check if this is the exact pattern: for item in items: json.dumps(asdict(item))
        local has_asdict_loop=$(echo "$CONTENT" | grep -A2 "for .* in .*:" | grep "json.dumps.*asdict" | head -1)

        if [ -n "$has_asdict_loop" ]; then
            VIOLATIONS+=("SSOT: JSONL serialization pattern duplicated")
            VIOLATIONS+=("  Found in: $FILE_PATH")
            VIOLATIONS+=("  -> This pattern is repeated in steps 9, 11, 13")
            VIOLATIONS+=("  -> Extract to: src/utils/io_utils.py")
            VIOLATIONS+=("  -> Use: write_jsonl_from_dataclasses(path, items)")
            VIOLATIONS+=("  -> Reference: JSON serialization SSOT violation")
            BLOCKED=true
        fi
    fi

    # -------------------------------------------------------------------------
    # Check 5: Step-specific exception classes (should use shared hierarchy)
    # -------------------------------------------------------------------------
    local exception_classes=$(echo "$CONTENT" | grep -oE "class Step[0-9]+(Input|Output|Contract)Error" | head -1)

    if [ -n "$exception_classes" ]; then
        VIOLATIONS+=("SSOT: Step-specific exception class detected")
        VIOLATIONS+=("  Found: $(echo "$exception_classes")")
        VIOLATIONS+=("  -> Steps 9, 10, 11, 12, 14 all define similar exception classes")
        VIOLATIONS+=("  -> Extract to: src/exceptions/step_exceptions.py")
        VIOLATIONS+=("  -> Use: StepInputError, StepOutputError, StepContractError")
        VIOLATIONS+=("  -> Add step_id attribute instead of creating new classes")
        VIOLATIONS+=("  -> Reference: Exception hierarchy inconsistency across steps")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 6: Directory creation pattern (layer_* directories)
    # -------------------------------------------------------------------------
    local layer_dir_pattern=$(echo "$CONTENT" | grep -E "output.*manifestation.*layer_[abc]" | grep "mkdir" | head -1)

    if [ -n "$layer_dir_pattern" ]; then
        VIOLATIONS+=("SSOT: Manual layer directory creation")
        VIOLATIONS+=("  Found in: $FILE_PATH")
        VIOLATIONS+=("  -> This pattern is duplicated in steps 9 and 13")
        VIOLATIONS+=("  -> Extract to: src/utils/io_utils.py")
        VIOLATIONS+=("  -> Use: get_or_create_layer_dir(state, sol_id, layer)")
        VIOLATIONS+=("  -> Reference: Directory management duplication")
        BLOCKED=true
    fi

    # -------------------------------------------------------------------------
    # Check 7: Manifest creation pattern
    # -------------------------------------------------------------------------
    local manifest_dict=$(echo "$CONTENT" | grep -E "manifest[[:space:]]*=[[:space:]]*\{" | head -1)

    if [ -n "$manifest_dict" ]; then
        # Check if it has common manifest fields
        local has_manifestation_id=$(echo "$CONTENT" | grep -E '"manifestation_id":|"manifestation_id"[[:space:]]*:' | head -1)
        local has_created_at=$(echo "$CONTENT" | grep -E '"created_at":|"created_at"[[:space:]]*:' | head -1)

        if [ -n "$has_manifestation_id" ] && [ -n "$has_created_at" ]; then
            VIOLATIONS+=("SSOT: Manual manifest dictionary construction")
            VIOLATIONS+=("  Found in: $FILE_PATH")
            VIOLATIONS+=("  -> Steps 9, 11, 13 manually build similar manifest structures")
            VIOLATIONS+=("  -> Extract to: src/utils/io_utils.py")
            VIOLATIONS+=("  -> Use: create_step_manifest(step_id, manifestation_id, **custom_fields)")
            VIOLATIONS+=("  -> Reference: Manifest creation duplication")
            BLOCKED=true
        fi
    fi

    # -------------------------------------------------------------------------
    # Check 8: Text splitting utilities in step files (should be in utils)
    # -------------------------------------------------------------------------
    local text_split_funcs=$(echo "$CONTENT" | grep -oE "def.*split_(at_boundaries|into_chunks|at_sentence)" | head -1)

    if [ -n "$text_split_funcs" ] && [[ "$FILE_PATH" == */src/steps/* ]]; then
        VIOLATIONS+=("SSOT: Text splitting utility in step file")
        VIOLATIONS+=("  Found: $(echo "$text_split_funcs")")
        VIOLATIONS+=("  -> Text utilities should not be in step-specific files")
        VIOLATIONS+=("  -> Move to: src/utils/text_utils.py")
        VIOLATIONS+=("  -> Make it reusable across all steps")
        VIOLATIONS+=("  -> Reference: Text splitting duplication in step 9")
        BLOCKED=true
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Run validations based on tool type
case "$TOOL_NAME" in
    Write|Edit|MultiEdit)
        validate_file_organization
        validate_file_size
        validate_security
        validate_python_constants
        validate_test_naming
        validate_no_var
        validate_magic_numbers
        validate_no_print
        validate_logger_mixin
        validate_no_silent_failures
        validate_exception_chaining
        validate_exc_info
        validate_fail_fast
        validate_performance
        validate_no_inline_comments
        validate_type_hints
        validate_docstrings
        validate_import_order
        validate_mypy_types
        validate_helper_functions
        validate_memory_leak_prevention
        validate_state_key_usage
        validate_ssot_no_duplication
        ;;
    Bash)
        validate_dangerous_commands
        ;;
esac

# ============================================================================
# REPORT RESULTS
# ============================================================================

if [ ${#VIOLATIONS[@]} -gt 0 ]; then
    echo "" >&2
    echo "============================================" >&2
    echo "  CODING STANDARDS VIOLATION - BLOCKED" >&2
    echo "============================================" >&2
    for violation in "${VIOLATIONS[@]}"; do
        echo "$violation" >&2
    done
    echo "============================================" >&2
    echo "" >&2
fi

if [ "$BLOCKED" = true ]; then
    exit 2
fi


# ============================================================================
# VALIDATION REMINDER - Track file modifications for validation enforcement
# ============================================================================
VALIDATION_PENDING="/tmp/.sol-validation-pending"

if [[ "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Write" ]]; then
    # Track that files were modified
    echo "$(date +%s):$FILE_PATH" >> "$VALIDATION_PENDING" 2>/dev/null || true
fi

if [[ "$TOOL_NAME" == "Task" ]]; then
    # If this is a validation task, clear the pending state
    if echo "$INPUT" | grep -qi '"subagent_type".*valid\|code-review\|test-automator'; then
        rm -f "$VALIDATION_PENDING" 2>/dev/null || true
    fi
fi

if [ ${#VIOLATIONS[@]} -gt 0 ]; then
    echo "" >&2
    echo "============================================" >&2
    echo "  CODING STANDARDS VIOLATION - BLOCKED" >&2
    echo "============================================" >&2
    for violation in "${VIOLATIONS[@]}"; do
        echo "$violation" >&2
    done
    echo "============================================" >&2
    echo "" >&2
fi

if [ "$BLOCKED" = true ]; then
    exit 2
fi

# Pass through input
echo "$INPUT"
exit 0
