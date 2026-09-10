"""
Generates docs/FAMS_System_Architecture.pdf — a technical architecture
overview for trainers, partner companies, and technical evaluators.

Run from the project root with the project venv active:

    python docs/generate_architecture_doc.py

Uses xhtml2pdf (the same PDF library the app itself uses for payslips/
reports, and the same one docs/generate_guides.py uses) so no extra
dependency is needed. Content lives in this file as plain HTML strings;
update ARCH_SECTIONS here and re-run rather than editing the PDF directly.
"""

from pathlib import Path

from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "static" / "images" / "ui" / "auth-logo.png"

STYLE = """
<style>
    @page {
        size: A4;
        margin: 2.2cm 2cm 2.5cm 2cm;
        @frame footer_frame {
            -pdf-frame-content: footer_content;
            bottom: 1cm; margin-left: 2cm; margin-right: 2cm; height: 1cm;
        }
    }
    body { font-family: Helvetica, sans-serif; font-size: 10.5pt; color: #1a1a1a; line-height: 1.45; }
    .cover { text-align: center; padding-top: 3cm; }
    .cover img { width: 3cm; }
    .cover .cover-title { font-size: 26pt; font-weight: bold; margin-top: 0.8cm; margin-bottom: 0.2cm; color: #0f2a4a; border-bottom: 2px solid #0f2a4a; padding-bottom: 10px; }
    .cover .cover-subtitle { font-size: 14pt; font-weight: normal; color: #555555; margin-top: 8px; }
    .cover .meta { margin-top: 2cm; font-size: 10pt; color: #888888; }
    h1 { font-size: 17pt; color: #0f2a4a; border-bottom: 2px solid #0f2a4a; padding-bottom: 4px; margin-top: 0; -pdf-outline: true; -pdf-outline-level: 0; }
    h2 { font-size: 12.5pt; color: #16406b; margin-top: 16px; margin-bottom: 4px; -pdf-outline: true; -pdf-outline-level: 1; }
    h3 { font-size: 11pt; color: #16406b; margin-top: 10px; margin-bottom: 3px; }
    p { margin: 4px 0 8px 0; text-align: justify; }
    ul, ol { margin: 4px 0 10px 0; padding-left: 18px; }
    li { margin-bottom: 3px; }
    table { width: 100%; border-collapse: collapse; margin: 8px 0 14px 0; font-size: 9.5pt; }
    th, td { border: 1px solid #cccccc; padding: 5px 7px; text-align: left; vertical-align: top; }
    th { background-color: #eef2f7; color: #0f2a4a; }
    code { font-family: Courier, monospace; background-color: #f2f2f2; padding: 1px 3px; font-size: 9pt; }
    .note { background-color: #fff7e6; border-left: 3px solid #e8a33d; padding: 6px 10px; margin: 8px 0; font-size: 9.5pt; }
    .box { border: 1px solid #16406b; background-color: #f5f8fc; padding: 6px 10px; margin: 4px 0; font-size: 9.5pt; }
    .layer-title { font-weight: bold; color: #0f2a4a; margin-bottom: 4px; }
    .chapter { page-break-before: always; }
    #footer_content { text-align: center; font-size: 8pt; color: #999999; border-top: 0.5pt solid #dddddd; padding-top: 4px; }
</style>
"""


def cover(title: str, subtitle: str) -> str:
    logo_tag = f'<img src="{LOGO.as_posix()}" />' if LOGO.exists() else ""
    return f"""
    <div class="cover">
        {logo_tag}
        <div class="cover-title">{title}</div>
        <div class="cover-subtitle">{subtitle}</div>
        <p class="meta">Fortivex Attendance Management System (FAMS)<br/>
        Built on the open-source Horilla HRMS (LGPL v2.1)</p>
    </div>
    """


def footer() -> str:
    return '<div id="footer_content">FAMS System Architecture &middot; Page <pdf:pagenumber /> of <pdf:pagecount /></div>'


