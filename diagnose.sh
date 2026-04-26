#!/bin/bash
echo "🔍 SecureDx 502 Diagnostic Script"
echo "=================================="

echo ""
echo "1. Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep securedx

echo ""
echo "2. API Health Check:"
docker exec securedx-nginx curl -s http://api:8000/health || echo "❌ API unreachable"

echo ""
echo "3. API Logs (last 10 lines):"
docker logs securedx-api --tail 10

echo ""
echo "4. Nginx Proxy Test:"
curl -I http://localhost/api/v1/health

echo ""
echo "5. Database Status:"
docker exec securedx-api python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(
    f\"postgresql://securedx_app:{os.getenv('DB_PASSWORD')}@postgres:5432/securedx\"
)
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database reachable')
except Exception as e:
    print(f'❌ Database error: {e}')
"

echo ""
echo "=================================="
echo "Analysis complete!"