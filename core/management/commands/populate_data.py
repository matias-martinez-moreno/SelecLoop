"""
Comando de Django para poblar la base de datos con empresas y reseñas de ejemplo.
Crea empresas variadas y reseñas realistas para testing y demostración.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Company, UserProfile, Review, WorkHistory, PendingReview
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Pobla la base de datos con empresas y reseñas de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--companies',
            type=int,
            default=15,
            help='Número de empresas a crear (default: 15)'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=25,
            help='Número de reseñas a crear (default: 25)'
        )

    def handle(self, *args, **options):
        companies_count = options['companies']
        reviews_count = options['reviews']
        
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando población de datos: {companies_count} empresas, {reviews_count} reseñas')
        )
        
        # Crear empresas
        companies = self.create_companies(companies_count)
        
        # Crear usuarios si no existen
        users = self.create_users()
        
        # Crear reseñas
        self.create_reviews(companies, users, reviews_count)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Población de datos completada exitosamente!')
        )

    def create_companies(self, count):
        """Crea empresas variadas con información realista"""
        
        companies_data = [
            # Tecnología
            {
                'name': 'Google Colombia',
                'description': 'Líder mundial en tecnología y servicios de internet. Ofrece oportunidades en desarrollo de software, análisis de datos y marketing digital.',
                'sector': 'Tecnología',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://careers.google.com'
            },
            {
                'name': 'Microsoft Colombia',
                'description': 'Empresa tecnológica multinacional especializada en software, servicios en la nube y soluciones empresariales.',
                'sector': 'Tecnología',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://careers.microsoft.com'
            },
            {
                'name': 'Amazon Colombia',
                'description': 'Compañía de comercio electrónico y servicios en la nube. Oportunidades en logística, desarrollo y operaciones.',
                'sector': 'Tecnología',
                'location': 'Medellín',
                'region': 'Antioquia',
                'country': 'Colombia',
                'website': 'https://amazon.jobs'
            },
            {
                'name': 'Globant',
                'description': 'Compañía de tecnología que diseña y desarrolla software para empresas líderes a nivel mundial.',
                'sector': 'Tecnología',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.globant.com'
            },
            {
                'name': 'Rappi',
                'description': 'Plataforma de delivery y servicios digitales que conecta usuarios con restaurantes, farmacias y tiendas.',
                'sector': 'Tecnología',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.rappi.com'
            },
            
            # Banca y Finanzas
            {
                'name': 'Bancolombia',
                'description': 'Banco líder en Colombia con amplia red de sucursales y servicios financieros integrales.',
                'sector': 'Banca y Finanzas',
                'location': 'Medellín',
                'region': 'Antioquia',
                'country': 'Colombia',
                'website': 'https://www.bancolombia.com'
            },
            {
                'name': 'BBVA Colombia',
                'description': 'Banco internacional con presencia en Colombia, ofreciendo servicios bancarios y financieros.',
                'sector': 'Banca y Finanzas',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.bbva.com.co'
            },
            {
                'name': 'Davivienda',
                'description': 'Institución financiera colombiana con enfoque en banca personal y empresarial.',
                'sector': 'Banca y Finanzas',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.davivienda.com'
            },
            
            # Retail y Comercio
            {
                'name': 'Éxito',
                'description': 'Cadena de supermercados y tiendas por departamentos líder en Colombia.',
                'sector': 'Retail y Comercio',
                'location': 'Medellín',
                'region': 'Antioquia',
                'country': 'Colombia',
                'website': 'https://www.exito.com'
            },
            {
                'name': 'Falabella',
                'description': 'Retailer multinacional con tiendas por departamentos, supermercados y servicios financieros.',
                'sector': 'Retail y Comercio',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.falabella.com.co'
            },
            {
                'name': 'Almacenes Éxito',
                'description': 'Cadena de almacenes de cadena con presencia nacional en Colombia.',
                'sector': 'Retail y Comercio',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.exito.com'
            },
            
            # Salud
            {
                'name': 'Sanitas',
                'description': 'Empresa de salud con clínicas, hospitales y servicios médicos especializados.',
                'sector': 'Salud',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.sanitas.com.co'
            },
            {
                'name': 'Colsanitas',
                'description': 'EPS y prestadora de servicios de salud con amplia cobertura nacional.',
                'sector': 'Salud',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.colsanitas.com'
            },
            
            # Telecomunicaciones
            {
                'name': 'Claro Colombia',
                'description': 'Operador de telecomunicaciones con servicios de telefonía móvil, internet y TV.',
                'sector': 'Telecomunicaciones',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.claro.com.co'
            },
            {
                'name': 'Movistar Colombia',
                'description': 'Operador de telecomunicaciones con servicios móviles, internet y entretenimiento.',
                'sector': 'Telecomunicaciones',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.movistar.com.co'
            },
            
            # Consultoría
            {
                'name': 'Deloitte Colombia',
                'description': 'Firma de consultoría profesional con servicios de auditoría, consultoría y asesoría.',
                'sector': 'Consultoría',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www2.deloitte.com/co'
            },
            {
                'name': 'PwC Colombia',
                'description': 'Firma de servicios profesionales con enfoque en auditoría, consultoría y asesoría fiscal.',
                'sector': 'Consultoría',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.pwc.com.co'
            },
            {
                'name': 'EY Colombia',
                'description': 'Firma de servicios profesionales con servicios de auditoría, consultoría y asesoría.',
                'sector': 'Consultoría',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.ey.com/co'
            },
            
            # Manufactura
            {
                'name': 'Bavaria',
                'description': 'Compañía de bebidas líder en Colombia, productora de cervezas y bebidas no alcohólicas.',
                'sector': 'Manufactura',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.bavaria.com.co'
            },
            {
                'name': 'Alpina',
                'description': 'Empresa de alimentos y bebidas con productos lácteos y derivados.',
                'sector': 'Manufactura',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.alpina.com'
            },
            
            # Educación
            {
                'name': 'Universidad de los Andes',
                'description': 'Universidad privada de prestigio con programas de pregrado y posgrado.',
                'sector': 'Educación',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://uniandes.edu.co'
            },
            {
                'name': 'Universidad Nacional',
                'description': 'Universidad pública líder en Colombia con amplia oferta académica.',
                'sector': 'Educación',
                'location': 'Bogotá',
                'region': 'Cundinamarca',
                'country': 'Colombia',
                'website': 'https://www.unal.edu.co'
            }
        ]
        
        companies = []
        for i, data in enumerate(companies_data[:count]):
            company, created = Company.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            companies.append(company)
            if created:
                self.stdout.write(f'✅ Empresa creada: {company.name}')
            else:
                self.stdout.write(f'⚠️ Empresa ya existe: {company.name}')
        
        return companies

    def create_users(self):
        """Crea usuarios de ejemplo si no existen"""
        
        users_data = [
            {'username': 'candidato1', 'email': 'candidato1@example.com', 'first_name': 'Ana', 'last_name': 'García'},
            {'username': 'candidato2', 'email': 'candidato2@example.com', 'first_name': 'Carlos', 'last_name': 'Rodríguez'},
            {'username': 'candidato3', 'email': 'candidato3@example.com', 'first_name': 'María', 'last_name': 'López'},
            {'username': 'candidato4', 'email': 'candidato4@example.com', 'first_name': 'Juan', 'last_name': 'Martínez'},
            {'username': 'candidato5', 'email': 'candidato5@example.com', 'first_name': 'Laura', 'last_name': 'Hernández'},
            {'username': 'candidato6', 'email': 'candidato6@example.com', 'first_name': 'Diego', 'last_name': 'González'},
            {'username': 'candidato7', 'email': 'candidato7@example.com', 'first_name': 'Sofia', 'last_name': 'Pérez'},
            {'username': 'candidato8', 'email': 'candidato8@example.com', 'first_name': 'Andrés', 'last_name': 'Sánchez'},
            {'username': 'candidato9', 'email': 'candidato9@example.com', 'first_name': 'Valentina', 'last_name': 'Ramírez'},
            {'username': 'candidato10', 'email': 'candidato10@example.com', 'first_name': 'Sebastián', 'last_name': 'Cruz'},
        ]
        
        users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                
                # Crear perfil
                UserProfile.objects.create(
                    user=user,
                    role='candidate',
                    display_name=f"{data['first_name']} {data['last_name']}"
                )
                self.stdout.write(f'✅ Usuario creado: {user.username}')
            else:
                self.stdout.write(f'⚠️ Usuario ya existe: {user.username}')
            
            users.append(user)
        
        return users

    def create_reviews(self, companies, users, count):
        """Crea reseñas variadas y realistas"""
        
        job_titles = [
            'Desarrollador Frontend', 'Desarrollador Backend', 'Desarrollador Full Stack',
            'Analista de Datos', 'Científico de Datos', 'Ingeniero de Software',
            'Product Manager', 'Project Manager', 'Scrum Master',
            'Diseñador UX/UI', 'Diseñador Gráfico', 'Marketing Digital',
            'Analista Financiero', 'Contador', 'Auditor',
            'Vendedor', 'Ejecutivo de Cuentas', 'Gerente de Ventas',
            'Recursos Humanos', 'Especialista en Talento', 'Coordinador de RRHH',
            'Ingeniero Industrial', 'Ingeniero de Sistemas', 'Arquitecto de Software',
            'Consultor', 'Analista de Negocios', 'Especialista en Procesos'
        ]
        
        modalities = ['presencial', 'remoto', 'híbrido']
        communication_ratings = ['excellent', 'good', 'regular', 'poor']
        difficulty_ratings = ['very_easy', 'easy', 'moderate', 'difficult', 'very_difficult']
        response_time_ratings = ['immediate', 'same_day', 'next_day', 'few_days', 'slow']
        
        # Templates de reseñas variadas
        pros_templates = [
            "El proceso fue muy organizado y transparente. Los entrevistadores fueron amables y profesionales.",
            "Excelente comunicación durante todo el proceso. Me mantuvieron informado en cada etapa.",
            "La empresa mostró mucho interés en mi perfil y experiencia. Se notaba que habían revisado mi CV.",
            "El ambiente laboral se ve muy positivo. Los empleados parecían contentos y motivados.",
            "Oportunidades de crecimiento claras y bien definidas. La empresa invierte en el desarrollo profesional.",
            "Tecnología moderna y procesos bien estructurados. Se nota que están a la vanguardia.",
            "Equipo muy colaborativo y dispuesto a ayudar. La cultura de trabajo es excelente.",
            "Beneficios competitivos y políticas laborales flexibles. Se preocupan por el bienestar del empleado.",
            "Proyectos interesantes y desafiantes. La empresa trabaja con clientes importantes.",
            "Liderazgo accesible y con visión clara. Los managers están muy involucrados con el equipo.",
            "Proceso de selección justo y meritocrático. Se evalúa realmente las competencias.",
            "Empresa con valores sólidos y compromiso social. Se siente orgullo de trabajar ahí.",
            "Oportunidades de aprendizaje continuo. La empresa fomenta la capacitación.",
            "Work-life balance respetado. No hay presión excesiva por horas extra.",
            "Salario competitivo y estructura de compensación clara. Transparencia en los beneficios."
        ]
        
        cons_templates = [
            "El proceso fue un poco largo. Tardaron más de lo esperado en dar respuestas.",
            "Algunas preguntas de la entrevista fueron muy técnicas y específicas.",
            "No hubo mucha información sobre el equipo con el que trabajaría.",
            "El proceso de selección fue un poco impersonal. No se sintió muy personalizado.",
            "Tardaron en programar las entrevistas. La coordinación podría mejorar.",
            "Faltó información clara sobre las responsabilidades específicas del cargo.",
            "El proceso fue un poco estresante. Muchas etapas y evaluaciones.",
            "No dieron feedback detallado después de las entrevistas.",
            "El horario de las entrevistas no fue muy flexible.",
            "Algunos aspectos del proceso podrían ser más transparentes.",
            "La comunicación entre etapas podría ser más fluida.",
            "Faltó información sobre la cultura organizacional específica.",
            "El proceso fue un poco burocrático en algunas etapas.",
            "No hubo oportunidad de conocer al equipo antes de la decisión final.",
            "Algunas expectativas no quedaron completamente claras desde el inicio."
        ]
        
        interview_questions_templates = [
            "¿Cuál es tu experiencia con tecnologías específicas? ¿Cómo resolverías este problema técnico?",
            "Cuéntame sobre un proyecto desafiante en el que hayas trabajado. ¿Cómo manejaste los obstáculos?",
            "¿Por qué quieres trabajar en esta empresa? ¿Qué sabes sobre nuestra cultura?",
            "Describe una situación donde tuviste que trabajar en equipo bajo presión.",
            "¿Cuáles son tus fortalezas y áreas de mejora? ¿Cómo te mantienes actualizado?",
            "¿Cómo priorizas tus tareas cuando tienes múltiples proyectos?",
            "Cuéntame sobre un error que hayas cometido y cómo lo solucionaste.",
            "¿Qué te motiva en tu trabajo? ¿Cuáles son tus metas profesionales?",
            "¿Cómo manejas el feedback negativo? ¿Cómo aprendes de tus errores?",
            "Describe tu proceso para resolver problemas complejos.",
            "¿Cómo te adaptas a los cambios en el entorno laboral?",
            "¿Qué harías si no estuvieras de acuerdo con una decisión del equipo?",
            "Cuéntame sobre una vez que tuviste que aprender algo nuevo rápidamente.",
            "¿Cómo mantienes la calidad del trabajo cuando hay presión de tiempo?",
            "¿Qué preguntas tienes sobre el rol y la empresa?"
        ]
        
        for i in range(count):
            # Seleccionar datos aleatorios
            company = random.choice(companies)
            user = random.choice(users)
            job_title = random.choice(job_titles)
            modality = random.choice(modalities)
            communication = random.choice(communication_ratings)
            difficulty = random.choice(difficulty_ratings)
            response_time = random.choice(response_time_ratings)
            overall_rating = random.randint(3, 5)  # Ratings positivos en general
            
            # Seleccionar pros y cons
            pros = random.choice(pros_templates)
            cons = random.choice(cons_templates)
            interview_questions = random.choice(interview_questions_templates)
            
            # Crear reseña
            review = Review.objects.create(
                user_profile=user.profile,
                company=company,
                job_title=job_title,
                modality=modality,
                communication_rating=communication,
                difficulty_rating=difficulty,
                response_time_rating=response_time,
                overall_rating=overall_rating,
                pros=pros,
                cons=cons,
                interview_questions=interview_questions,
                status='approved',
                is_approved=True,
                submission_date=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            
            self.stdout.write(f'✅ Reseña creada: {user.username} - {company.name} - {job_title}')
        
        self.stdout.write(f'✅ Se crearon {count} reseñas exitosamente!')
