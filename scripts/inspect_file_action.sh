#!/bin/zsh

# Inspect & Process File - Interactive Terminal Action for Finder
# Created for macOS Automator Quick Action

set -e

FILE="$1"

if [[ -z "$FILE" ]]; then
    echo "Usage: inspect_file_action.sh <file_path>"
    echo "No file path provided."
    read -k 1 "?Press any key to exit..."
    exit 1
fi

# Reset terminal screen
clear

# Visual Styles
BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
BLUE="\033[34m"
RED="\033[31m"
RESET="\033[0m"

echo "${CYAN}${BOLD}========================================================================${RESET}"
echo "${CYAN}${BOLD}                  🔍 FINDER FILE SPECIFICATIONS                         ${RESET}"
echo "${CYAN}${BOLD}========================================================================${RESET}"

# Basic Attributes
FILENAME=$(basename "$FILE")
DIRNAME=$(dirname "$FILE")
EXTENSION="${FILENAME##*.}"

echo "${BOLD}File Name:${RESET}  $FILENAME"
echo "${BOLD}Full Path:${RESET}  $FILE"
echo "${BOLD}Directory:${RESET}  $DIRNAME"

# Check existence
if [[ ! -e "$FILE" ]]; then
    echo "${RED}Error: File or directory does not exist!${RESET}"
    read -k 1 "?Press any key to exit..."
    exit 1
fi

# File Type Info
FILE_KIND=$(file -b "$FILE" 2>/dev/null || echo "Unknown")
MIME_TYPE=$(file --mime-type -b "$FILE" 2>/dev/null || echo "Unknown")
MDLS_KIND=$(mdls -raw -name kMDItemKind "$FILE" 2>/dev/null | grep -v "(null)" || echo "")

echo "${BOLD}File Type:${RESET}  $FILE_KIND"
if [[ -n "$MDLS_KIND" && "$MDLS_KIND" != "(null)" ]]; then
    echo "${BOLD}Finder Kind:${RESET}$MDLS_KIND"
fi
echo "${BOLD}MIME Type:${RESET}  $MIME_TYPE"

# Detect if Text File
IS_TEXT=false
if [[ -f "$FILE" ]]; then
    if [[ "$MIME_TYPE" == text/* || "$MIME_TYPE" == */json || "$MIME_TYPE" == */xml || "$MIME_TYPE" == */javascript || "$MIME_TYPE" == */x-sh || "$MIME_TYPE" == */x-python || "$MIME_TYPE" == */yaml || "$MIME_TYPE" == */x-yaml || "$MIME_TYPE" == application/x-empty ]]; then
        IS_TEXT=true
    else
        if file -b "$FILE" 2>/dev/null | grep -qE "text|script|JSON|XML|HTML|source"; then
            IS_TEXT=true
        fi
    fi
fi

# Size & Stats
if [[ -d "$FILE" ]]; then
    ITEM_COUNT=$(ls -1A "$FILE" 2>/dev/null | wc -l | tr -d ' ')
    DIR_SIZE=$(du -sh "$FILE" 2>/dev/null | cut -f1)
    echo "${BOLD}Type:${RESET}       Directory / Folder"
    echo "${BOLD}Item Count:${RESET} $ITEM_COUNT items"
    echo "${BOLD}Total Size:${RESET} $DIR_SIZE"
else
    SIZE_BYTES=$(stat -f "%z" "$FILE" 2>/dev/null || echo "0")
    SIZE_HUMAN=$(du -sh "$FILE" 2>/dev/null | cut -f1)
    echo "${BOLD}Size:${RESET}       $SIZE_HUMAN ($SIZE_BYTES bytes)"
fi

# Timestamps & Permissions
PERM_HUMAN=$(stat -f "%Sp (%Lp)" "$FILE" 2>/dev/null || echo "Unknown")
OWNER_INFO=$(stat -f "%Su:%Sg" "$FILE" 2>/dev/null || echo "Unknown")
MOD_TIME=$(stat -f "%Sm" "$FILE" 2>/dev/null || echo "Unknown")
CREATE_TIME=$(stat -f "%SB" "$FILE" 2>/dev/null || echo "Unknown")

