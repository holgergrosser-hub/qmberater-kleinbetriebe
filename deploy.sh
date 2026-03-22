#!/bin/bash
# Deploy: qmberater-kleinbetriebe → 9001-zertifikat.qmberater.info

REPO="qmberater-kleinbetriebe"
NETLIFY_SITE="qmberater-kleinbetriebe"

echo "🚀 Deploying $REPO..."

# Build
npm install && npm run build

# Deploy to Netlify
netlify deploy --prod --dir=dist --site=$NETLIFY_SITE

echo "✅ Done. Live at: https://9001-zertifikat.qmberater.info"
