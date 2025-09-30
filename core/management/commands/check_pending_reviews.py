# ===== COMANDO: VERIFICAR RESEÑAS PENDIENTES =====
# Comando para verificar reseñas pendientes de usuarios específicos
# Uso: python manage.py check_pending_reviews

from django.core.management.base import BaseCommand
from core.models import PendingReview, UserProfile


class Command(BaseCommand):
    help = 'Verifica reseñas pendientes de usuarios específicos'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('📋 VERIFICACIÓN DE RESEÑAS PENDIENTES')
        )
        
        # Usuarios objetivo
        target_users = ['user2', 'user3', 'user4', 'user5', 'user6', 'user7', 'user8', 'user9', 'user10']
        
        self.stdout.write('\n👥 Reseñas pendientes por usuario:')
        self.stdout.write('='*60)
        
        total_pending = 0
        
        for username in target_users:
            try:
                user_profile = UserProfile.objects.get(user__username=username)
                pending_reviews = PendingReview.objects.filter(
                    user_profile=user_profile, 
                    is_reviewed=False
                )
                
                count = pending_reviews.count()
                total_pending += count
                
                self.stdout.write(f'{username}: {count} reseñas pendientes')
                
                # Mostrar detalles de las reseñas pendientes
                if count > 0:
                    for review in pending_reviews:
                        self.stdout.write(f'  - {review.company.name} ({review.job_title})')
                
            except UserProfile.DoesNotExist:
                self.stdout.write(f'{username}: Usuario no encontrado')
        
        self.stdout.write('='*60)
        self.stdout.write(f'📊 Total reseñas pendientes: {total_pending}')
        
        # Estadísticas generales
        all_pending = PendingReview.objects.filter(is_reviewed=False).count()
        self.stdout.write(f'📈 Reseñas pendientes en todo el sistema: {all_pending}')
        
        self.stdout.write('\n🎯 Estado del sistema:')
        if total_pending > 0:
            self.stdout.write('  ✅ Los usuarios tienen reseñas pendientes que completar')
            self.stdout.write('  📝 Pueden acceder a "Mis Reseñas" para completarlas')
            self.stdout.write('  🔒 El acceso a empresas está restringido hasta completar las reseñas')
        else:
            self.stdout.write('  ⚠️ No hay reseñas pendientes para estos usuarios')
