"""
Regenerates docs/FAMS_Admin_Guide.pdf and docs/FAMS_User_Guide.pdf.

Run from the project root with the project venv active:

    python docs/generate_guides.py

Uses xhtml2pdf (the same PDF library the app itself uses for payslips/
reports - see base/methods.py's link_callback) so no extra dependency is
needed. Content lives in this file as plain HTML strings; there's no
other source of truth for the guides, so update ADMIN_SECTIONS /
USER_SECTIONS here and re-run rather than editing the PDFs directly.
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
    p { margin: 4px 0 8px 0; text-align: justify; }
    ul, ol { margin: 4px 0 10px 0; padding-left: 18px; }
    li { margin-bottom: 3px; }
    table { width: 100%; border-collapse: collapse; margin: 8px 0 14px 0; font-size: 9.5pt; }
    th, td { border: 1px solid #cccccc; padding: 5px 7px; text-align: left; vertical-align: top; }
    th { background-color: #eef2f7; color: #0f2a4a; }
    .note { background-color: #fff7e6; border-left: 3px solid #e8a33d; padding: 6px 10px; margin: 8px 0; font-size: 9.5pt; }
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
        <p class="meta">Fortivex Attendance Management System (FAMS)</p>
    </div>
    """


def footer() -> str:
    return '<div id="footer_content">FAMS Guide &middot; Page <pdf:pagenumber /> of <pdf:pagecount /></div>'


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
# Admin Guide
# ---------------------------------------------------------------------------

