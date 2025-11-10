# Generated manually to clean up models that were moved to other apps
# This migration removes tables from core that have been moved to:
# - Achievement/UserAchievement -> achievements app
# - Company -> companies app
# - Review -> reviews app
# - UserProfile -> accounts app
# - OnboardingStatus -> accounts app
# - PendingReview -> reviews app
# - WorkHistory -> work_history app

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_achievement_userachievement'),
        # Ensure the new apps have their tables created first
        ('achievements', '0001_initial'),
        ('companies', '0001_initial'),
        ('reviews', '0001_initial'),
        ('accounts', '0001_initial'),
        ('work_history', '0001_initial'),
    ]

    operations = [
        # Remove models that were moved to other apps
        # Delete in order: first tables with foreign keys, then referenced tables
        # Delete UserAchievement first (has FK to Achievement and UserProfile)
        migrations.DeleteModel(
            name='UserAchievement',
        ),
        # Delete Achievement (referenced by UserAchievement)
        migrations.DeleteModel(
            name='Achievement',
        ),
        # Delete Review (has FK to Company and UserProfile)
        migrations.DeleteModel(
            name='Review',
        ),
        # Delete WorkHistory if it exists (has FK to UserProfile and Company)
        # Note: WorkHistory table exists in DB but model was moved to work_history app
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "DROP TABLE IF EXISTS core_workhistory;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
        # Delete PendingReview if it exists (has FK to UserProfile and Company)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "DROP TABLE IF EXISTS core_pendingreview;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
        # Delete OnboardingStatus if it exists (has FK to UserProfile)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "DROP TABLE IF EXISTS core_onboardingstatus;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
        # Delete Event if it exists (has FK to UserProfile)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "DROP TABLE IF EXISTS core_event;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[],
        ),
        # Delete UserProfile (referenced by many tables)
        migrations.DeleteModel(
            name='UserProfile',
        ),
        # Delete Company (referenced by Review, WorkHistory, etc.)
        migrations.DeleteModel(
            name='Company',
        ),
    ]

