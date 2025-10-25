# core/management/commands/verify_reviews.py
from django.core.management.base import BaseCommand
from reviews.models import Review
from core.services.review_verification import ReviewVerificationService

class Command(BaseCommand):
    help = 'Verifica todas las reseñas existentes con el sistema anti-odio y anti-contenido fuera de lugar'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar verificación de reseñas ya verificadas',
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='Verificar solo reseñas de una empresa específica',
        )
    
    def handle(self, *args, **options):
        verification_service = ReviewVerificationService()
        
        # Construir queryset
        queryset = Review.objects.all()
        
        if not options['force']:
            queryset = queryset.filter(is_verified=False)
        
        if options['company_id']:
            queryset = queryset.filter(company_id=options['company_id'])
        
        total_reviews = queryset.count()
        
        if total_reviews == 0:
            self.stdout.write(self.style.WARNING('No hay reseñas para verificar'))
            return
        
        self.stdout.write(f'Verificando {total_reviews} reseñas...')
        
        approved_count = 0
        rejected_count = 0
        error_count = 0
        
        for review in queryset:
            try:
                # Combinar todo el contenido de la reseña para verificar
                content_to_verify = f"{review.pros} {review.cons} {review.interview_questions or ''}"
                result = verification_service.verify_review(content_to_verify)
                
                review.is_verified = True
                review.verification_reason = result['reason']
                review.verification_confidence = result['confidence']
                review.verification_category = result['category']
                
                if result['is_appropriate']:
                    review.status = 'approved'
                    review.is_approved = True
                    approved_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Reseña {review.id}: APROBADA - {result["reason"]}')
                    )
                else:
                    review.status = 'rejected'
                    review.is_approved = False
                    rejected_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Reseña {review.id}: RECHAZADA - {result["reason"]} (confianza: {result["confidence"]:.2f})')
                    )
                
                review.save()
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error en reseña {review.id}: {str(e)}')
                )
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Verificación completada:'))
        self.stdout.write(f'  • Total procesadas: {total_reviews}')
        self.stdout.write(self.style.SUCCESS(f'  • Aprobadas: {approved_count}'))
        self.stdout.write(self.style.ERROR(f'  • Rechazadas: {rejected_count}'))
        self.stdout.write(self.style.WARNING(f'  • Errores: {error_count}'))
        
        if rejected_count > 0:
            self.stdout.write('\n' + self.style.WARNING('Reseñas rechazadas requieren revisión manual en el admin.'))
