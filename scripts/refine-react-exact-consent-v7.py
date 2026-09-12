from pathlib import Path

p = Path('frontend-react/scripts/copy-legacy-assets.mjs')
s = p.read_text()
old = '''    privacyCss += `\n/* ${deployParityMarker}: exact computed values from backup deploy output. */\n@media(max-width:760px){.cv-consent-banner h2{font-size:25.35px;line-height:28.392px;max-width:100%}.cv-consent-banner .cv-consent-actions .button{padding:10.24px 14.72px;max-width:100%}}\n`;'''
new = '''    privacyCss += `\n/* ${deployParityMarker}: exact computed values from backup deploy output. */\n.cv-consent-banner h2{font-family:Georgia,"Times New Roman",serif!important;font-weight:700!important;letter-spacing:-0.672px!important}.cv-consent-banner .cv-consent-actions .button{padding:10.24px 14.72px!important;letter-spacing:normal!important;min-width:0!important;max-width:100%!important}@media(max-width:760px){.cv-consent-banner h2{font-size:25.35px!important;line-height:28.392px!important;letter-spacing:-0.7098px!important;max-width:100%!important}}\n`;'''
if old not in s:
    raise SystemExit('consent built-parity generator contract changed')
s = s.replace(old, new, 1)
p.write_text(s)
