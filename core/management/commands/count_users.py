# ===== COMANDO: CONTAR USUARIOS =====
# Comando personalizado para contar usuarios en el sistema
# Uso: python manage.py count_users

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count
from core.models import UserProfile, Company, Review


class Command(BaseCommand):
    help = 'Cuenta usuarios y muestra estadísticas del sistema'

    def handle(self, *args, **options):
        # ===== CONTEO DE USUARIOS =====
        total_users = User.objects.count()
        total_profiles = UserProfile.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(f'📊 ESTADÍSTICAS DE USUARIOS')
        )
        self.stdout.write(f'Total usuarios: {total_users}')
        self.stdout.write(f'Perfiles de usuario: {total_profiles}')
        
        # ===== DESGLOSE POR ROL =====
        self.stdout.write('\n👥 Desglose por rol:')
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
        
        # ===== ESTADÍSTICAS ADICIONALES =====
        self.stdout.write('\n📈 Estadísticas adicionales:')
        total_companies = Company.objects.count()
        total_reviews = Review.objects.count()
        active_companies = Company.objects.filter(is_active=True).count()
        
        self.stdout.write(f'Total empresas: {total_companies}')
        self.stdout.write(f'Empresas activas: {active_companies}')
        self.stdout.write(f'Total reseñas: {total_reviews}')
        
        # ===== USUARIOS CON RESEÑAS =====
        users_with_reviews = UserProfile.objects.filter(reviews__isnull=False).distinct().count()
        self.stdout.write(f'Usuarios con reseñas: {users_with_reviews}')
        
        # ===== USUARIOS CON HISTORIAL LABORAL =====
        users_with_work_history = UserProfile.objects.filter(work_history__isnull=False).distinct().count()
        self.stdout.write(f'Usuarios con historial laboral: {users_with_work_history}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Consulta completada')
        )
