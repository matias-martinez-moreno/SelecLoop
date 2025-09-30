# ===== COMANDO: LLENAR EMPRESAS CON RESEÑAS =====
# Comando para llenar todas las empresas con mínimo 3-4 reseñas únicas
# Uso: python manage.py fill_companies_reviews

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Company, Review, UserProfile


class Command(BaseCommand):
    help = 'Llena todas las empresas con mínimo 3-4 reseñas únicas usando usuarios aleatorios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-reviews',
            type=int,
            default=3,
            help='Número mínimo de reseñas por empresa (default: 3)'
        )
        parser.add_argument(
            '--max-reviews',
            type=int,
            default=4,
            help='Número máximo de reseñas por empresa (default: 4)'
        )

    def handle(self, *args, **options):
        min_reviews = options['min_reviews']
        max_reviews = options['max_reviews']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Iniciando llenado de empresas con {min_reviews}-{max_reviews} reseñas cada una')
        )
        
        # ===== NOMBRES DE USUARIOS ALEATORIOS =====
        first_names = [
            'Alejandro', 'María', 'Carlos', 'Ana', 'Luis', 'Carmen', 'José', 'Laura',
            'Miguel', 'Isabel', 'Antonio', 'Patricia', 'Francisco', 'Elena', 'Manuel',
            'Rosa', 'David', 'Cristina', 'Juan', 'Mónica', 'Pedro', 'Sandra', 'Rafael',
            'Beatriz', 'Fernando', 'Natalia', 'Sergio', 'Andrea', 'Diego', 'Paula',
            'Roberto', 'Silvia', 'Javier', 'Marta', 'Álvaro', 'Lucía', 'Rubén', 'Eva',
            'Daniel', 'Claudia', 'Adrián', 'Raquel', 'Víctor', 'Sara', 'Óscar', 'Nuria'
        ]
        
        last_names = [
            'García', 'Rodríguez', 'Martínez', 'Hernández', 'López', 'González', 'Pérez',
            'Sánchez', 'Ramírez', 'Cruz', 'Flores', 'Morales', 'Gutiérrez', 'Ruiz',
            'Díaz', 'Torres', 'Jiménez', 'Vargas', 'Reyes', 'Moreno', 'Álvarez', 'Mendoza',
            'Castillo', 'Romero', 'Herrera', 'Medina', 'Guerrero', 'Ramos', 'Vega',
            'Castro', 'Ortega', 'Delgado', 'Rivera', 'Contreras', 'Espinoza', 'Silva',
            'Molina', 'Valencia', 'Navarro', 'Aguilar', 'Sandoval', 'Campos', 'Peña'
        ]
        
        # ===== TEMPLATES DE RESEÑAS ÚNICAS =====
        review_templates = [
            {
                'job_titles': ['Desarrollador Frontend', 'Analista de Datos', 'Diseñador UX/UI', 'Product Manager'],
                'pros_templates': [
                    'Excelente ambiente de trabajo, equipo muy colaborativo y comunicación fluida.',
                    'Proceso muy organizado, feedback constante y oportunidades de crecimiento claras.',
                    'Empresa innovadora con tecnología de punta y proyectos desafiantes.',
                    'Cultura empresarial sólida, horarios flexibles y beneficios competitivos.',
                    'Equipo multidisciplinario, aprendizaje continuo y reconocimiento al esfuerzo.',
                    'Proceso transparente, entrevistas técnicas bien estructuradas y evaluación justa.',
                    'Empresa con visión clara, productos interesantes y mercado establecido.',
                    'Ambiente dinámico, proyectos diversos y posibilidad de impacto real.',
                    'Equipo técnico sólido, metodologías ágiles y herramientas modernas.',
                    'Cultura de innovación, experimentación y desarrollo profesional.'
                ],
                'cons_templates': [
                    'Proceso muy largo, múltiples entrevistas y tiempo de respuesta lento.',
                    'Falta de claridad en los requisitos del puesto y expectativas poco definidas.',
                    'Comunicación interna podría mejorar, información fragmentada.',
                    'Proceso de selección muy técnico, poco enfoque en habilidades blandas.',
                    'Tiempo de espera excesivo entre entrevistas, falta de feedback oportuno.',
                    'Estructura organizacional compleja, procesos burocráticos.',
                    'Falta de transparencia en el salario y beneficios durante el proceso.',
                    'Equipo de reclutamiento poco preparado, preguntas repetitivas.',
                    'Proceso muy competitivo, evaluación muy estricta.',
                    'Falta de información sobre la cultura de la empresa.'
                ],
                'interview_questions': [
                    '¿Cuál es tu experiencia con React y JavaScript moderno?',
                    'Describe un proyecto desafiante que hayas liderado.',
                    '¿Cómo manejas el trabajo en equipo bajo presión?',
                    '¿Qué metodologías ágiles conoces y has aplicado?',
                    'Explica tu proceso de resolución de problemas técnicos.',
                    '¿Cómo te mantienes actualizado con las nuevas tecnologías?',
                    'Describe una situación donde tuviste que aprender algo nuevo rápidamente.',
                    '¿Cuál es tu enfoque para escribir código limpio y mantenible?',
                    '¿Cómo manejas los conflictos en el equipo de desarrollo?',
                    '¿Qué te motiva más en tu carrera profesional?'
                ]
            }
        ]
        
        # ===== OBTENER EMPRESAS =====
        companies = Company.objects.filter(is_active=True)
        total_companies = companies.count()
        
        self.stdout.write(f'📊 Empresas encontradas: {total_companies}')
        
        if total_companies == 0:
            self.stdout.write(self.style.ERROR('❌ No hay empresas activas en el sistema'))
            return
        
        # ===== CREAR USUARIOS ALEATORIOS =====
        created_users = []
        for i in range(50):  # Crear 50 usuarios aleatorios
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(10, 99)}"
            
            # Verificar que el usuario no exista
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password='password123',
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Crear perfil de candidato
                UserProfile.objects.create(
                    user=user,
                    role='candidate',
                    display_name=f"{first_name} {last_name}"
                )
                
                created_users.append(user)
        
        self.stdout.write(f'👥 Usuarios creados: {len(created_users)}')
        
        # ===== LLENAR EMPRESAS CON RESEÑAS =====
        total_reviews_created = 0
        
        for company in companies:
            # Determinar número de reseñas para esta empresa
            num_reviews = random.randint(min_reviews, max_reviews)
            
            self.stdout.write(f'🏢 Procesando {company.name} - {num_reviews} reseñas')
            
            for i in range(num_reviews):
                # Seleccionar usuario aleatorio
                user = random.choice(created_users)
                user_profile = user.profile
                
                # Seleccionar template aleatorio
                template = random.choice(review_templates)
                
                # Generar datos únicos
                job_title = random.choice(template['job_titles'])
                pros = random.choice(template['pros_templates'])
                cons = random.choice(template['cons_templates'])
                interview_questions = random.choice(template['interview_questions'])
                
                # Calificaciones aleatorias pero realistas
                overall_rating = random.randint(3, 5)  # Mayoría positivas
                communication_rating = random.choice(['excellent', 'good', 'regular'])
                difficulty_rating = random.choice(['moderate', 'difficult', 'easy'])
                response_time_rating = random.choice(['same_day', 'next_day', 'few_days'])
                modality = random.choice(['presencial', 'remoto', 'híbrido'])
                
                # Fecha aleatoria en los últimos 6 meses
                days_ago = random.randint(1, 180)
                submission_date = timezone.now() - timedelta(days=days_ago)
                
                # Crear reseña
                review = Review.objects.create(
                    user_profile=user_profile,
                    company=company,
                    job_title=job_title,
                    modality=modality,
                    communication_rating=communication_rating,
                    difficulty_rating=difficulty_rating,
                    response_time_rating=response_time_rating,
                    overall_rating=overall_rating,
                    pros=pros,
                    cons=cons,
                    interview_questions=interview_questions,
                    status='approved',  # Aprobar automáticamente
                    is_approved=True,
                    submission_date=submission_date,
                    approval_date=submission_date + timedelta(hours=random.randint(1, 24))
                )
                
                total_reviews_created += 1
        
        # ===== ESTADÍSTICAS FINALES =====
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Proceso completado exitosamente!')
        )
        self.stdout.write(f'📊 Reseñas creadas: {total_reviews_created}')
        self.stdout.write(f'👥 Usuarios creados: {len(created_users)}')
        self.stdout.write(f'🏢 Empresas procesadas: {total_companies}')
        
        # Mostrar estadísticas por empresa
        self.stdout.write('\n📈 Reseñas por empresa:')
        for company in companies:
            review_count = company.reviews.count()
            self.stdout.write(f'  {company.name}: {review_count} reseñas')
