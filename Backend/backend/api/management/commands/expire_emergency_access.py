"""
Management command to expire emergency access requests that have passed their expiration time.
Run this command periodically (e.g., via cron job) to automatically clean up expired emergency access.
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from api.models import EmergencyAccess, GlobalsHoldsdesignation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Expire emergency access requests that have passed their expiration time'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Get current time
        now = timezone.now()

        # Find active emergency access requests that have expired
        expired_requests = EmergencyAccess.objects.filter(
            status='ACTIVE',
            expires_at__lte=now
        ).select_related('requester', 'requested_role')

        if not expired_requests.exists():
            self.stdout.write(
                self.style.SUCCESS('No expired emergency access requests found.')
            )
            return

        expired_count = 0

        for request in expired_requests:
            try:
                with transaction.atomic():
                    if dry_run:
                        self.stdout.write(
                            f'Would expire: {request} (expires at: {request.expires_at})'
                        )
                    else:
                        # Mark as expired
                        request.expire()

                        # Remove the temporary role assignment
                        GlobalsHoldsdesignation.objects.filter(
                            user=request.requester,
                            designation=request.requested_role
                        ).delete()

                        logger.info(f'Expired emergency access: {request}')
                        self.stdout.write(
                            f'Expired: {request}'
                        )

                    expired_count += 1

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'Failed to expire request {request.id}: {e}')
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Dry run completed. Would expire {expired_count} requests.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully expired {expired_count} emergency access requests.')
            )