# SecureDx AI — Sprint 2 Missing Files

This package contains all the missing files needed to complete the physician workflow with working authentication.

## What's Included

### Keycloak Configuration
- `realm-export.json` — Complete Keycloak realm with users and roles

### Frontend Files
- `useAuth.tsx` — Keycloak authentication hook
- `apiClient.ts` — Axios instance with auth interceptor
- `inference.ts` — Inference API functions
- `patients.ts` — Patients API functions
- `feedback.ts` — Feedback API functions
- `LoginPage.tsx` — Login page component
- `LoadingScreen.tsx` — Loading component
- `AppLayout.tsx` — Main app layout with navigation
- `PatientListPage.tsx` — Patient list page
- `vite.config.ts` — Vite configuration
- `index.html` — HTML entry point
- `main.tsx` — React entry point
- `index.css` — Tailwind CSS imports
- `tailwind.config.js` — Tailwind configuration
- `postcss.config.js` — PostCSS configuration
- `tsconfig.json` — TypeScript configuration
- `tsconfig.node.json` — TypeScript config for Vite

## Installation Instructions

### 1. Copy Keycloak Realm

```bash
cd securedx
cp realm-export.json infrastructure/keycloak/realm-export.json
```

### 2. Copy Frontend Files

```bash
# Hooks
cp useAuth.tsx services/frontend/src/hooks/

# API Layer
mkdir -p services/frontend/src/api
cp apiClient.ts services/frontend/src/api/
cp inference.ts services/frontend/src/api/
cp patients.ts services/frontend/src/api/
cp feedback.ts services/frontend/src/api/

# Components
cp LoadingScreen.tsx services/frontend/src/components/shared/
cp AppLayout.tsx services/frontend/src/components/shared/

# Pages
cp LoginPage.tsx services/frontend/src/pages/
cp PatientListPage.tsx services/frontend/src/pages/physician/

# Config files (root of services/frontend/)
cp vite.config.ts services/frontend/
cp index.html services/frontend/
cp main.tsx services/frontend/src/
cp index.css services/frontend/src/
cp tailwind.config.js services/frontend/
cp postcss.config.js services/frontend/
cp tsconfig.json services/frontend/
cp tsconfig.node.json services/frontend/
```

### 3. Restart Services

```bash
docker compose down
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### 4. Wait for Keycloak to Initialize

Keycloak takes ~60 seconds to import the realm and start. Check logs:

```bash
docker logs -f securedx-keycloak
```

Wait for: `Keycloak 23.0.7 started in X.XXXs`

### 5. Access the Application

Open: http://localhost/

Login with:
- **Physician**: `physician@clinic.local` / `ChangeMe123!`
- **Admin**: `admin@clinic.local` / `ChangeMe123!`
- **Compliance**: `compliance@clinic.local` / `ChangeMe123!`

## What Works Now

✅ Complete authentication flow with Keycloak
✅ Login page with OIDC
✅ Patient list page
✅ Inference page (from your existing code)
✅ SHAP visualization
✅ Feedback submission
✅ Role-based navigation
✅ Auto token refresh
✅ Logout

## Test Users

All users have the same password: `ChangeMe123!`

| Email | Role | Access |
|-------|------|--------|
| physician@clinic.local | physician | Run diagnostics, submit feedback |
| admin@clinic.local | admin | Full system access |
| compliance@clinic.local | compliance_officer | Audit logs only |

## Troubleshooting

### "Failed to connect to localhost:3000"

Services are behind nginx. Access via **http://localhost** (port 80), not port 3000.

### Keycloak health check failing

Already fixed in your docker-compose.yml. If it still fails, check:
```bash
docker logs securedx-keycloak
```

### Frontend shows blank page

Check browser console for errors. Common issues:
- Missing `keycloak-js` package: `cd services/frontend && npm install keycloak-js`
- CORS errors: Check `.env` has `CORS_ORIGINS=http://localhost:3000,http://localhost`

### API returns 401

Token expired or not being sent. Check:
1. You're logged in (refresh the page)
2. Browser dev tools → Network → Request has `Authorization: Bearer ...` header

## Next Steps

After this works, you can add:
- Real patient data (currently returns empty list)
- Database models for patients/feedback
- Admin dashboard
- Compliance audit viewer
- Break-glass UI

Let me know which you want built next!
