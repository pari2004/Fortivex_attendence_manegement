"""
Creates the initial FAMS superadmin account (user + employee + Super Admin
group) with a one-time, randomly generated password. The password is never
written to the database, a log file, or the repository — it is only ever
printed once to stdout when this command runs.
"""

import secrets
import string

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from employee.models import Employee
from horilla_auth.models import HorillaUser

SUPER_ADMIN_GROUP = "Super Admin"


def generate_strong_password(length=24):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^&*()-_=+" for c in password)
        ):
            return password


class Command(BaseCommand):
    help = "Creates the initial FAMS superadmin user, employee record, and Super Admin group."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="superadmin")
        parser.add_argument("--email", default="admin@empowersacademy.com")
        parser.add_argument("--first-name", default="Super")
        parser.add_argument("--last-name", default="Administrator")
        parser.add_argument(
            "--phone",
            default="+10000000000",
            help="Placeholder phone number; update it after first login.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]

        if HorillaUser.objects.filter(username=username).exists():
            raise CommandError(f'A user named "{username}" already exists. Aborting.')
        if Employee.objects.filter(email=email).exists():
            raise CommandError(f'An employee with email "{email}" already exists. Aborting.')

        password = generate_strong_password()

        user = HorillaUser.objects.create_superuser(
            username=username, email=email, password=password
        )
        # Forces the existing NewEmployeeMiddleware to redirect this account
        # to /change-password/ on first login (base/middleware.py).
        user.is_new_employee = True
        user.is_active = True
        user.save()

        employee = Employee()
        employee.employee_user_id = user
        employee.employee_first_name = options["first_name"]
        employee.employee_last_name = options["last_name"]
        employee.email = email
        employee.phone = options["phone"]
        employee.save()

        group, _created = Group.objects.get_or_create(name=SUPER_ADMIN_GROUP)
        group.permissions.set(Permission.objects.all())
        user.groups.add(group)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("FAMS superadmin account created."))
        self.stdout.write(f"  Username : {username}")
        self.stdout.write(f"  Email    : {email}")
        self.stdout.write(f"  Group    : {SUPER_ADMIN_GROUP} (all permissions) + is_superuser")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "  Password (shown ONCE, not stored anywhere - copy it now):"
            )
        )
        self.stdout.write(f"  {password}")
        self.stdout.write("")
        self.stdout.write(
            "  This account is flagged is_new_employee=True, so the app will force a "
            "password change on first login before anything else is accessible."
        )
        self.stdout.write(
            self.style.WARNING(
                "  Note: there is no existing UI gate that forces a 'recovery email' "
                "update on first login (no such field exists in the codebase yet). "
                "I did not bolt one onto the shared change-password form to avoid a "
                "half-built flow - flag if you want that built as a real feature."
            )
        )
        self.stdout.write(
            "  Audit logging: Employee changes (including this account's) are tracked "
            "by default via horilla_audit's AuditModelConfig - no extra setup needed."
        )
        self.stdout.write(
            f"  Placeholder phone number ({options['phone']}) was set - update it in "
            "the employee profile after first login."
        )
