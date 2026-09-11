# Load Testing Feature - Cleanup Guide

This document lists all temporary files and code added for load testing. **Remove these before production deployment.**

## Files to Delete

1. `backend/routes/test.py` - Temporary load testing endpoint
2. `components/BulkTestButton.tsx` - Temporary bulk test component
3. `LOAD_TESTING_CLEANUP.md` - This file

## Code to Remove

### backend/main.py

Remove the import line:
```python
from routes.test import router as test_router  # TEMPORARY - for load testing
```

Remove the router registration line:
```python
app.include_router(test_router)  # TEMPORARY - for load testing
```

### app/(dashboard)/dashboard/page.tsx

Remove the import:
```typescript
import BulkTestButton from "@/components/BulkTestButton"; // TEMPORARY - for load testing
```

Remove the entire section (search for "TEMPORARY - Bulk load testing"):
```typescript
{/* TEMPORARY - Bulk load testing */}
<section className="rounded-xl border border-dashed border-yellow-500/50 bg-yellow-50/50 p-5 dark:bg-yellow-950/20">
  <BulkTestButton onComplete={() => setRefreshKey((k) => k + 1)} />
</section>
```

## Quick Cleanup Script

Run this PowerShell script from the project root:

```powershell
# Delete files
Remove-Item "backend/routes/test.py" -ErrorAction SilentlyContinue
Remove-Item "components/BulkTestButton.tsx" -ErrorAction SilentlyContinue
Remove-Item "LOAD_TESTING_CLEANUP.md" -ErrorAction SilentlyContinue

Write-Host "Load testing files deleted. Now manually remove the code snippets from main.py and dashboard/page.tsx as documented above."
```

## Testing the Feature

1. Make sure backend is running: `cd backend && uvicorn main:app --reload`
2. Make sure frontend is running: `npm run dev`
3. Navigate to Dashboard
4. Scroll to the bottom to see the "Load Testing (Temporary)" section
5. Click "20 messages", "50 messages", or "100 messages" to test
6. Messages will be created with realistic content and go through full AI pipeline
7. Dashboard will auto-refresh after completion

## Notes

- Maximum allowed: 150 messages per request (enforced by backend)
- Small delays (0.5s every 10 messages) prevent server freeze
- Each message is unique with timestamp
- Messages cycle through 15 realistic templates
- Full AI analysis runs for each message (same as real messages)
- User isolation is properly enforced
