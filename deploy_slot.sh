#!/bin/bash
set -euo pipefail

# Usage: ./deploy_slot.sh <RESOURCE_GROUP> <APP_NAME> <SLOT_NAME>
# Example: ./deploy_slot.sh sr-impact-navigator-rg sr-impact-navigator sr-impact-navigator-dec

if [ $# -ne 3 ]; then
  echo "Usage: $0 <RESOURCE_GROUP> <APP_NAME> <SLOT_NAME>"
  exit 1
fi

RESOURCE_GROUP="$1"
APP_NAME="$2"
SLOT_NAME="$3"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure startup.sh is executable
if [ -f startup.sh ]; then
  chmod +x startup.sh
fi

# Set startup file on the slot
az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --slot "$SLOT_NAME" \
  --startup-file "startup.sh"

# Create ZIP package
ZIP_NAME="app.zip"
rm -f "$ZIP_NAME"
zip -r "$ZIP_NAME" . -x "*.git*" "*.DS_Store*" "__pycache__/*" "*.pyc"

# Deploy ZIP to the slot
az webapp deployment source config-zip \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --slot "$SLOT_NAME" \
  --src "$ZIP_NAME"

# Show slot URL
HOSTNAME=$(az webapp show --resource-group "$RESOURCE_GROUP" --name "$APP_NAME" --slot "$SLOT_NAME" --query "defaultHostName" -o tsv)
echo "Deployment completed. Slot URL: https://$HOSTNAME"
