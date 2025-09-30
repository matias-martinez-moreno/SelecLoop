# ===== COMANDO: LISTAR USUARIOS ACTIVOS =====
# Comando para mostrar todos los usuarios activos del sistema
# Uso: python manage.py list_active_users

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count
from core.models import UserProfile, Review, WorkHistory


class Command(BaseCommand):
    help = 'Lista todos los usuarios activos del sistema con información detallada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            type=str,
            choices=['candidate', 'company_rep', 'staff'],
            help='Filtrar por rol específico'
        )
        parser.add_argument(
            '--with-reviews',
            action='store_true',
            help='Mostrar solo usuarios con reseñas'
        )

    def handle(self, *args, **options):
        role_filter = options.get('role')
        with_reviews_only = options.get('with_reviews')
        
        self.stdout.write(
            self.style.SUCCESS('👥 USUARIOS ACTIVOS EN EL SISTEMA')
        )
        
        # ===== CONSULTA BASE =====
        users_query = User.objects.select_related('profile').all()
        
        if role_filter:
            users_query = users_query.filter(profile__role=role_filter)
        
        if with_reviews_only:
            users_query = users_query.filter(profile__reviews__isnull=False).distinct()
        
        users = users_query.order_by('username')
        
        # ===== MOSTRAR USUARIOS =====
        total_users = users.count()
        self.stdout.write(f'\n📊 Total usuarios encontrados: {total_users}')
        
        if total_users == 0:
            self.stdout.write(self.style.WARNING('⚠️ No se encontraron usuarios'))
            return
        
        # ===== ENCABEZADOS =====
        self.stdout.write('\n' + '='*100)
        self.stdout.write(f'{"USUARIO":<20} {"NOMBRE":<25} {"ROL":<15} {"RESEÑAS":<8} {"HISTORIAL":<10} {"ÚLTIMO LOGIN":<15}')
        self.stdout.write('='*100)
        
        # ===== DATOS DE USUARIOS =====
        for user in users:
            profile = user.profile
            
            # Información básica
            username = user.username[:19]  # Truncar si es muy largo
            full_name = f"{user.first_name} {user.last_name}".strip()[:24]
            role_display = {
                'candidate': 'Candidato',
                'company_rep': 'Empresa',
                'staff': 'Staff'
            }.get(profile.role, profile.role)
            
            # Estadísticas
            reviews_count = Review.objects.filter(user_profile=profile).count()
            work_history_count = WorkHistory.objects.filter(user_profile=profile).count()
            
            # Último login
            last_login = user.last_login.strftime('%d/%m/%Y') if user.last_login else 'Nunca'
            
            # Formatear línea
            line = f"{username:<20} {full_name:<25} {role_display:<15} {reviews_count:<8} {work_history_count:<10} {last_login:<15}"
            
            # Resaltar usuarios importantes
            if user.is_superuser:
                line = self.style.WARNING(line + " [SUPERUSER]")
            elif profile.role == 'staff':
                line = self.style.SUCCESS(line + " [STAFF]")
            elif profile.role == 'company_rep':
                line = self.style.HTTP_INFO(line + " [EMPRESA]")
            
            self.stdout.write(line)
        
        # ===== ESTADÍSTICAS RESUMEN =====
        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS('📈 ESTADÍSTICAS RESUMEN'))
        
        # Conteos por rol
        role_counts = UserProfile.objects.values('role').annotate(count=Count('role')).order_by('-count')
        for item in role_counts:
            role = item['role']
            count = item['count']
            role_display = {
                'candidate': 'Candidatos',
                'company_rep': 'Representantes de Empresa',
                'staff': 'Staff del Sistema'
            }.get(role, role)
            self.stdout.write(f'  {role_display}: {count}')
        
        # Usuarios con actividad
        users_with_reviews = UserProfile.objects.filter(reviews__isnull=False).distinct().count()
        users_with_work_history = UserProfile.objects.filter(work_history__isnull=False).distinct().count()
        users_with_login = User.objects.filter(last_login__isnull=False).count()
        
        self.stdout.write(f'\n📊 Actividad:')
        self.stdout.write(f'  Con reseñas: {users_with_reviews}')
        self.stdout.write(f'  Con historial laboral: {users_with_work_history}')
        self.stdout.write(f'  Con login reciente: {users_with_login}')
        
        # Usuarios creados recientemente
        from django.utils import timezone
        from datetime import timedelta
        
        recent_users = User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count()
        self.stdout.write(f'  Creados esta semana: {recent_users}')
        
        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS('✅ Consulta completada'))
