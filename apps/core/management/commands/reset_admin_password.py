from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from getpass import getpass
import secrets
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset admin password and print it (or optional QR code)'

    def add_arguments(self, parser):
        parser.add_argument('--qr', action='store_true', help='Print QR code (requires qrcode)')
        parser.add_argument(
            '--prompt-password', action='store_true',
            help='Enter and confirm a chosen temporary password using hidden terminal prompts.',
        )

    def handle(self, *args, **options):
        user = User.objects.filter(username='admin').first()
        if not user:
            self.stderr.write('Admin user not found')
            return
        if options['prompt_password']:
            try:
                new_pass = getpass('Temporary password: ')
                confirmation = getpass('Confirm temporary password: ')
            except (EOFError, KeyboardInterrupt):
                raise CommandError('Password entry canceled; password unchanged.') from None
            if not new_pass:
                raise CommandError('Password cannot be empty; password unchanged.')
            if new_pass != confirmation:
                raise CommandError('Passwords do not match; password unchanged.')
            try:
                validate_password(new_pass, user=user)
            except ValidationError as exc:
                raise CommandError(' '.join(exc.messages)) from None
        else:
            new_pass = secrets.token_urlsafe(12)
        user.set_password(new_pass)
        user.must_change_password = True
        user.save(update_fields=['password', 'must_change_password'])

        sys.stderr.write('Username: admin\n')
        if options['prompt_password']:
            sys.stderr.write('Chosen temporary password saved.\n')
        else:
            sys.stderr.write(f'New Password: {new_pass}\n')
        sys.stderr.write(
            '(This is a one-time credential. You will be required to '
            'change it on next login.)\n'
        )

        if options['qr']:
            try:
                import qrcode
                qr = qrcode.QRCode(box_size=1, border=2)
                qr.add_data(new_pass)
                qr.make(fit=True)
                qr.print_ascii(invert=True)
            except ImportError:
                self.stderr.write('qrcode not installed, skipping QR')