def build(title: str, subtitle: str, sections: list[tuple[str, str]]) -> str:
    chapters = "".join(
        f'<div class="chapter"><h1>{heading}</h1>{body}</div>'
        for heading, body in sections
    )
    return f"""
    <html>
    <head>{STYLE}</head>
    <body>
        {cover(title, subtitle)}
        <div class="chapter"><pdf:toc /></div>
        {chapters}
        {footer()}
    </body>
    </html>
    """


# ---------------------------------------------------------------------------
# Architecture Overview
# ---------------------------------------------------------------------------

ARCH_SECTIONS: list[tuple[str, str]] = [
    (
        "1. Executive Summary",
        """
        <p>FAMS (Fortivex Attendance Management System) is a multi-tenant Human Resource and
        Attendance Management platform built on top of the open-source <b>Horilla HRMS</b> project.
        It is a monolithic, server-rendered <b>Django 5.2</b> web application with a REST API layer,
        covering the full employee lifecycle: recruitment, onboarding, attendance &amp; biometric
        capture, leave, payroll, performance management, assets, helpdesk, and offboarding.</p>
        <p>The codebase is organized as roughly 35 self-contained Django "apps" (one per business
        domain), sharing a single PostgreSQL/SQLite database, a common authentication and
        company-scoped permission layer, and a shared theming/UI framework. The same codebase ships
        two deployment targets: a self-hosted Docker Compose stack (Postgres + Redis + Nginx +
        Gunicorn) and a serverless deployment on Vercel.</p>
        <div class="note">This document describes the technical architecture as of the latest commit
        on the <code>main</code> branch. It is intended for trainers, implementation partners, and
        engineering teams evaluating or extending the system &mdash; not for end users (see the
        separate <i>FAMS Admin Guide</i> and <i>FAMS User Guide</i> for operational instructions).</div>
        """,
    ),
    (
        "2. Technology Stack",
        """
        <table>
        <tr><th>Layer</th><th>Technology</th></tr>
        <tr><td>Language / Runtime</td><td>Python 3.12</td></tr>
        <tr><td>Web Framework</td><td>Django 5.2 (server-rendered templates + Django REST Framework API)</td></tr>
        <tr><td>API Auth</td><td>djangorestframework-simplejwt (JWT), drf-yasg (Swagger/OpenAPI docs)</td></tr>
        <tr><td>Primary Database</td><td>PostgreSQL 16 (production/Docker); SQLite fallback for local dev / Vercel default</td></tr>
        <tr><td>Cache Layer</td><td>Redis 7 via django-redis (optional &ndash; falls back to Django LocMem cache when <code>REDIS_URL</code> is unset)</td></tr>
        <tr><td>Background Jobs</td><td>APScheduler (django-apscheduler) &ndash; in-process scheduled/periodic tasks, no separate worker/broker</td></tr>
        <tr><td>Static Files</td><td>WhiteNoise (compressed, content-hashed static file serving from the app server itself)</td></tr>
        <tr><td>Media / File Storage</td><td>Local filesystem by default; Amazon S3 (private, signed URLs) or Google Cloud Storage when configured</td></tr>
        <tr><td>Web Server (self-hosted)</td><td>Gunicorn (WSGI) behind Nginx reverse proxy</td></tr>
        <tr><td>Web Server (serverless)</td><td>Vercel Python runtime invoking <code>horilla/wsgi.py</code> as a serverless function</td></tr>
        <tr><td>Frontend</td><td>Server-rendered Django templates, jQuery-era JS, custom "Horilla theme" component library (no SPA framework)</td></tr>
        <tr><td>PDF Generation</td><td>xhtml2pdf, pdfkit, PyMuPDF, reportlab, pyHanko (digital signing) &ndash; payslips, reports, guides</td></tr>
        <tr><td>Containerization</td><td>Docker (multi-stage build), Docker Compose (dev &amp; prod overlays)</td></tr>
        <tr><td>Change Tracking</td><td>django-simple-history + django-auditlog (opt-in, per-model audit trail)</td></tr>
        </table>
        """,
    ),
    (
        "3. High-Level Architecture",
        """
        <p>FAMS follows a classic monolithic Django architecture: a single WSGI application serves
        both server-rendered HTML views and a JSON REST API, backed by one relational database.
        There is no microservices split and no message broker &mdash; background work runs as
        in-process scheduled jobs rather than a distributed task queue.</p>
        <div class="box">
        <div class="layer-title">Client Layer</div>
        Browser (server-rendered HTML + jQuery) &middot; Mobile/3rd-party clients via REST/JWT API
        &middot; Biometric hardware terminals (ZKTeco/pyzk, Anviz, Dahua, eTimeOffice, COSEC)
        </div>
        <div class="box">
        <div class="layer-title">Edge / Delivery</div>
        Nginx reverse proxy (self-hosted) or Vercel Edge Network (serverless) &middot;
        WhiteNoise-served static assets &middot; TLS termination
        </div>
        <div class="box">
        <div class="layer-title">Application Layer &ndash; Django (horilla project)</div>
        Middleware chain (security, sessions, company context, 2FA, audit log) &rarr;
        URL routing (per-app <code>urls.py</code>) &rarr; Class-based &amp; function views &rarr;
        Forms/Serializers &rarr; ORM Models &middot; ~35 domain apps (see Section 5)
        </div>
        <div class="box">
        <div class="layer-title">Integration Layer</div>
        LDAP / Microsoft 365 (Outlook) SSO &middot; WhatsApp messaging &middot; Google Calendar
        (Meet) &amp; Google Drive (backups) &middot; SMTP email &middot; Biometric device SDKs &middot;
        Face detection &amp; geofencing services
        </div>
        <div class="box">
        <div class="layer-title">Data &amp; Persistence Layer</div>
        PostgreSQL / SQLite (system of record) &middot; Redis (cache, optional) &middot;
        Local disk / Amazon S3 / Google Cloud Storage (media &amp; documents) &middot;
        APScheduler job store (DB-backed)
        </div>
        <p>Requests flow top-to-bottom through this stack; there is no separate API gateway or
        service mesh &mdash; Django's middleware pipeline and URL dispatcher perform that role.</p>
        """,
    ),
    (
        "4. Multi-Tenancy &amp; Permission Model",
        """
        <p>FAMS is <b>multi-company (multi-tenant) by design</b>: a single deployment can host several
        companies' data in one database, with data and permissions scoped per company.</p>
        <h2>4.1 Company context resolution</h2>
        <p><code>base.middleware.CompanyMiddleware</code> runs on every request. It determines the
        "current company" for the logged-in user &mdash; from the session (if the user has switched
        companies via the UI), otherwise from the employee's work-info record &mdash; and stores it
        in a thread-local/context variable that the rest of the request lifecycle reads from.</p>
        <h2>4.2 Company-scoped permissions</h2>
        <p><code>base.auth_backends.CompanyScopedBackend</code> replaces Django's default
        <code>ModelBackend</code> in <code>AUTHENTICATION_BACKENDS</code>. When the
        <code>COMPANY_SCOPED_PERMISSIONS</code> feature flag is enabled (default: on), a user's
        effective Django group permissions are resolved <i>per company</i> via
        <code>CompanyGroupAssignment</code> rather than globally:</p>
        <table>
        <tr><th>Context</th><th>Permissions resolved from</th></tr>
        <tr><td>Specific company selected</td><td>Groups assigned to the user for that company only</td></tr>
        <tr><td>"All companies" view</td><td>Union of the user's assignments across every company (data still row-filtered per company by the manager layer)</td></tr>
        <tr><td>No session/request context (API, JWT, shell, scheduler)</td><td>User's work-info company; falls back to the union of all assignments if none</td></tr>
        </table>
        <p>The union fallback never grants a permission the user doesn't already hold in <i>some</i>
        company, so it cannot be used to escalate privileges &mdash; it only prevents accidental
        lockouts in session-less code paths. The flag is an instant rollback switch: setting
        <code>COMPANY_SCOPED_PERMISSIONS=False</code> reverts to Django's stock global group
        permissions with no code changes.</p>
        <p>Superusers bypass this backend entirely, as with standard Django auth.</p>
        """,
    ),
    (
        "5. Application Modules",
        """
        <p>The project is decomposed into focused Django apps under a single project package
        (<code>horilla/</code>). Each owns its own models, views, migrations, and templates.</p>
        <table>
        <tr><th>App</th><th>Responsibility</th></tr>
        <tr><td><code>base</code></td><td>Core cross-cutting concerns: company/multi-tenancy, auth backends, middleware, shared context processors, dashboards</td></tr>
        <tr><td><code>horilla_auth</code></td><td>Custom user model (<code>HorillaUser</code>) and authentication</td></tr>
        <tr><td><code>employee</code></td><td>Employee master data, org structure, work info, documents</td></tr>
        <tr><td><code>attendance</code></td><td>Clock-in/out, shift &amp; work-type tracking, late-come/early-out rules</td></tr>
        <tr><td><code>biometric</code></td><td>Integrations with ZKTeco (pyzk), Anviz, Dahua, eTimeOffice, COSEC biometric terminals</td></tr>
        <tr><td><code>facedetection</code></td><td>Face-based attendance capture/verification</td></tr>
        <tr><td><code>geofencing</code></td><td>Location-restricted attendance (geofenced check-in/out)</td></tr>
        <tr><td><code>leave</code></td><td>Leave types, policies, requests, approvals, balances</td></tr>
        <tr><td><code>payroll</code></td><td>Salary structures, payslip generation, tax/compliance calculations</td></tr>
        <tr><td><code>daily_report</code></td><td>Employee daily activity/status reporting</td></tr>
        <tr><td><code>recruitment</code></td><td>Job postings, candidate pipeline, interview stages</td></tr>
        <tr><td><code>onboarding</code> / <code>offboarding</code></td><td>Structured joiner/leaver workflows and tasks</td></tr>
        <tr><td><code>pms</code></td><td>Performance Management &ndash; goals, KRAs, reviews, feedback</td></tr>
        <tr><td><code>project</code></td><td>Project &amp; task tracking tied to employees</td></tr>
        <tr><td><code>asset</code></td><td>Company asset allocation and return tracking</td></tr>
        <tr><td><code>helpdesk</code></td><td>Internal ticketing system for HR support requests</td></tr>
        <tr><td><code>report</code></td><td>Cross-module reporting &amp; exports</td></tr>
        <tr><td><code>horilla_api</code></td><td>DRF-based REST API surface (JWT-authenticated) with Swagger docs</td></tr>
        <tr><td><code>horilla_views</code>, <code>horilla_widgets</code>, <code>horilla_theme</code></td><td>Shared generic list/detail/CRUD view scaffolding and the UI component/theme library</td></tr>
        <tr><td><code>horilla_automations</code></td><td>Configurable rule-based automation (trigger &rarr; condition &rarr; action)</td></tr>
        <tr><td><code>horilla_audit</code></td><td>Opt-in per-model audit trail registry (built on django-auditlog)</td></tr>
        <tr><td><code>horilla_documents</code></td><td>Document upload/management shared across modules</td></tr>
        <tr><td><code>horilla_backup</code></td><td>Scheduled backups to local disk or Google Drive; Postgres dump support</td></tr>
        <tr><td><code>horilla_ldap</code></td><td>LDAP/Active Directory authentication integration</td></tr>
        <tr><td><code>outlook_auth</code></td><td>Microsoft 365 / Outlook OAuth SSO integration</td></tr>
        <tr><td><code>horilla_meet</code></td><td>Google Calendar-based meeting scheduling</td></tr>
        <tr><td><code>whatsapp</code></td><td>WhatsApp messaging integration (notifications/flows)</td></tr>
        <tr><td><code>notifications</code></td><td>In-app notification inbox (django-notifications)</td></tr>
        <tr><td><code>accessibility</code></td><td>Accessibility preferences middleware/UI</td></tr>
        <tr><td><code>horilla_tour</code></td><td>Guided in-app onboarding tours</td></tr>
        <tr><td><code>horilla_dbtemplate</code></td><td>Database-backed template override loader (lets admins customize templates without redeploying)</td></tr>
        <tr><td><code>horilla_crumbs</code></td><td>Breadcrumb navigation generation</td></tr>
        <tr><td><code>dynamic_fields</code></td><td>Admin-configurable custom fields on existing models</td></tr>
        </table>
        """,
    ),
    (
        "6. Data Layer",
        """
        <h2>6.1 Database</h2>
        <p>PostgreSQL is the production database (via <code>DATABASE_URL</code>, with
        <code>CONN_MAX_AGE=60</code> for connection pooling). When no <code>DATABASE_URL</code> is
        set, Django falls back to a local SQLite file &mdash; used for quick local development and
        as the Vercel default (Vercel deployments are expected to point at an external managed
        Postgres via <code>DATABASE_URL</code>, since serverless functions have no persistent disk).</p>
        <h2>6.2 Caching</h2>
        <p>Redis is used via <code>django-redis</code> when <code>REDIS_URL</code> is configured
        (the Docker Compose stack always sets it). Without it, Django's default in-memory cache is
        used automatically &mdash; caching is additive, not a hard dependency.</p>
        <h2>6.3 File &amp; Media Storage</h2>
        <p>Configurable via Django's <code>STORAGES</code> setting, resolved at startup in
        <code>horilla/settings/addons.py</code>:</p>
        <ul>
        <li><b>Default:</b> local filesystem (<code>MEDIA_ROOT</code>), served by Django in dev.</li>
        <li><b>Amazon S3:</b> enabled automatically when <code>AWS_ACCESS_KEY_ID</code> is present.
        Uses <code>PrivateMediaStorage</code> (a private-ACL, signed-URL S3 backend defined in
        <code>horilla/horilla_backends.py</code>) so uploaded documents are never publicly readable
        by guessing a URL.</li>
        <li><b>Google Cloud Storage:</b> supported as an alternative backend
        (<code>horilla_backends_gcp.py</code>, <code>google-cloud-storage</code> dependency).</li>
        </ul>
        <p>Static assets (CSS/JS/images) are handled separately from media, always via WhiteNoise
        with compressed, content-hashed filenames for cache-busting
        (<code>whitenoise.storage.CompressedManifestStaticFilesStorage</code>, subclassed as
        <code>NonStrictWhiteNoiseStorage</code> to tolerate missing source maps).</p>
        <h2>6.4 Change History &amp; Audit</h2>
        <p><code>django-simple-history</code> provides model-level version history broadly across the
        app. <code>horilla_audit</code> layers a separate, explicitly opt-in audit trail
        (<code>AUDITLOG_INCLUDE_ALL_MODELS = False</code>) on top of django-auditlog, whitelisting
        sensitive models such as Employee, EmployeeWorkInformation, and EmployeeBankDetails by
        default.</p>
        """,
    ),
    (
        "7. Authentication, Security &amp; Middleware",
        """
        <h2>7.1 Authentication</h2>
        <p>A custom user model, <code>horilla_auth.HorillaUser</code>
        (<code>AUTH_USER_MODEL</code>), backs standard Django session-based login for the web UI and
        JWT (via <code>djangorestframework-simplejwt</code>, 60-minute access tokens) for the REST
        API. Optional SSO integrations extend this: LDAP/Active Directory (<code>horilla_ldap</code>)
        and Microsoft 365 / Outlook OAuth (<code>outlook_auth</code>). Two-factor authentication is
        available as a feature flag (<code>TWO_FACTORS_AUTHENTICATION</code>), enforced by
        <code>TwoFactorAuthMiddleware</code>.</p>
        <h2>7.2 Middleware pipeline (in order)</h2>
        <p>Django SecurityMiddleware &rarr; WhiteNoise &rarr; Sessions &rarr; Common &rarr; CORS
        headers &rarr; simple-history request context &rarr; Locale &rarr; CSRF &rarr;
        Authentication &rarr; Messages &rarr; X-Frame-Options &rarr;
        <b>CompanyMiddleware</b> (multi-tenant context) &rarr; <b>ForcePasswordChangeMiddleware</b>
        &rarr; <b>TwoFactorAuthMiddleware</b> &rarr; AccessibilityMiddleware &rarr;
        MethodNotAllowedMiddleware &rarr; SVGSecurityMiddleware (sanitizes uploaded SVGs) &rarr;
        MissingParameterMiddleware &rarr; Auditlog.</p>
        <h2>7.3 Production security gates</h2>
        <p><code>horilla/settings/security.py</code> fails startup closed when running with
        <code>DEBUG=False</code> or <code>HORILLA_ENV=production</code>: it refuses to boot if
        <code>SECRET_KEY</code>, <code>ALLOWED_HOSTS</code>, or <code>DB_INIT_PASSWORD</code> are
        left at known-insecure placeholder values. When not in DEBUG, it also applies secure defaults
        (secure session/CSRF cookies, <code>SECURE_CONTENT_TYPE_NOSNIFF</code>,
        referrer policy, optional HSTS/SSL-redirect, trust of
        <code>X-Forwarded-Proto/Host/Port</code> for reverse-proxy deployments such as Vercel/Nginx).</p>
        <h2>7.4 Permissions</h2>
        <p>See Section 4 for the company-scoped permission backend. Individual object/action
        permissions still use Django's standard <code>auth.Permission</code>/group model underneath;
        FAMS only changes <i>which company's</i> group assignments are consulted.</p>
        """,
    ),
    (
        "8. External Integrations",
        """
        <table>
        <tr><th>Integration</th><th>Purpose</th><th>App</th></tr>
        <tr><td>LDAP / Active Directory</td><td>Enterprise SSO login</td><td><code>horilla_ldap</code></td></tr>
        <tr><td>Microsoft 365 / Outlook</td><td>OAuth SSO, calendar</td><td><code>outlook_auth</code></td></tr>
        <tr><td>Google Calendar</td><td>Meeting scheduling ("Horilla Meet")</td><td><code>horilla_meet</code></td></tr>
        <tr><td>Google Drive</td><td>Off-site database backup storage</td><td><code>horilla_backup</code></td></tr>
        <tr><td>Amazon S3 / GCS</td><td>Private media/document object storage</td><td><code>horilla</code> core settings</td></tr>
        <tr><td>WhatsApp</td><td>Outbound notifications / conversational flows</td><td><code>whatsapp</code></td></tr>
        <tr><td>SMTP</td><td>Transactional email (leave approvals, invites, password resets); per-company override via <code>DynamicEmailConfiguration</code>, env-var fallback</td><td><code>base.backends</code></td></tr>
        <tr><td>Biometric terminals</td><td>ZKTeco (pyzk), Anviz, Dahua, eTimeOffice, COSEC device polling for attendance punches</td><td><code>biometric</code></td></tr>
        <tr><td>Face detection</td><td>Camera-based attendance verification</td><td><code>facedetection</code></td></tr>
        <tr><td>Geofencing</td><td>Location-bounded attendance via <code>geopy</code></td><td><code>geofencing</code></td></tr>
        <tr><td>AWS Cognito</td><td>Reserved for a planned future SSO integration; settings are declared but not yet wired into any auth backend</td><td><code>horilla/settings/addons.py</code></td></tr>
        </table>
        """,
    ),
    (
        "9. Background Processing",
        """
        <p>FAMS does <b>not</b> use a separate task queue/broker (no Celery, no RabbitMQ). Scheduled
        and periodic work &mdash; e.g. recurring backups, reminder emails, biometric device polling
        &mdash; runs via <b>APScheduler</b> (<code>django-apscheduler</code>), executing in-process
        within the Django application server and persisting job state to the database. This keeps the
        deployment footprint small (no extra worker process/infrastructure to run) at the cost of jobs
        being tied to an application server's lifecycle rather than an independently scalable worker
        fleet.</p>
        """,
    ),
    (
        "10. Deployment Architectures",
        """
        <p>The same codebase supports two deployment models, selected by which environment variables
        are present &mdash; there is no separate branch or build for either.</p>
        <h2>10.1 Self-hosted (Docker Compose)</h2>
        <p>A multi-stage Dockerfile (Python 3.12-slim builder + minimal runtime image, non-root
        <code>appuser</code>) produces a Gunicorn-served image. <code>docker-compose.yml</code>
        defines the development stack; <code>docker-compose.prod.yml</code> is a production overlay
        (Docker Compose v2.24+ <code>!override</code>/<code>!reset</code> merge) that enforces
        required secrets via <code>${VAR:?error}</code> and disables the bind-mounted source volume.</p>
        <table>
        <tr><th>Service</th><th>Role</th></tr>
        <tr><td><code>web</code></td><td>Django app via Gunicorn, port 8000, liveness probe at <code>/health/</code></td></tr>
        <tr><td><code>db</code></td><td>PostgreSQL 16</td></tr>
        <tr><td><code>redis</code></td><td>Redis 7, AOF persistence, password-protected</td></tr>
        <tr><td><code>nginx</code></td><td>Reverse proxy for static files + <code>/media/</code> auth passthrough (production profile only)</td></tr>
        </table>
        <p>Static files and media are named Docker volumes shared between <code>web</code> and
        <code>nginx</code>; <code>/media/</code> is deliberately proxied through Django (not served
        directly by Nginx) so private-media access control is enforced.</p>
        <h2>10.2 Serverless (Vercel)</h2>
        <p><code>vercel.json</code> routes requests to <code>horilla/wsgi.py</code> as a Python
        serverless function (region <code>sfo1</code>, 60s max duration). Because serverless functions
        have no persistent disk and a hard deployment-bundle size limit:</p>
        <ul>
        <li>The database must be an external managed Postgres reachable via <code>DATABASE_URL</code>.</li>
        <li>Media storage must be S3 or GCS (see Section 6.3) &mdash; local disk storage doesn't
        survive across invocations.</li>
        <li><code>vercel_build_hook.py</code> runs post-install to strip build-time-only tooling
        (pip/setuptools/wheel), unused Google API discovery documents (~97MB), unused AWS service
        definitions from botocore (~80MB, keeps only S3), and third-party test directories from
        site-packages &mdash; keeping the function under Vercel's 225MB bundle limit.</li>
        <li>Dependency resolution on Vercel reads <code>pyproject.toml</code> (kept in sync with
        <code>requirements.txt</code>) via <code>uv</code>, with <code>[tool.uv] package = false</code>
        since this is an application, not an installable library.</li>
        </ul>
        <h2>10.3 Health &amp; readiness endpoints</h2>
        <table>
        <tr><th>Endpoint</th><th>Checks</th><th>Use</th></tr>
        <tr><td><code>/health/</code></td><td>None (process is up)</td><td>Docker <code>HEALTHCHECK</code>, liveness probes</td></tr>
        <tr><td><code>/ready/</code></td><td>Database connectivity; Redis cache round-trip if <code>REDIS_URL</code> is set</td><td>Readiness/orchestration probes</td></tr>
        </table>
        """,
    ),
    (
        "11. Codebase Layout",
        """
        <p>Flat, per-domain app layout at the repository root (no <code>src/</code> nesting):</p>
        <table>
        <tr><th>Path</th><th>Contents</th></tr>
        <tr><td><code>horilla/</code></td><td>Django project package: settings (<code>settings/base.py</code>, <code>addons.py</code>, <code>security.py</code>, <code>local_settings.py</code>), root <code>urls.py</code>, WSGI/ASGI entrypoints, custom middleware, storage backends</td></tr>
        <tr><td><code>&lt;domain&gt;/</code> (35 dirs)</td><td>One Django app per business domain (Section 5); each has its own <code>models.py</code>, <code>views.py</code>/<code>cbv/</code>, <code>urls.py</code>, <code>migrations/</code>, <code>templates/</code></td></tr>
        <tr><td><code>templates/</code>, <code>horilla_theme/</code></td><td>Global templates and the shared UI component/theme library</td></tr>
        <tr><td><code>static/</code>, <code>staticfiles/</code></td><td>Source static assets and WhiteNoise's collected/compressed output</td></tr>
        <tr><td><code>docker/</code></td><td>Nginx config, Gunicorn config, container entrypoint script</td></tr>
        <tr><td><code>docs/</code></td><td>Generated PDF documentation (this document, admin/user guides) and their generator scripts</td></tr>
        <tr><td><code>load_data/</code></td><td>Fixture/seed data for initial setup</td></tr>
        <tr><td><code>manage.py</code></td><td>Django management CLI entrypoint</td></tr>
        </table>
        <div class="note">Two integration branches exist upstream (Horilla convention): a stable
        default branch and an active <code>dev</code> integration branch for contributions. Refer to
        the repository's branch protection rules for FAMS-specific policy.</div>
        """,
    ),
    (
        "12. Appendix: Key Environment Variables",
        """
        <p>Configuration follows twelve-factor conventions via <code>django-environ</code>, read from
        the process environment first and a local <code>.env</code> file as fallback.</p>
        <table>
        <tr><th>Variable</th><th>Purpose</th></tr>
        <tr><td><code>DEBUG</code>, <code>HORILLA_ENV</code></td><td>Toggle production security gates (Section 7.3)</td></tr>
        <tr><td><code>SECRET_KEY</code>, <code>ALLOWED_HOSTS</code>, <code>CSRF_TRUSTED_ORIGINS</code></td><td>Core Django security config</td></tr>
        <tr><td><code>DATABASE_URL</code> (or <code>DB_ENGINE</code>/<code>DB_NAME</code>/...)</td><td>Database connection</td></tr>
        <tr><td><code>REDIS_URL</code></td><td>Enables Redis cache backend</td></tr>
        <tr><td><code>AWS_ACCESS_KEY_ID</code>, <code>AWS_SECRET_ACCESS_KEY</code>, <code>AWS_STORAGE_BUCKET_NAME</code>, <code>AWS_S3_REGION_NAME</code>/<code>AWS_REGION</code></td><td>Enables S3 private media storage</td></tr>
        <tr><td><code>SMTP_HOST</code>, <code>SMTP_PORT</code>, <code>SMTP_USERNAME</code>, <code>SMTP_PASSWORD</code>, <code>SMTP_USE_TLS</code>, <code>SMTP_FROM</code></td><td>Default outgoing email (overridable per company)</td></tr>
        <tr><td><code>DB_INIT_PASSWORD</code></td><td>Database setup/initialization secret; must be changed in production</td></tr>
        <tr><td><code>COMPANY_SCOPED_PERMISSIONS</code></td><td>Toggles per-company permission scoping (Section 4.2)</td></tr>
        <tr><td><code>AUTH_LDAP_SERVER_URI</code>, <code>AUTH_LDAP_BIND_DN</code>, <code>AUTH_LDAP_BIND_PASSWORD</code></td><td>LDAP integration</td></tr>
        <tr><td><code>SECURE_SSL_REDIRECT</code>, <code>SECURE_HSTS_SECONDS</code></td><td>Opt-in HTTPS enforcement</td></tr>
        </table>
        <p>See <code>.env.dist</code> / <code>.env.example</code> in the repository root for the full,
        current list with descriptions.</p>
        """,
    ),
]


def main() -> None:
    html = build(
        "FAMS System Architecture",
        "Technical Overview for Trainers &amp; Implementation Partners",
        ARCH_SECTIONS,
    )
    out_path = ROOT / "docs" / "FAMS_System_Architecture.pdf"
    with open(out_path, "wb") as f:
        result = pisa.CreatePDF(html, dest=f)
    if result.err:
        raise SystemExit(f"PDF generation failed with {result.err} error(s)")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
