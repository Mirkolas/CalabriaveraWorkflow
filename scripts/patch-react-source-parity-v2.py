from pathlib import Path

base = Path('automation/scripts/patch-react-source-parity.py')
code = base.read_text(encoding='utf-8')
start = code.index('# 4) Empty public endpoint')
end = code.index('# 5) Prevent Leaflet', start)
replacement = '''# 4) Current public-data loader already treats an empty endpoint as non-authoritative and retries the Firebase SDK.\np = root / 'frontend-react/src/lib/public-data.ts'\ns = p.read_text(encoding='utf-8')\nif 'if (!publicRows.length)' not in s or 'retry(() => loadAllBusinesses(true))' not in s:\n    raise SystemExit('public data empty-snapshot fallback is missing')\n\n'''
code = code[:start] + replacement + code[end:]
exec(compile(code, str(base), 'exec'))
