"""
Comando de Django para agregar más reseñas variadas a empresas que no tienen reseñas.
Crea reseñas únicas y realistas para empresas específicas.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Company, UserProfile, Review
from django.utils import timezone
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Agrega más reseñas variadas a empresas que no tienen reseñas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reviews',
            type=int,
            default=20,
            help='Número de reseñas a crear (default: 20)'
        )

    def handle(self, *args, **options):
        reviews_count = options['reviews']
        
        self.stdout.write(
            self.style.SUCCESS(f'Agregando {reviews_count} reseñas variadas a empresas sin reseñas')
        )
        
        # Obtener empresas sin reseñas
        companies_without_reviews = Company.objects.filter(
            is_active=True,
            reviews__isnull=True
        ).distinct()
        
        if not companies_without_reviews.exists():
            self.stdout.write(
                self.style.WARNING('Todas las empresas ya tienen reseñas. Creando reseñas adicionales...')
            )
            companies_without_reviews = Company.objects.filter(is_active=True)
        
        # Obtener usuarios candidatos
        users = UserProfile.objects.filter(role='candidate')
        if not users.exists():
            self.stdout.write(
                self.style.ERROR('No hay usuarios candidatos. Ejecuta primero populate_data.')
            )
            return
        
        # Crear reseñas variadas
        self.create_varied_reviews(companies_without_reviews, users, reviews_count)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Reseñas adicionales creadas exitosamente!')
        )

    def create_varied_reviews(self, companies, users, count):
        """Crea reseñas muy variadas y únicas"""
        
        # Templates de reseñas completamente diferentes
        review_templates = [
            {
                'job_title': 'Desarrollador Frontend',
                'modality': 'remoto',
                'communication_rating': 'excellent',
                'difficulty_rating': 'moderate',
                'response_time_rating': 'same_day',
                'overall_rating': 4,
                'pros': 'Excelente equipo de trabajo, muy colaborativo y dispuesto a ayudar. La tecnología que usan es moderna y el ambiente laboral es muy positivo.',
                'cons': 'El proceso de selección fue un poco largo, tardaron casi 3 semanas en dar una respuesta final. Algunas preguntas técnicas fueron muy específicas.',
                'interview_questions': '¿Cómo optimizarías el rendimiento de una aplicación React? ¿Cuál es tu experiencia con TypeScript? ¿Cómo manejas el estado en aplicaciones grandes?'
            },
            {
                'job_title': 'Analista de Datos',
                'modality': 'híbrido',
                'communication_rating': 'good',
                'difficulty_rating': 'difficult',
                'response_time_rating': 'next_day',
                'overall_rating': 3,
                'pros': 'Proyectos muy interesantes con datos reales de clientes importantes. La empresa invierte en herramientas de última generación.',
                'cons': 'El proceso fue muy técnico y exigente. Tuvieron 4 rondas de entrevistas y un caso práctico que tomó 6 horas completar.',
                'interview_questions': '¿Cómo crearías un modelo predictivo para detectar fraudes? ¿Qué herramientas usarías para visualizar datos? ¿Cómo manejarías datos faltantes?'
            },
            {
                'job_title': 'Product Manager',
                'modality': 'presencial',
                'communication_rating': 'excellent',
                'difficulty_rating': 'moderate',
                'response_time_rating': 'immediate',
                'overall_rating': 5,
                'pros': 'Liderazgo muy accesible y con visión clara. La empresa tiene una cultura de innovación y permite mucha autonomía en el trabajo.',
                'cons': 'La carga de trabajo puede ser intensa en algunos períodos, especialmente durante lanzamientos de productos.',
                'interview_questions': '¿Cómo priorizarías features en un roadmap? ¿Cómo medirías el éxito de un producto? ¿Cómo manejarías conflictos entre stakeholders?'
            },
            {
                'job_title': 'Diseñador UX/UI',
                'modality': 'remoto',
                'communication_rating': 'good',
                'difficulty_rating': 'easy',
                'response_time_rating': 'same_day',
                'overall_rating': 4,
                'pros': 'Proyectos creativos y desafiantes. El equipo de diseño es muy talentoso y hay muchas oportunidades de aprendizaje.',
                'cons': 'Algunas veces los feedbacks no son muy específicos y hay que adivinar qué es lo que realmente quieren.',
                'interview_questions': '¿Cuál es tu proceso de diseño? ¿Cómo investigas a los usuarios? ¿Qué herramientas de prototipado prefieres?'
            },
            {
                'job_title': 'Ingeniero de Software',
                'modality': 'híbrido',
                'communication_rating': 'regular',
                'difficulty_rating': 'very_difficult',
                'response_time_rating': 'few_days',
                'overall_rating': 2,
                'pros': 'La tecnología que usan es interesante y hay oportunidades de trabajar con sistemas a gran escala.',
                'cons': 'El proceso fue extremadamente difícil con algoritmos complejos. La comunicación fue lenta y no muy clara sobre las expectativas.',
                'interview_questions': '¿Cómo implementarías un sistema de caché distribuido? ¿Qué es la complejidad Big O? ¿Cómo optimizarías una consulta SQL lenta?'
            },
            {
                'job_title': 'Marketing Digital',
                'modality': 'presencial',
                'communication_rating': 'excellent',
                'difficulty_rating': 'easy',
                'response_time_rating': 'immediate',
                'overall_rating': 4,
                'pros': 'Equipo muy dinámico y creativo. La empresa tiene buenos recursos para campañas y herramientas de marketing.',
                'cons': 'Algunas métricas de éxito no están muy bien definidas y hay que proponerlas uno mismo.',
                'interview_questions': '¿Cómo crearías una campaña para aumentar el engagement? ¿Qué métricas usarías para medir el ROI? ¿Cómo optimizarías un funnel de conversión?'
            },
            {
                'job_title': 'Consultor',
                'modality': 'híbrido',
                'communication_rating': 'good',
                'difficulty_rating': 'moderate',
                'response_time_rating': 'next_day',
                'overall_rating': 4,
                'pros': 'Clientes muy interesantes y proyectos variados. La empresa tiene buena reputación en el mercado.',
                'cons': 'Los viajes pueden ser frecuentes y la carga de trabajo es variable dependiendo del proyecto.',
                'interview_questions': '¿Cómo abordarías un problema de optimización de procesos? ¿Qué metodologías de consultoría conoces? ¿Cómo manejarías un cliente difícil?'
            },
            {
                'job_title': 'Recursos Humanos',
                'modality': 'presencial',
                'communication_rating': 'excellent',
                'difficulty_rating': 'easy',
                'response_time_rating': 'same_day',
                'overall_rating': 5,
                'pros': 'Ambiente laboral excelente, equipo muy humano y preocupado por el bienestar de los empleados. Políticas muy progresistas.',
                'cons': 'Algunos procesos internos podrían ser más ágiles, pero en general todo funciona bien.',
                'interview_questions': '¿Cómo manejarías un conflicto entre empleados? ¿Qué estrategias usarías para retener talento? ¿Cómo implementarías un programa de bienestar?'
            },
            {
                'job_title': 'Analista Financiero',
                'modality': 'remoto',
                'communication_rating': 'good',
                'difficulty_rating': 'difficult',
                'response_time_rating': 'next_day',
                'overall_rating': 3,
                'pros': 'Datos financieros muy interesantes y la oportunidad de trabajar con modelos complejos. El equipo es muy analítico.',
                'cons': 'El proceso fue muy técnico con muchas preguntas sobre finanzas corporativas y modelos de valoración.',
                'interview_questions': '¿Cómo valorarías una empresa? ¿Qué es el WACC? ¿Cómo construirías un modelo DCF? ¿Cómo analizarías el riesgo crediticio?'
            },
            {
                'job_title': 'Scrum Master',
                'modality': 'híbrido',
                'communication_rating': 'excellent',
                'difficulty_rating': 'moderate',
                'response_time_rating': 'immediate',
                'overall_rating': 4,
                'pros': 'Equipos muy colaborativos y abiertos a metodologías ágiles. La empresa realmente cree en los valores ágiles.',
                'cons': 'Algunos equipos son nuevos en agile y requieren mucha paciencia y educación.',
                'interview_questions': '¿Cómo manejarías un equipo que no sigue las ceremonias ágiles? ¿Qué harías si un sprint falla? ¿Cómo medirías la efectividad de un equipo?'
            },
            {
                'job_title': 'Arquitecto de Software',
                'modality': 'remoto',
                'communication_rating': 'good',
                'difficulty_rating': 'very_difficult',
                'response_time_rating': 'few_days',
                'overall_rating': 3,
                'pros': 'Proyectos de arquitectura muy desafiantes y la oportunidad de diseñar sistemas desde cero. Tecnología de vanguardia.',
                'cons': 'El proceso fue extremadamente técnico con preguntas sobre patrones de diseño, escalabilidad y performance.',
                'interview_questions': '¿Cómo diseñarías un sistema de microservicios? ¿Qué patrones usarías para alta disponibilidad? ¿Cómo manejarías la consistencia de datos?'
            },
            {
                'job_title': 'Vendedor',
                'modality': 'presencial',
                'communication_rating': 'excellent',
                'difficulty_rating': 'easy',
                'response_time_rating': 'immediate',
                'overall_rating': 4,
                'pros': 'Producto muy bueno y fácil de vender. La empresa da excelente soporte y herramientas de ventas.',
                'cons': 'Las metas de ventas pueden ser ambiciosas, pero son alcanzables con esfuerzo.',
                'interview_questions': '¿Cómo cerrarías una venta difícil? ¿Qué harías si un cliente dice que no tiene presupuesto? ¿Cómo construirías una relación a largo plazo?'
            },
            {
                'job_title': 'Científico de Datos',
                'modality': 'híbrido',
                'communication_rating': 'good',
                'difficulty_rating': 'very_difficult',
                'response_time_rating': 'next_day',
                'overall_rating': 3,
                'pros': 'Datos muy ricos y la oportunidad de trabajar con machine learning avanzado. El equipo técnico es muy fuerte.',
                'cons': 'El proceso fue muy exigente con preguntas sobre algoritmos, estadística y programación. Tuvieron que resolver un caso práctico complejo.',
                'interview_questions': '¿Cómo implementarías un modelo de recomendación? ¿Qué es overfitting y cómo lo evitarías? ¿Cómo evaluarías la calidad de un modelo?'
            },
            {
                'job_title': 'Gerente de Proyectos',
                'modality': 'presencial',
                'communication_rating': 'excellent',
                'difficulty_rating': 'moderate',
                'response_time_rating': 'same_day',
                'overall_rating': 4,
                'pros': 'Proyectos muy variados y la oportunidad de trabajar con equipos multidisciplinarios. La empresa valora la gestión profesional.',
                'cons': 'Algunas veces hay que lidiar con stakeholders muy exigentes y plazos ajustados.',
                'interview_questions': '¿Cómo manejarías un proyecto que se está retrasando? ¿Qué herramientas de gestión prefieres? ¿Cómo comunicarías malas noticias?'
            },
            {
                'job_title': 'Especialista en Talento',
                'modality': 'remoto',
                'communication_rating': 'excellent',
                'difficulty_rating': 'easy',
                'response_time_rating': 'immediate',
                'overall_rating': 5,
                'pros': 'Empresa con cultura muy positiva y realmente se preocupa por el desarrollo del talento. Políticas de diversidad e inclusión excelentes.',
                'cons': 'La carga de trabajo puede ser alta durante períodos de reclutamiento intensivo.',
                'interview_questions': '¿Cómo atraerías talento diverso? ¿Qué estrategias usarías para employer branding? ¿Cómo medirías la efectividad del reclutamiento?'
            }
        ]
        
        # Crear reseñas únicas
        created_reviews = 0
        used_combinations = set()
        
        while created_reviews < count and companies.exists():
            # Seleccionar empresa y usuario aleatorios
            company = random.choice(companies)
            user = random.choice(users)
            
            # Seleccionar template aleatorio
            template = random.choice(review_templates)
            
            # Crear combinación única
            combination = (company.id, user.id, template['job_title'])
            if combination in used_combinations:
                continue
            
            used_combinations.add(combination)
            
            # Crear reseña
            review = Review.objects.create(
                user_profile=user,
                company=company,
                job_title=template['job_title'],
                modality=template['modality'],
                communication_rating=template['communication_rating'],
                difficulty_rating=template['difficulty_rating'],
                response_time_rating=template['response_time_rating'],
                overall_rating=template['overall_rating'],
                pros=template['pros'],
                cons=template['cons'],
                interview_questions=template['interview_questions'],
                status='approved',
                is_approved=True,
                submission_date=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            
            created_reviews += 1
            self.stdout.write(f'✅ Reseña creada: {user.user.username} - {company.name} - {template["job_title"]}')
        
        self.stdout.write(f'✅ Se crearon {created_reviews} reseñas únicas!')
