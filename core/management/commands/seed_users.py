# ===== COMANDO DE GESTIÓN: SEMBRAR USUARIOS =====
# Crea/normaliza los usuarios estándar del proyecto y sus perfiles/roles.

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Crea o normaliza usuarios predefinidos y sus perfiles (staff, company, candidatos).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reasigna las contraseñas de los usuarios semilla a los valores por defecto',
        )

    def handle(self, *args, **options):
        reset_passwords = options['reset_passwords']

        # Definición de usuarios semilla
        staff_users = [
            {'username': 'staff', 'password': 'staff', 'is_staff': True, 'first_name': 'System', 'last_name': 'Staff'},
        ]

        company_users = [
            {'username': 'company', 'password': 'company', 'is_staff': False, 'first_name': 'Company', 'last_name': 'Rep'},
        ]

        candidate_users = [
            {'username': f'user{i}', 'password': f'user{i}', 'first_name': 'User', 'last_name': str(i)}
            for i in range(1, 11)
        ]

        created = 0
        updated = 0

        # Helper para asegurar perfil
        def ensure_profile(user: User, role: str):
            profile = getattr(user, 'profile', None)
            if profile is None:
                UserProfile.objects.create(user=user, role=role)
                return True
            changed = False
            if user.is_staff and profile.role != 'staff':
                profile.role = 'staff'
                changed = True
            elif not user.is_staff and role and profile.role != role:
                profile.role = role
                changed = True
            if changed:
                profile.save()
            return changed

        # Crear/actualizar staff
        for data in staff_users:
            user, was_created = User.objects.get_or_create(username=data['username'], defaults={
                'is_staff': data.get('is_staff', False),
                'is_superuser': data.get('is_staff', False),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
            })
            if was_created:
                user.set_password(data['password'])
                user.is_staff = True
                user.is_superuser = True
                user.save()
                created += 1
            else:
                if reset_passwords:
                    user.set_password(data['password'])
                if not user.is_staff:
                    user.is_staff = True
                if not user.is_superuser:
                    user.is_superuser = True
                user.save()
                updated += 1
            ensure_profile(user, 'staff')

        # Crear/actualizar company reps
        for data in company_users:
            user, was_created = User.objects.get_or_create(username=data['username'], defaults={
                'is_staff': data.get('is_staff', False),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
            })
            if was_created:
                user.set_password(data['password'])
                user.is_staff = data.get('is_staff', False)
                user.save()
                created += 1
            else:
                if reset_passwords:
                    user.set_password(data['password'])
                user.is_staff = data.get('is_staff', False)
                user.save()
                updated += 1
            ensure_profile(user, 'company_rep')

        # Crear/actualizar candidatos
        for data in candidate_users:
            user, was_created = User.objects.get_or_create(username=data['username'], defaults={
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
            })
            if was_created:
                user.set_password(data['password'])
                user.is_staff = False
                user.save()
                created += 1
            else:
                if reset_passwords:
                    user.set_password(data['password'])
                user.is_staff = False
                user.save()
                updated += 1
            ensure_profile(user, 'candidate')

        self.stdout.write(self.style.SUCCESS(
            f'Usuarios semilla procesados. Creados: {created}, Actualizados: {updated}.\n' \
            'Contraseñas reiniciadas: {}.'.format('sí' if reset_passwords else 'no')
        ))