echo "${BOLD}Permissions:${RESET}$PERM_HUMAN"
echo "${BOLD}Owner:Group:${RESET}$OWNER_INFO"
echo "${BOLD}Created:${RESET}    $CREATE_TIME"
echo "${BOLD}Modified:${RESET}   $MOD_TIME"

# Extended Specifications depending on type
echo ""
echo "${YELLOW}${BOLD}--- Type-Specific Details ---${RESET}"

if [[ -f "$FILE" ]]; then
    # Text or Code Files
    if [[ "$IS_TEXT" == true ]]; then
        LINES=$(wc -l < "$FILE" | tr -d ' ')
        WORDS=$(wc -w < "$FILE" | tr -d ' ')
        CHARS=$(wc -m < "$FILE" | tr -d ' ')
        echo "${BOLD}Line Count:${RESET} $LINES lines"
        echo "${BOLD}Word Count:${RESET} $WORDS words"
        echo "${BOLD}Char Count:${RESET} $CHARS characters"
        echo "${BOLD}Preview (First 5 lines):${RESET}"
        echo "${BLUE}--------------------------------------------------${RESET}"
        head -n 5 "$FILE" | sed 's/^/  /'
        echo "${BLUE}--------------------------------------------------${RESET}"

    # Image Files
    elif [[ "$MIME_TYPE" == image/* ]]; then
        WIDTH=$(sips -g pixelWidth "$FILE" 2>/dev/null | awk '/pixelWidth:/ {print $2}')
        HEIGHT=$(sips -g pixelHeight "$FILE" 2>/dev/null | awk '/pixelHeight:/ {print $2}')
        if [[ -n "$WIDTH" && -n "$HEIGHT" ]]; then
            echo "${BOLD}Resolution:${RESET} ${WIDTH}x${HEIGHT} pixels"
        fi
        COLORSPACE=$(sips -g space "$FILE" 2>/dev/null | awk '/space:/ {print $2}')
        if [[ -n "$COLORSPACE" ]]; then
            echo "${BOLD}Color Space:${RESET}$COLORSPACE"
        fi

    # Audio / Video Files
    elif [[ "$MIME_TYPE" == video/* || "$MIME_TYPE" == audio/* ]]; then
        DURATION=$(mdls -raw -name kMDItemDurationSeconds "$FILE" 2>/dev/null)
        if [[ -n "$DURATION" && "$DURATION" != "(null)" ]]; then
            DUR_INT=$(printf "%.0f" "$DURATION" 2>/dev/null || echo "0")
            MINS=$((DUR_INT / 60))
            SECS=$((DUR_INT % 60))
            echo "${BOLD}Duration:${RESET}   ${MINS}m ${SECS}s (${DUR_INT} seconds)"
        fi
        CODEC=$(mdls -raw -name kMDItemCodecs "$FILE" 2>/dev/null | tr -d '()' | tr -d '\n' || echo "")
        if [[ -n "$CODEC" && "$CODEC" != "(null)" ]]; then
            echo "${BOLD}Codecs:${RESET}     $CODEC"
        fi

    # PDF / Document Files
    elif [[ "$MIME_TYPE" == "application/pdf" ]]; then
        PAGES=$(mdls -raw -name kMDItemNumberOfPages "$FILE" 2>/dev/null)
        if [[ -n "$PAGES" && "$PAGES" != "(null)" ]]; then
            echo "${BOLD}Page Count:${RESET} $PAGES pages"
        fi
    fi

    # Checksum (fast for files < 100MB)
    if [[ "$SIZE_BYTES" -lt 104857600 ]]; then
        SHA256=$(shasum -a 256 "$FILE" 2>/dev/null | awk '{print $1}')
        echo "${BOLD}SHA-256:${RESET}    $SHA256"
    fi
fi

# Interactive Action Loop
while true; do
    echo ""
    echo "${GREEN}${BOLD}========================================================================${RESET}"
    echo "${GREEN}${BOLD}❓ WHAT WOULD YOU LIKE TO DO WITH THIS FILE?${RESET}"
    echo "${GREEN}${BOLD}========================================================================${RESET}"
    echo "  ${BOLD}[1]${RESET} 📄 Open file in default application"
    echo "  ${BOLD}[2]${RESET} 👁️ Quick Look preview (qlmanage)"
    echo "  ${BOLD}[3]${RESET} 📋 Copy full path to clipboard"
    echo "  ${BOLD}[4]${RESET} 📖 View full content in terminal (less)"
    echo "  ${BOLD}[5]${RESET} 📂 Open containing folder in Finder"
    echo "  ${BOLD}[6]${RESET} ✏️ Rename file"
    echo "  ${BOLD}[7]${RESET} 📦 Compress (create .zip archive)"
    echo "  ${BOLD}[8]${RESET} 🔒 Change file permissions (chmod)"
    echo "  ${BOLD}[9]${RESET} ⚙️ Run custom shell command on file"
    echo "  ${BOLD}[10]${RESET} 🗑️ Move to Trash"
    if [[ "$IS_TEXT" == true ]]; then
        echo "  ${BOLD}[11]${RESET} 📝 Summarize text file contents"
    fi
    echo "  ${BOLD}[12]${RESET} 🛡️ Scan for Prompt Injections & Security Risks (gtwyguard)"
    echo "  ${BOLD}[0]${RESET} ❌ Exit / Close window"
    echo ""
    if [[ "$IS_TEXT" == true ]]; then
        printf "${BOLD}Select an option [0-12]: ${RESET}"
    else
        printf "${BOLD}Select an option [0-10, 12]: ${RESET}"
    fi
    read CHOICE

    case "$CHOICE" in
        1)
            echo "${CYAN}Opening $FILENAME in default application...${RESET}"
            open "$FILE"
            ;;
        2)
            echo "${CYAN}Launching Quick Look preview...${RESET}"
            qlmanage -p "$FILE" >/dev/null 2>&1 &
            ;;
        3)
            echo -n "$FILE" | pbcopy
            echo "${GREEN}✓ Copied path to clipboard:${RESET} $FILE"
            ;;
        4)
            if [[ -f "$FILE" ]]; then
                less "$FILE"
            else
                echo "${YELLOW}Directory contents:${RESET}"
                ls -la "$FILE"
            fi
            ;;
        5)
            echo "${CYAN}Opening Finder at containing folder...${RESET}"
            open -R "$FILE"
            ;;
        6)
            printf "${BOLD}Enter new filename (current: $FILENAME): ${RESET}"
            read NEW_NAME
            if [[ -n "$NEW_NAME" ]]; then
                NEW_PATH="$DIRNAME/$NEW_NAME"
                mv "$FILE" "$NEW_PATH"
                FILE="$NEW_PATH"
                FILENAME="$NEW_NAME"
                echo "${GREEN}✓ File renamed to: $NEW_NAME${RESET}"
            fi
            ;;
        7)
            ZIP_PATH="${FILE}.zip"
            echo "${CYAN}Creating zip archive at $ZIP_PATH...${RESET}"
            zip -r "$ZIP_PATH" "$FILE" >/dev/null
            echo "${GREEN}✓ Zip archive created!${RESET}"
            ;;
        8)
            printf "${BOLD}Enter new octal permissions (e.g., 755, 644): ${RESET}"
            read MODE
            if [[ -n "$MODE" ]]; then
                chmod "$MODE" "$FILE"
                echo "${GREEN}✓ Permissions updated to $MODE${RESET}"
            fi
            ;;
        9)
            echo "${YELLOW}Use '\$FILE' or \$FILE in your command to reference the file.${RESET}"
            printf "${BOLD}Enter shell command (e.g., head -n 20 \$FILE, wc \$FILE): ${RESET}"
            read CMD
            if [[ -n "$CMD" ]]; then
                echo "${CYAN}Running: $CMD${RESET}"
                eval "$CMD"
            fi
            ;;
        10)
            printf "${RED}${BOLD}Are you sure you want to move $FILENAME to Trash? (y/N): ${RESET}"
            read CONFIRM
            if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
                osascript -e 'tell application "Finder" to delete POSIX file "'"$FILE"'"'
                echo "${GREEN}✓ Moved $FILENAME to Trash.${RESET}"
                echo "Exiting..."
                sleep 1
                break
            else
                echo "Cancelled."
            fi
            ;;
        11)
            if [[ "$IS_TEXT" == true ]]; then
                echo ""
                echo "${MAGENTA}${BOLD}========================================================================${RESET}"
                echo "${MAGENTA}${BOLD}                  📝 TEXT FILE SUMMARY & ANALYTICS                      ${RESET}"
                echo "${MAGENTA}${BOLD}========================================================================${RESET}"
                
                TOTAL_LINES=$(wc -l < "$FILE" | tr -d ' ')
                NON_EMPTY_LINES=$(grep -c -v '^[[:space:]]*$' "$FILE" 2>/dev/null || echo "0")
                WORD_COUNT=$(wc -w < "$FILE" | tr -d ' ')
                CHAR_COUNT=$(wc -m < "$FILE" | tr -d ' ')
                AVG_WORDS_PER_LINE=0
                if [[ "$TOTAL_LINES" -gt 0 ]]; then
                    AVG_WORDS_PER_LINE=$(( WORD_COUNT / TOTAL_LINES ))
                fi

                echo "${BOLD}Total Lines:${RESET}      $TOTAL_LINES ($NON_EMPTY_LINES non-empty)"
                echo "${BOLD}Total Words:${RESET}      $WORD_COUNT"
                echo "${BOLD}Total Chars:${RESET}      $CHAR_COUNT"
                echo "${BOLD}Avg Words/Line:${RESET}   $AVG_WORDS_PER_LINE"

                HEADINGS=$(grep -nE '^(#+|[a-zA-Z_0-9]+[[:space:]]*\(|def |class |function|\[|\/\/) ' "$FILE" 2>/dev/null | head -n 10 || echo "")
                if [[ -n "$HEADINGS" ]]; then
                    echo ""
                    echo "${YELLOW}${BOLD}--- Outline / Key Headings ---${RESET}"
                    echo "$HEADINGS" | sed 's/^/  /'
                fi

                TOP_WORDS=$(tr -c '[:alnum:]' '[\n*]' < "$FILE" 2>/dev/null | tr '[:upper:]' '[:lower:]' | grep -vE '^(the|and|for|that|this|with|from|have|not|you|are|was|which|they|will|would|there|their|been|has|more|what|some|into|than|out|them|other|can|only|its|also|about|over|such|most|or|in|on|of|to|is|a|an|it|if|by|as|at|be)$' | awk 'length($0) > 3' | sort | uniq -c | sort -nr | head -n 8 || echo "")
                if [[ -n "$TOP_WORDS" ]]; then
                    echo ""
                    echo "${YELLOW}${BOLD}--- Top Key Topics / Frequently Used Words ---${RESET}"
                    echo "$TOP_WORDS" | awk '{printf "  - %-15s (count: %d)\n", $2, $1}'
                fi

                echo ""
                echo "${YELLOW}${BOLD}--- Opening Excerpt ---${RESET}"
                head -n 5 "$FILE" | sed 's/^/  /'
                if [[ "$TOTAL_LINES" -gt 10 ]]; then
                    echo ""
                    echo "${YELLOW}${BOLD}--- Closing Excerpt ---${RESET}"
                    tail -n 5 "$FILE" | sed 's/^/  /'
                fi
                echo "${MAGENTA}${BOLD}========================================================================${RESET}"
            else
                echo "${RED}Option [11] is only available for text files.${RESET}"
            fi
            ;;
        12)
            echo "${CYAN}${BOLD}Shielding file & scanning for Prompt Injections with gtwyguard...${RESET}"
            if command -v gtwyguard >/dev/null 2>&1; then
                gtwyguard scan "$FILE" --quarantine
            elif [[ -x "$HOME/gtwyguard/.venv/bin/gtwyguard" ]]; then
                "$HOME/gtwyguard/.venv/bin/gtwyguard" scan "$FILE" --quarantine
            elif [[ -x "$HOME/.local/bin/gtwyguard" ]]; then
                "$HOME/.local/bin/gtwyguard" scan "$FILE" --quarantine
            else
                echo "${RED}gtwyguard is not installed or not found on PATH.${RESET}"
            fi
            ;;
        0)
            echo "Exiting..."
            break
            ;;
        *)
            echo "${RED}Invalid choice, please try again.${RESET}"
            ;;
    esac
done
