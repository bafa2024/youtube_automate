# B-Roll Organize Button Fix Guide

## Issue Fixed
The B-Roll organize button was not functioning because the frontend (served from XAMPP on port 80) was trying to make API calls to relative URLs, but the backend API server runs on port 8080.

## Solution Applied

### 1. Added API Base URL Configuration
Added a configuration constant in `app.js` to properly route API calls:
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8080' : '';
```

### 2. Created API URL Helper Function
Added a helper function to construct proper API URLs:
```javascript
function apiUrl(path) {
    return `${API_BASE_URL}${path}`;
}
```

### 3. Updated All API Calls
Updated all fetch() calls throughout the application to use the apiUrl() helper function.

## How to Test

### Step 1: Start the Backend Server
Run the backend server using one of these methods:
```bash
# Option 1: Using the batch file
start_server.bat

# Option 2: Using Python directly
python main.py

# Option 3: Using the B-roll organizer starter
python start_broll_organizer.py
```

The server should start on `http://localhost:8080`

### Step 2: Access the Web Interface
Open your browser and go to:
```
http://localhost/yt_automation_web/static/
```

### Step 3: Test the B-Roll Organize Feature
1. Upload at least one B-roll clip using the B-Roll tab
2. Click the "Reorganize B-Roll" button
3. Check the browser console (F12) for detailed logs

### Step 4: Use Test Pages
- Test server connection: `http://localhost/yt_automation_web/test_broll_fix.html`
- Test B-roll endpoint: `http://localhost/yt_automation_web/test_broll_button.html`

## Troubleshooting

### Server Not Running
- Check if port 8080 is already in use
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

### CORS Issues
The backend is configured to accept requests from localhost. If you still get CORS errors, check `config.py` for ALLOWED_ORIGINS.

### Button Still Not Working
1. Open browser console (F12) and check for errors
2. Look for network requests to see if they're going to the correct URL
3. Check that uploads are successful before trying to organize

## What Changed

### Files Modified:
1. `static/app.js` - Added API base URL configuration and updated all fetch calls
2. Created test files for debugging
3. Created documentation

### Key Changes in app.js:
- Line 5: Added `API_BASE_URL` constant
- Line 18-20: Added `apiUrl()` helper function
- Updated all fetch() calls to use `apiUrl()`
- Added detailed console logging in `organizeBroll()` function

## Additional Notes
- The fix ensures that the frontend can communicate with the backend regardless of where it's served from
- Enhanced error logging helps debug issues faster
- The solution is backwards compatible and won't break if both frontend and backend are served from the same origin