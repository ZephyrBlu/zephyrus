from django.core.management.base import BaseCommand
from apps.user_profile.models import BattlenetAccount


class Command(BaseCommand):
    help = 'Updates user Battlenet Account Region Profiles to a list format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--details',
            action='store_true',
            help='Show the details of each account being updated'
        )

    def handle(self, *args, **options):
        user_accounts = list(BattlenetAccount.objects.all())

        for account in user_accounts:
            for region, info in account.region_profiles.items():
                if type(info['profile_id']) is not list:
                    info['profile_id'] = [info['profile_id']]

                    if options['details']:
                        self.stdout.write(f'Updated Region {region}\n\n')
                elif options['details']:
                    self.stdout.write(f'Region {region} data is already in list format\n\n')

            account.save()
            if options['details']:
                self.stdout.write(f'Updated all regions associated with: {account.battletag}\n\n')

        num_accounts = len(user_accounts)
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {num_accounts} replays'))
