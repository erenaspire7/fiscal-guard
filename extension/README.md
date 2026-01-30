# Fiscal Guard Chrome Extension

Real-time purchase analysis for e-commerce sites, starting with Amazon.

## Implementation Status

### ✅ Completed (Phase 1 & 2)

#### Backend API
- ✅ Added `google-auth` dependency
- ✅ Created `POST /auth/google/token` endpoint for extension OAuth
- ✅ Created cart analysis models (`core/src/core/models/cart.py`)
- ✅ Created `POST /decisions/extract-cart-screenshot` endpoint (Vision Agent)
- ✅ Created `POST /decisions/analyze-cart` endpoint
- ✅ Implemented `VisionAgent` for secure server-side screenshot processing
- ✅ Implemented `analyze_cart_items` service method
- ✅ Updated CORS to allow Chrome extension

#### Extension Setup
- ✅ Project structure with Vite + React + TypeScript
- ✅ Tailwind CSS v4 configuration (matching main app)
- ✅ shadcn/ui components (button, card, input, label, etc.)
- ✅ Shared types and utilities
- ✅ Storage manager for Chrome storage
- ✅ API client for backend communication
- ✅ OAuth authentication flow (popup-based)
- ✅ Login popup UI
- ✅ Background service worker setup

### ✅ Completed (Phase 3-5)

#### Phase 3: Vision & Capture
- ✅ Screenshot capture logic for Amazon pages
- ✅ Amazon page detector
- ✅ Server-side vision processing via Vision Agent
- ⬜ Test Vision Agent extraction accuracy on real Amazon pages

#### Phase 4: UI Components
- ✅ FloatingSidebar component (chat-style interface)
- ✅ ItemCard component (individual item display)
- ✅ ScoreBadge component (score visualization)
- ✅ Shadow DOM injection wrapper
- ✅ Streaming markdown support for chat

#### Phase 5: Integration & Polish
- ✅ Main content script orchestration
- ✅ Loading states and error handling
- ✅ Secure backend-based vision processing (no client-side API keys)
- ⬜ Screenshot consent flow
- ⬜ End-to-end testing
- ✅ Extension icons and assets

### 🚧 Remaining Tasks

#### Polish & Testing
- ⬜ Test Vision Agent extraction accuracy on real Amazon pages
- ⬜ Implement screenshot consent dialog
- ✅ Add extension icons (16x16, 48x48, 128x128)
- ⬜ End-to-end testing on various Amazon pages
- ⬜ Handle edge cases (empty cart, network errors, etc.)
- ⬜ Improve error messages and user feedback

## Project Structure

```
extension/
├── src/
│   ├── popup/                  # Login popup
│   │   ├── index.html
│   │   ├── index.tsx
│   │   └── Login.tsx           ✅
│   ├── content/                # Content script (injected into Amazon)
│   │   ├── index.tsx           ✅
│   │   ├── FloatingSidebar.tsx ✅
│   │   ├── ShadowDOM.tsx       ✅
│   │   ├── AmazonDetector.ts   ✅
│   │   └── ScreenshotCapture.ts ✅
│   ├── background/             # Background service worker
│   │   ├── service-worker.ts   ✅
│   │   └── auth.ts             ✅
│   ├── shared/                 # Shared utilities
│   │   ├── types.ts            ✅
│   │   ├── constants.ts        ✅
│   │   ├── storage.ts          ✅
│   │   └── api-client.ts       ✅
│   ├── components/ui/          # shadcn components
│   │   ├── button.tsx          ✅
│   │   ├── card.tsx            ✅
│   │   ├── input.tsx           ✅
│   │   ├── label.tsx           ✅
│   │   ├── streaming-markdown.tsx ✅
│   │   └── ...                 ✅
│   ├── lib/
│   │   └── utils.ts            ✅
│   ├── manifest.json           ✅
│   └── index.css               ✅
├── package.json                ✅
├── vite.config.ts              ✅
├── tsconfig.json               ✅
└── README.md                   ✅
```

## Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Popup      │  │   Content    │  │  Background  │      │
│  │   (Login)    │  │   Script     │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                  │               │
│         │                 │  1. Capture      │               │
│         │                 │  Screenshot      │               │
│         │                 │                  │               │
│         │                 │  2. Send to      │               │
│         │                 │  Backend API     │               │
│         │                 │  (base64 image)  │               │
│         │                 │                  │               │
└─────────────────────────────┼──────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────────────┐
                │   Fiscal Guard API                  │
                ├─────────────────────────────────────┤
                │  - POST /auth/google/token          │
                │  - POST /decisions/                 │
                │         extract-cart-screenshot     │
                │    (Vision Agent extracts items)    │
                │  - POST /decisions/analyze-cart     │
                │  - POST /chat/message               │
                └─────────────────────────────────────┘
```

### Key Features

1. **Server-Side Vision Processing**: Screenshots processed securely on backend using Vision Agent
2. **No Client API Keys**: Gemini API key stored securely on backend only
3. **Privacy-First**: Screenshots deleted immediately after extraction
4. **Individual Item Analysis**: Each cart item analyzed separately with aggregate view
5. **Chat Follow-Up**: Users can ask questions about recommendations
6. **OAuth Integration**: Secure Google OAuth with token exchange

## Development

### Prerequisites

```bash
# Install dependencies
yarn install

# Environment variables are loaded from the root .env file
# Make sure your root .env has:
# - VITE_API_URL (your backend API URL)
# - VITE_GOOGLE_CLIENT_ID (Google OAuth client ID)
```

### Build

```bash
# Development (watch mode)
yarn dev

# Production build
yarn build

# Or use the build script from the root
../scripts/build-extension.sh
```

### Load Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension/dist` directory

## Configuration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URIs:
   - `https://<extension-id>.chromiumapp.org/`
   - Get extension ID from `chrome://extensions/`
4. Add your client ID to the root `.env` file:
   ```bash
   VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```
   The build script will source this and inject it into manifest.json during build

## Security & Privacy

- ✅ Screenshots processed securely on backend (never stored)
- ✅ Server-side vision processing with Vision Agent
- ✅ No API keys exposed to client
- ✅ Token verification on backend
- ✅ Secure Chrome storage for auth tokens
- ⬜ Explicit screenshot consent (TODO: implement)

## Next Steps

### Ready for Testing

The core functionality is now complete! Here's what you can do next:

1. **Build the extension**:
   ```bash
   # From project root
   ./scripts/build-extension.sh
   
   # Or from extension directory
   cd extension
   yarn install
   yarn build
   ```

2. **Load in Chrome**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select `extension/dist`

3. **Configure**:
   - Set `VITE_API_URL` in `extension/.env` to your backend URL
   - Set `VITE_GOOGLE_CLIENT_ID` with your Google OAuth client ID
   - Update `extension/manifest.json` with your Google client ID
   - Ensure backend has `GOOGLE_API_KEY` configured for Vision Agent

4. **Test the flow**:
   - Visit Amazon.com and add items to cart
   - Click the extension icon
   - Login with Google OAuth
   - View cart analysis with AI recommendations
   - Ask follow-up questions in the chat

### Remaining Work

Before production release:
- Test Vision Agent extraction accuracy on real Amazon pages
- Add screenshot consent dialog
- ✅ Design and add extension icons (16x16, 48x48, 128x128)
- Comprehensive testing on various Amazon pages
- Handle edge cases and improve error handling
- Add usage analytics (optional)

## Recent Changes

### Migration to Backend Vision Processing

The extension has been refactored to use secure server-side vision processing:

**What Changed:**
- ❌ Removed client-side Gemini API calls
- ❌ Removed Gemini API key storage in browser
- ❌ Removed `gemini-client.ts` from extension
- ✅ Added `VisionAgent` on backend (`core/src/core/ai/agents/vision_agent.py`)
- ✅ Added `/decisions/extract-cart-screenshot` endpoint
- ✅ Extension now sends screenshots to backend for processing

**Benefits:**
- 🔒 **Security**: No API keys exposed to client
- 🔒 **Privacy**: Screenshots processed server-side with immediate deletion
- 🎯 **Consistency**: Centralized vision processing logic
- 🚀 **Performance**: Backend can optimize processing
- 💰 **Cost Control**: Backend manages API usage and rate limiting
