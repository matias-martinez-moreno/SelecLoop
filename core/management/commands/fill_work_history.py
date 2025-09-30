# ===== COMANDO: LLENAR HISTORIAL LABORAL =====
# Comando para llenar historial laboral de usuarios específicos
# Uso: python manage.py fill_work_history

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Company, UserProfile, WorkHistory


class Command(BaseCommand):
    help = 'Llena historial laboral de usuarios específicos con experiencias únicas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            nargs='+',
            default=['user2', 'user3', 'user4', 'user5', 'user6', 'user7', 'user8', 'user9', 'user10'],
            help='Lista de usuarios a procesar'
        )
        parser.add_argument(
            '--min-experiences',
            type=int,
            default=2,
            help='Número mínimo de experiencias por usuario (default: 2)'
        )
        parser.add_argument(
            '--max-experiences',
            type=int,
            default=4,
            help='Número máximo de experiencias por usuario (default: 4)'
        )

    def handle(self, *args, **options):
        usernames = options['users']
        min_experiences = options['min_experiences']
        max_experiences = options['max_experiences']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Iniciando llenado de historial laboral para usuarios: {", ".join(usernames)}')
        )
        
        # ===== OBTENER EMPRESAS =====
        companies = Company.objects.filter(is_active=True)
        total_companies = companies.count()
        
        self.stdout.write(f'📊 Empresas disponibles: {total_companies}')
        
        if total_companies == 0:
            self.stdout.write(self.style.ERROR('❌ No hay empresas activas en el sistema'))
            return
        
        # ===== TEMPLATES DE CARGOS ÚNICOS =====
        job_templates = {
            'tech': [
                'Desarrollador Frontend', 'Desarrollador Backend', 'Desarrollador Full Stack',
                'Ingeniero de Software', 'Arquitecto de Software', 'DevOps Engineer',
                'Data Scientist', 'Data Analyst', 'Machine Learning Engineer',
                'Product Manager', 'Scrum Master', 'Tech Lead', 'QA Engineer',
                'Mobile Developer', 'Cloud Engineer', 'Cybersecurity Analyst'
            ],
            'business': [
                'Analista de Negocios', 'Consultor de Procesos', 'Project Manager',
                'Business Analyst', 'Marketing Manager', 'Sales Manager',
                'HR Specialist', 'Financial Analyst', 'Operations Manager',
                'Customer Success Manager', 'Account Manager', 'Business Development',
                'Strategy Analyst', 'Process Improvement Specialist'
            ],
            'design': [
                'UX Designer', 'UI Designer', 'Product Designer', 'Graphic Designer',
                'Visual Designer', 'Interaction Designer', 'Design System Manager',
                'Brand Designer', 'Motion Graphics Designer', 'Web Designer'
            ],
            'finance': [
                'Financial Analyst', 'Investment Analyst', 'Risk Analyst',
                'Treasury Analyst', 'Audit Associate', 'Tax Specialist',
                'Financial Controller', 'Credit Analyst', 'Portfolio Manager'
            ],
            'marketing': [
                'Digital Marketing Specialist', 'Content Marketing Manager',
                'Social Media Manager', 'SEO Specialist', 'Growth Marketing Manager',
                'Brand Manager', 'Marketing Analyst', 'Campaign Manager',
                'Influencer Marketing Specialist', 'Email Marketing Manager'
            ]
        }
        
        # ===== PROCESAR USUARIOS =====
        total_experiences_created = 0
        processed_users = []
        
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                user_profile = user.profile
                
                self.stdout.write(f'\n👤 Procesando {username} ({user.first_name} {user.last_name})')
                
                # Determinar número de experiencias para este usuario
                num_experiences = random.randint(min_experiences, max_experiences)
                
                # Seleccionar empresas aleatorias sin repetir
                selected_companies = random.sample(list(companies), min(num_experiences, total_companies))
                
                # Seleccionar categoría de trabajo para este usuario
                work_category = random.choice(list(job_templates.keys()))
                available_jobs = job_templates[work_category]
                
                for i, company in enumerate(selected_companies):
                    # Seleccionar cargo único
                    job_title = random.choice(available_jobs)
                    
                    # Generar fechas realistas
                    # Fecha de inicio: entre 1 y 3 años atrás
                    start_days_ago = random.randint(365, 1095)  # 1-3 años
                    start_date = timezone.now().date() - timedelta(days=start_days_ago)
                    
                    # Determinar si es trabajo actual o pasado
                    is_current = random.choice([True, False]) if i == len(selected_companies) - 1 else False
                    
                    if is_current:
                        end_date = None
                    else:
                        # Fecha de fin: entre 3 meses y 2 años después del inicio
                        duration_days = random.randint(90, 730)  # 3 meses a 2 años
                        end_date = start_date + timedelta(days=duration_days)
                    
                    # Crear experiencia laboral
                    work_history = WorkHistory.objects.create(
                        user_profile=user_profile,
                        company=company,
                        job_title=job_title,
                        start_date=start_date,
                        end_date=end_date,
                        is_current_job=is_current,
                        has_review_pending=False  # Se establecerá automáticamente
                    )
                    
                    # Crear reseña pendiente automáticamente
                    work_history.create_pending_review()
                    
                    total_experiences_created += 1
                    
                    status = "Trabajo actual" if is_current else f"Hasta {end_date.strftime('%d/%m/%Y')}"
                    self.stdout.write(f'  ✅ {company.name} - {job_title} ({start_date.strftime("%d/%m/%Y")} - {status})')
                
                processed_users.append({
                    'username': username,
                    'name': f"{user.first_name} {user.last_name}",
                    'experiences': len(selected_companies),
                    'category': work_category
                })
                
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠️ Usuario {username} no encontrado'))
                continue
        
        # ===== ESTADÍSTICAS FINALES =====
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Proceso completado exitosamente!')
        )
        self.stdout.write(f'📊 Experiencias laborales creadas: {total_experiences_created}')
        self.stdout.write(f'👥 Usuarios procesados: {len(processed_users)}')
        
        # Mostrar resumen por usuario
        self.stdout.write('\n📈 Resumen por usuario:')
        for user_info in processed_users:
            self.stdout.write(f'  {user_info["username"]} ({user_info["name"]}): {user_info["experiences"]} experiencias - Categoría: {user_info["category"]}')
        
        # Verificar reseñas pendientes creadas
        from core.models import PendingReview
        pending_reviews = PendingReview.objects.filter(is_reviewed=False).count()
        self.stdout.write(f'\n📋 Reseñas pendientes totales: {pending_reviews}')
        
        self.stdout.write('\n🎯 Próximos pasos:')
        self.stdout.write('  - Los usuarios pueden ver sus reseñas pendientes en "Mis Reseñas"')
        self.stdout.write('  - Al completar las reseñas pendientes, se desbloqueará el acceso completo')
        self.stdout.write('  - Las reseñas pendientes aparecerán en el dashboard principal')
