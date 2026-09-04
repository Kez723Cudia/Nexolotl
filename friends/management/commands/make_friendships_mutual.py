from django.core.management.base import BaseCommand
from friends.models import Friendship


class Command(BaseCommand):

    help = "Creates missing reverse Friendship records."

    def handle(self, *args, **options):

        friendships = Friendship.objects.all()

        created_count = 0

        for friendship in friendships:

            reverse_exists = Friendship.objects.filter(
                user=friendship.friend,
                friend=friendship.user
            ).exists()

            if not reverse_exists:

                Friendship.objects.create(
                    user=friendship.friend,
                    friend=friendship.user
                )

                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed. Created {created_count} reverse friendships."
            )
        )