ADMIN_SECTIONS: list[tuple[str, str]] = [
    (
        "1. Getting Started",
        """
        <p>FAMS is accessed from a web browser at your organization's FAMS URL. Sign in with the
        email and password your system administrator provided. An administrator account can see
        every menu described in this guide; a regular employee sees only the Employee Self-Service
        items covered in the separate <i>FAMS User Guide</i>.</p>
        <p>Access to each module is controlled by <b>User Groups &amp; Permissions</b>
        (Settings &rarr; Users &amp; Permissions), so a colleague with an "HR" or "Manager" role may see
        a subset of the screens below rather than the full administrator set.</p>
        <div class="note">Two-factor login and password reset are available from the sign-in page if enabled
        for your organization.</div>
        """,
    ),
    (
        "2. Company &amp; System Settings",
        """
        <p>Before onboarding employees, configure the company itself under <b>Settings</b>:</p>
        <ul>
            <li><b>Company Profile</b> &ndash; legal name, address, logo, and date/time format used across the app.</li>
            <li><b>Departments &amp; Job Roles</b> &ndash; the org structure employees are assigned into.</li>
            <li><b>Work Types &amp; Shifts</b> &ndash; the schedules attendance and payroll are calculated against.</li>
            <li><b>Users &amp; Permissions</b> &ndash; create user groups (e.g. Admin, HR, Manager) and assign granular
            per-module permissions to each; every staff login should map to a group here rather than being made a
            superuser.</li>
            <li><b>Mail Server</b> &ndash; SMTP settings used for notification emails (leave approvals, onboarding
            invites, password resets). Send a test email after saving to confirm delivery.</li>
            <li><b>LDAP / Microsoft (Outlook) Authentication</b> &ndash; optional single sign-on integration if your
            organization uses Active Directory or Microsoft 365 accounts.</li>
            <li><b>Backup</b> &ndash; schedule or trigger a database backup to local storage or Google Drive.</li>
            <li><b>Guided Tours</b> &ndash; enable in-app onboarding walkthroughs shown to new users.</li>
        </ul>
        """,
    ),
    (
        "3. Employee Management",
        """
        <p>Under <b>Employee</b>, add each staff member's profile: personal details, department, job
        position, reporting manager, and work schedule. The <b>Organization Chart</b> view renders the
        reporting hierarchy automatically once managers are assigned.</p>
        <ul>
            <li><b>Work Requests</b> &ndash; approve or reject employee requests to change work type or shift.</li>
            <li><b>Work Schedules</b> &ndash; define the weekly working pattern each work type follows.</li>
            <li><b>Policies &amp; Discipline</b> &ndash; publish company policy documents and record disciplinary actions.</li>
        </ul>
        <p>Each employee record has an associated login; disable a login (rather than deleting the employee
        record) when someone leaves, so historical attendance/payroll data is preserved.</p>
        """,
    ),
    (
        "4. Attendance Management",
        """
        <p>The <b>Attendance</b> module tracks clock-in/clock-out for every employee.</p>
        <ul>
            <li><b>Attendances</b> &ndash; the full log of clock-ins across the company; filter by employee, date, or
            department.</li>
            <li><b>Attendance Requests</b> &ndash; review and approve corrections employees submit when a clock-in was
            missed or recorded incorrectly.</li>
            <li><b>Late Come Early Out</b> &ndash; a filtered view surfacing attendance exceptions for follow-up.</li>
            <li><b>Hour Account &amp; Work Records</b> &ndash; running totals of worked vs. scheduled hours per employee,
            used for overtime and payroll calculations.</li>
            <li><b>Time Policies</b> &ndash; configure grace periods, minimum working hours, and overtime rules.</li>
        </ul>
        <h2>Biometric Devices</h2>
        <p>Under Settings &rarr; Biometric Devices you can connect physical attendance hardware. FAMS supports
        Anviz, COSEC, Dahua, and eTimeOffice device brands &ndash; add the device's IP address and credentials, then
        sync; punches recorded on the device appear automatically in Attendances.</p>
        <h2>Geofencing</h2>
        <p>Under Settings &rarr; Geofencing, define one or more allowed geographic zones per company location.
        When enabled, employee clock-ins are checked against these zones and rejected if the employee is
        outside the configured radius.</p>
        <h2>Face Verification</h2>
        <p>Face-detection verification can be toggled on per company under Settings. When enabled, employees
        must complete a face-capture step as part of clocking in, reducing buddy-punching.</p>
        """,
    ),
    (
        "5. Leave Management",
        """
        <ul>
            <li><b>Leave Requests</b> &ndash; approve, reject, or reassign pending leave applications from any employee.</li>
            <li><b>Compensatory Leave Requests</b> &ndash; approve comp-off requests submitted for extra hours worked.</li>
            <li><b>Leave Allocation Request &amp; Assigned Leave</b> &ndash; grant additional leave balance to specific
            employees outside the standard policy.</li>
            <li><b>Restrict Leaves</b> &ndash; block leave applications on specific dates (e.g. month-end close, peak
            season).</li>
            <li><b>Public Holidays &amp; Company Leaves</b> &ndash; maintain the holiday calendar used to calculate
            working days.</li>
            <li><b>Configuration</b> &ndash; define leave types (annual, sick, unpaid, etc.), accrual rules, and carry
            -forward limits.</li>
        </ul>
        """,
    ),
    (
        "6. Recruitment",
        """
        <p>The <b>Recruitment</b> module manages the full hiring pipeline:</p>
        <ul>
            <li><b>Job Openings</b> &ndash; publish open positions, optionally to a public careers page.</li>
            <li><b>Candidates &amp; Pipeline</b> &ndash; track applicants through hiring stages (e.g. Applied,
            Interview, Offer, Hired) using a drag-and-drop board.</li>
            <li><b>Interview</b> &ndash; schedule interviews and record panel feedback.</li>
            <li><b>Survey</b> &ndash; attach application questionnaires to a job opening.</li>
            <li><b>Skill Zone</b> &ndash; a talent pool of candidates tagged by skill for future openings.</li>
        </ul>
        """,
    ),
    (
        "7. Onboarding",
        """
        <p>Once a candidate is marked <i>Hired</i> in Recruitment, move them into <b>Onboarding</b>:</p>
        <ul>
            <li><b>Candidates</b> &ndash; the list of hires currently in the onboarding pipeline.</li>
            <li><b>Onboarding Tasks</b> &ndash; assign checklist tasks (equipment setup, document collection,
            training) to HR, IT, or the new hire.</li>
        </ul>
        <p>FAMS emails each new hire a secure, token-based self-service link so they can create their own login
        and fill in their profile without an administrator entering it manually &ndash; you only need to review and
        approve what they submit.</p>
        """,
    ),
    (
        "8. Offboarding",
        """
        <ul>
            <li><b>Resignation Letters</b> &ndash; review resignation submissions from employees.</li>
            <li><b>Exit Process</b> &ndash; track the offboarding checklist (asset return, final settlement,
            access revocation) through to completion.</li>
        </ul>
        """,
    ),
    (
        "9. Payroll Administration",
        """
        <ul>
            <li><b>Contract</b> &ndash; define each employee's salary structure and contract terms.</li>
            <li><b>Allowances &amp; Deductions</b> &ndash; configure recurring or one-off pay components.</li>
            <li><b>Loan / Advanced Salary</b> &ndash; record employee loans and repayment schedules.</li>
            <li><b>Encashments &amp; Reimbursements</b> &ndash; process leave encashment and expense reimbursement
            claims.</li>
            <li><b>Federal Tax</b> &ndash; configure applicable tax brackets/rules.</li>
            <li><b>Payslips</b> &ndash; generate and publish payslips for a pay period; once published, employees can
            view and download their own from their dashboard.</li>
        </ul>
        <div class="note">Run payroll configuration changes (tax, allowances) before generating payslips for the
        period &ndash; published payslips are not automatically recalculated.</div>
        """,
    ),
    (
        "10. Performance Management",
        """
        <ul>
            <li><b>Objectives &amp; Key Results</b> &ndash; create OKRs for employees or teams and track progress.</li>
            <li><b>360&deg; Feedback</b> &ndash; configure feedback cycles where employees review peers, managers,
            and reports.</li>
            <li><b>Meetings</b> &ndash; schedule and log 1:1 or performance review meetings.</li>
            <li><b>Bonus Points</b> &ndash; award recognition points tied to performance.</li>
        </ul>
        """,
    ),
    (
        "11. Projects &amp; Timesheets",
        """
        <ul>
            <li><b>Projects &amp; Tasks</b> &ndash; create projects, break them into tasks, and assign employees.</li>
            <li><b>Timesheet</b> &ndash; review hours employees have logged against tasks, used for billing/reporting.</li>
        </ul>
        """,
    ),
    (
        "12. Asset Management",
        """
        <ul>
            <li><b>Assets &amp; Asset Batches</b> &ndash; maintain the inventory of company equipment, individually or
            in batches (e.g. 20 identical laptops).</li>
            <li><b>Requests &amp; Allocation</b> &ndash; approve employee asset requests and record what has been
            issued to whom.</li>
            <li><b>Asset History</b> &ndash; full audit trail of an asset's allocation and return history.</li>
        </ul>
        """,
    ),
    (
        "13. Helpdesk",
        """
        <ul>
            <li><b>Tickets</b> &ndash; view and respond to support tickets raised by any employee, assign them to the
            right team, and track status to resolution.</li>
            <li><b>FAQs</b> &ndash; maintain the self-service FAQ library shown to employees before they raise a
            ticket.</li>
        </ul>
        """,
    ),
    (
        "14. Daily Reports",
        """
        <p>Under <b>Daily Report</b>, managers and administrators with the appropriate permission can review the
        work-report entries employees submit for each working day, alongside those of their direct reports.
        Use this to spot-check daily output without waiting for a weekly or monthly review cycle.</p>
        """,
    ),
    (
        "15. Reports",
        """
        <p>The <b>Reports</b> menu provides pivot-table style reporting across Employee, Leave, Payroll, Asset,
        and Performance data &ndash; filter, group, and export to build the recurring reports your organization
        needs without a separate BI tool.</p>
        """,
    ),
    (
        "16. Getting Help",
        """
        <p>If something in this guide doesn't match what you see on screen, check that your user group has the
        relevant permission enabled under Settings &rarr; Users &amp; Permissions, and that you are looking at the
        correct company if your FAMS instance manages more than one. For technical issues, contact your FAMS
        system administrator or raise a Helpdesk ticket.</p>
        """,
    ),
]


