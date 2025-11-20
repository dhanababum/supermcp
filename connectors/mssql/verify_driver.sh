#!/bin/bash
# Verify ODBC Driver installation

echo "=== ODBC Driver Verification ==="
echo ""

echo "1. Checking installed ODBC drivers:"
odbcinst -q -d
echo ""

echo "2. Checking ODBC Driver 18 for SQL Server:"
if odbcinst -q -d -n "ODBC Driver 18 for SQL Server"; then
    echo "✅ ODBC Driver 18 for SQL Server is installed"
else
    echo "❌ ODBC Driver 18 for SQL Server NOT found"
    exit 1
fi
echo ""

echo "3. Driver library location:"
find /opt/microsoft -name "libmsodbcsql*.so*" 2>/dev/null || echo "Driver library not found"
echo ""

echo "4. SQL Server tools:"
which sqlcmd 2>/dev/null && echo "✅ sqlcmd is available" || echo "❌ sqlcmd not found"
echo ""

echo "5. Python aioodbc test:"
python3 -c "import aioodbc; print('✅ aioodbc module imported successfully')" 2>/dev/null || \
    echo "⚠️  aioodbc not yet installed (will be installed during build)"
echo ""

echo "=== Verification Complete ==="

