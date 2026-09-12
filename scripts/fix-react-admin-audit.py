from pathlib import Path

auth=Path('source/frontend-react/src/lib/auth.ts')
rules=Path('source/firestore.rules')

s=auth.read_text(encoding='utf-8')
old='export async function auditEvent(event: "account_created" | "login_password" | "login_google" | "password_changed" | "logout", resourceId = "") {'
new='export type AuditEventName = "account_created" | "login_password" | "login_google" | "password_changed" | "logout" | "admin_conversation_deleted";\n\nexport async function auditEvent(event: AuditEventName, resourceId = "") {'
if old not in s:
    raise SystemExit('auditEvent signature marker missing')
s=s.replace(old,new,1)
auth.write_text(s,encoding='utf-8')

s=rules.read_text(encoding='utf-8')
old="        && request.resource.data.event in ['account_created', 'login_password', 'login_google', 'password_changed', 'logout', 'business_created', 'business_updated']\n"
new="        && (request.resource.data.event in ['account_created', 'login_password', 'login_google', 'password_changed', 'logout', 'business_created', 'business_updated']\n          || (admin() && request.resource.data.event == 'admin_conversation_deleted'))\n"
if old not in s:
    raise SystemExit('auditLogs event allowlist marker missing')
s=s.replace(old,new,1)
rules.write_text(s,encoding='utf-8')
print('ADMIN_AUDIT_EVENT_AUTHORIZED')