# ---------------------------------------------------------------------------
# User (Employee) Guide
# ---------------------------------------------------------------------------

USER_SECTIONS: list[tuple[str, str]] = [
    (
        "1. Signing In",
        """
        <p>Open your organization's FAMS web address in a browser and sign in with the email and password
        your administrator gave you. If your organization uses Microsoft 365 or Active Directory sign-in,
        use the matching button on the login page instead of typing a password.</p>
        <p>If you're a new hire, you may instead receive a personal welcome email with a secure setup link -
        follow it to create your password and confirm your profile details.</p>
        """,
    ),
    (
        "2. Your Dashboard",
        """
        <p>After signing in you land on your personal dashboard, which summarizes:</p>
        <ul>
            <li>Today's attendance status and quick clock-in/clock-out button.</li>
            <li>Your current leave balance and any pending requests.</li>
            <li>Your latest payslip.</li>
            <li>Your active performance objectives.</li>
            <li>Upcoming holidays, meetings, and announcements.</li>
        </ul>
        <p>Use the sidebar to navigate to the individual modules described in this guide. Only the modules
        your organization has enabled and given you access to will appear.</p>
        """,
    ),
    (
        "3. Attendance",
        """
        <p>Go to <b>Attendance &rarr; My Attendances</b> to clock in and out and to see your own history.</p>
        <ul>
            <li>Click <b>Clock In</b> when you start work and <b>Clock Out</b> when you finish; the time is
            recorded automatically.</li>
            <li>If your organization has geofencing enabled, clocking in only works while you're within the
            approved company location - if you get a location error while genuinely on-site, contact your
            administrator.</li>
            <li>If face verification is enabled, you'll be asked to look at your camera briefly as part of
            clocking in.</li>
            <li>If you forgot to clock in/out, or a time was recorded incorrectly, submit an <b>Attendance
            Request</b> explaining the correction needed; it goes to your manager for approval.</li>
        </ul>
        """,
    ),
    (
        "4. Leave",
        """
        <p>Go to <b>Leave &rarr; My Leave Requests</b> to apply for time off.</p>
        <ul>
            <li>Click <b>New Request</b>, choose a leave type, the date range, and add a reason, then submit.
            You'll see the request's status (pending/approved/rejected) update once your manager reviews it.</li>
            <li>Worked extra hours you'd like converted to a day off later? Use <b>Compensatory Leave
            Requests</b> instead.</li>
            <li>Check the <b>Public Holidays</b> and <b>Company Leaves</b> calendars before planning time off,
            since those days don't need to be requested separately.</li>
            <li>Your available balance per leave type is shown at the top of the My Leave Requests page.</li>
        </ul>
        """,
    ),
    (
        "5. Daily Report",
        """
        <p>If your team uses daily reporting, go to <b>Daily Report &rarr; My Reports</b> and add an entry for
        each working day summarizing what you worked on. Your manager can see your submitted reports alongside
        those of the rest of the team.</p>
        """,
    ),
    (
        "6. Your Profile &amp; Work Requests",
        """
        <ul>
            <li>Update your contact details, emergency contact, and profile photo from <b>Employee &rarr; My
            Profile</b>.</li>
            <li>Need a different shift or work type temporarily or permanently? Submit a <b>Work Request</b> and
            your manager will approve or reject it.</li>
            <li>Company policies and any disciplinary records that apply to you are visible under
            <b>Policies &amp; Discipline</b>.</li>
        </ul>
        """,
    ),
    (
        "7. Payroll",
        """
        <p>Go to <b>Payroll &rarr; Payslips</b> to view and download your payslip once it's published for a pay
        period. If you believe there's an error on your payslip, raise it with HR or via a Helpdesk ticket
        rather than requesting a change directly.</p>
        """,
    ),
    (
        "8. Assets",
        """
        <p>Go to <b>Assets</b> to request equipment (e.g. a laptop, monitor, or phone) you need for work. Track
        the status of your request and see what's currently allocated to you, including return dates for
        loaned equipment.</p>
        """,
    ),
    (
        "9. Performance",
        """
        <ul>
            <li>View and update progress on your <b>Objectives &amp; Key Results</b> as you make progress
            through a review period.</li>
            <li>If a 360&deg; feedback cycle is open, you'll be prompted to submit feedback for peers, your
            manager, or your reports.</li>
            <li>Scheduled 1:1 or review <b>Meetings</b> with your manager appear here too.</li>
        </ul>
        """,
    ),
    (
        "10. Projects &amp; Timesheet",
        """
        <p>If you're assigned to any projects, go to <b>Project &rarr; Tasks</b> to see and update your assigned
        tasks, and to <b>Timesheet</b> to log hours worked against each task.</p>
        """,
    ),
    (
        "11. Helpdesk",
        """
        <p>Have a question or an issue with any part of FAMS (or a workplace matter generally handled by HR/IT)?
        Check the <b>FAQs</b> first, then raise a <b>Ticket</b> under Helpdesk if you can't find an answer.
        You can track replies and status on the same ticket.</p>
        """,
    ),
    (
        "12. Notifications &amp; Theme",
        """
        <p>The bell icon in the top bar shows notifications for approvals, mentions, and reminders relevant to
        you. You can switch between light and dark theme from the same top bar to suit your preference.</p>
        """,
    ),
    (
        "13. Getting Help",
        """
        <p>If a menu described in this guide doesn't appear for you, your organization may not have that
        module enabled, or your account may not have access to it - check with your manager or administrator.
        For anything else, raise a Helpdesk ticket.</p>
        """,
    ),
]


def render_pdf(html: str, out_path: Path) -> None:
    with open(out_path, "wb") as f:
        result = pisa.CreatePDF(html, dest=f)
    if result.err:
        raise RuntimeError(f"Failed to render {out_path.name}: {result.err} error(s)")
    print(f"generate_guides: wrote {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)

    admin_html = build(
        "FAMS Admin Guide",
        "A complete walkthrough of every module for administrators and HR",
        ADMIN_SECTIONS,
    )
    render_pdf(admin_html, docs_dir / "FAMS_Admin_Guide.pdf")

    user_html = build(
        "FAMS User Guide",
        "Everything employees need to use FAMS day to day",
        USER_SECTIONS,
    )
    render_pdf(user_html, docs_dir / "FAMS_User_Guide.pdf")


if __name__ == "__main__":
    main()
