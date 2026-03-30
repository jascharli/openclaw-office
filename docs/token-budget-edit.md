# Token Budget Edit Feature - v1.0.4

## Overview
Frontend Token budget editing - no need to manually edit config files.

## API Endpoint
PUT /api/v1/tokens/budget

## Usage
1. Click edit button on Daily Budget card
2. Enter new budget value
3. Save - takes effect immediately

## Files Modified
- backend/main.py: Added PUT endpoint
- frontend/index.html: Added edit dialog and methods
