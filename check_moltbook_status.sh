#!/bin/bash
# Helper script to check Moltbook ban status
# Returns exit code 0 if OK to post, 1 if banned
# Automatically unbans if ban has expired

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATUS_FILE="$SCRIPT_DIR/moltbook_status.json"

# If status file doesn't exist, assume no ban
if [[ ! -f "$STATUS_FILE" ]]; then
    echo "✅ Moltbook: No ban status file found - OK to post"
    exit 0
fi

# Check status using Python for proper JSON and datetime handling
python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('$STATUS_FILE') as f:
        status = json.load(f)
    
    banned = status.get('banned', False)
    
    if not banned:
        print('✅ Moltbook: Account is in good standing - OK to post')
        sys.exit(0)
    
    # Check if ban has expired
    ban_expires = status.get('ban_expires')
    if ban_expires:
        try:
            ban_expiry_dt = datetime.fromisoformat(ban_expires.replace('Z', '+00:00'))
            now = datetime.now(ban_expiry_dt.tzinfo)
            
            if now >= ban_expiry_dt:
                # Ban has expired, automatically unban
                status['banned'] = False
                with open('$STATUS_FILE', 'w') as f:
                    json.dump(status, f, indent=2)
                print('✅ Moltbook: Ban expired and cleared automatically - OK to post')
                sys.exit(0)
            else:
                # Ban is still active
                expiry_str = ban_expiry_dt.strftime('%Y-%m-%d %H:%M %Z')
                reason = status.get('reason', 'account restriction')
                offense_num = status.get('offense_number', 'unknown')
                print(f'❌ Moltbook: Account suspended until {expiry_str}')
                print(f'   Reason: {reason} (offense #{offense_num})')
                sys.exit(1)
        except (ValueError, TypeError) as e:
            print(f'⚠️  Moltbook: Invalid ban_expires format in status file: {e}')
            sys.exit(1)
    else:
        # No expiry date means permanent ban
        reason = status.get('reason', 'account restriction')
        offense_num = status.get('offense_number', 'unknown')
        print(f'❌ Moltbook: Account permanently suspended')
        print(f'   Reason: {reason} (offense #{offense_num})')
        sys.exit(1)

except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f'⚠️  Moltbook: Error reading status file: {e}')
    sys.exit(1)
"