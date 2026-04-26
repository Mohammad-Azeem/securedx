/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_KEYCLOAK_URL: string
  readonly VITE_KEYCLOAK_REALM: string
  readonly VITE_KEYCLOAK_CLIENT_ID: string
  readonly VITE_FL_ENABLED: string
  readonly VITE_FEEDBACK_LOOP_ENABLED: string
  readonly VITE_AUDIT_EXPORT_ENABLED: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
