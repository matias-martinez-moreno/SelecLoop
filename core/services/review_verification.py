# core/services/review_verification.py
import logging
import re

logger = logging.getLogger(__name__)

# Intentar importar dependencias de ML
try:
    import torch
    from transformers import pipeline
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("torch or transformers not available, will use basic checks only")

class ReviewVerificationService:
    def __init__(self):
        self.toxicity_pipeline = None
        self.sentiment_pipeline = None
        self.models_loaded = False
        self._load_models()
    
    def _load_models(self):
        if not ML_AVAILABLE:
            logger.info("ML libraries not available, skipping model loading")
            self.models_loaded = False
            return
            
        try:
            # Modelo para toxicidad y odio
            self.toxicity_pipeline = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=-1  # CPU para evitar problemas de GPU
            )
            
            # Modelo para sentimiento extremo
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1
            )
            
            self.models_loaded = True
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.models_loaded = False
    
    def verify_review(self, text):
        """
        Verifica si una reseña es apropiada - Anti-odio y anti-contenido fuera de lugar
        """
        # Solo rechazar si es completamente vacío
        if not text or len(text.strip()) < 1:
            return {
                'is_appropriate': False,
                'reason': 'Texto vacío',
                'confidence': 1.0,
                'category': 'insufficient_content'
            }
        
        try:
            # Verificaciones básicas primero
            basic_check = self._comprehensive_content_check(text)
            if not basic_check['is_appropriate']:
                return basic_check
            
            # Si los modelos no se cargaron, usar solo verificaciones básicas
            if not self.models_loaded:
                logger.warning("Models not loaded, using basic checks only")
                return {
                    'is_appropriate': basic_check['is_appropriate'],
                    'reason': basic_check['reason'],
                    'confidence': basic_check['confidence'],
                    'category': basic_check['category']
                }
            
            # Verificar toxicidad y odio con el modelo
            try:
                toxicity_result = self.toxicity_pipeline(text)
                toxicity_score = 0
                toxic_categories = []
                
                for result in toxicity_result:
                    if result['label'] in ['TOXIC', 'SEVERE_TOXIC', 'THREAT', 'INSULT', 'IDENTITY_ATTACK']:
                        toxicity_score = max(toxicity_score, result['score'])
                        toxic_categories.append(result['label'])
                
                # Verificar sentimiento extremo
                sentiment_result = self.sentiment_pipeline(text)
                sentiment_score = sentiment_result[0]['score']
                sentiment_label = sentiment_result[0]['label']
                
                # Lógica de decisión más estricta
                is_appropriate = True
                reason = "Reseña apropiada"
                confidence = 0.5
                category = 'appropriate'
                
                # Detectar odio y contenido ofensivo
                if toxicity_score > 0.6:  # Umbral más bajo para ser más estricto
                    is_appropriate = False
                    reason = f"Contenido tóxico detectado: {', '.join(toxic_categories)}"
                    confidence = toxicity_score
                    category = 'toxic'
                elif sentiment_score > 0.75 and sentiment_label == 'NEGATIVE':
                    # Umbral reducido para detectar sentimiento negativo extremo más agresivo
                    is_appropriate = False
                    reason = "Sentimiento extremadamente negativo y agresivo"
                    confidence = sentiment_score
                    category = 'hate_speech'
                
                return {
                    'is_appropriate': is_appropriate,
                    'reason': reason,
                    'confidence': confidence,
                    'category': category,
                    'toxicity_score': toxicity_score,
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label,
                    'toxic_categories': toxic_categories
                }
                
            except Exception as model_error:
                logger.error(f"Error using ML models: {model_error}")
                # Fallback a verificaciones básicas
                return basic_check
            
        except Exception as e:
            logger.error(f"Error in review verification: {e}", exc_info=True)
            # En caso de error, aprobar la reseña para no rechazar contenido legítimo
            return {
                'is_appropriate': True,
                'reason': f'Error en verificación automática, aprobada por defecto',
                'confidence': 0.5,
                'category': 'appropriate'
            }
    
    def _comprehensive_content_check(self, text):
        """Verificaciones exhaustivas anti-odio y anti-contenido fuera de lugar"""
        
        # Palabras de odio y ofensivas en español (expandida)
        hate_words = [
            'puta', 'mierda', 'joder', 'cabrón', 'hijo de puta', 'estúpido', 
            'idiota', 'imbécil', 'gilipollas', 'maricón', 'puto', 'hijueputa',
            'malparido', 'gonorrea', 'hijueputa', 'malparido', 'mamahuevo',
            'gonorrea', 'cerote', 'verga', 'pendejo', 'culero', 'chingar',
            'baboso', 'tarado', 'bobo', 'huevón', 'marica', 'manco', 'inútil'
        ]
        
        # Palabras discriminatorias
        discriminatory_words = [
            'negro de mierda', 'india puta', 'chino marica', 'gordo asqueroso',
            'flaco desgraciado', 'feo del carajo', 'viejo mierda', 'mujer huevona',
            'hombre marica', 'gay puto', 'lesbiana asquerosa'
        ]
        
        # Contenido fuera de lugar - SPAM FINANCIERO (prioridad alta)
        spam_financial_keywords = [
            'bitcoin', 'forex', 'inversión', 'trading', 'crypto', 'criptomoneda',
            'invertir', 'ganar dinero', 'usd', 'dólares', 'dollar', 'profits',
            'get rich', 'dinero fácil', 'sin riesgo', '100% seguro', 'ganancias'
        ]
        
        # Contenido fuera de lugar - OTROS TEMAS
        off_topic_indicators = [
            'medicina', 'doctor', 'hospital', 'enfermedad', 'tratamiento',
            'política', 'gobierno', 'presidente', 'elecciones', 'votar',
            'deportes', 'fútbol', 'partido', 'equipo', 'jugador',
            'videojuegos', 'playstation', 'xbox', 'fifa', 'call of duty'
        ]
        
        text_lower = text.lower()
        
        # PRIORIDAD 1: Detectar SPAM financiero - SOLO 1 keyword es suficiente
        spam_count = 0
        for keyword in spam_financial_keywords:
            if keyword in text_lower:
                spam_count += 1
        
        if spam_count >= 1:  # Si tiene al menos 1 keyword de spam financiero
            return {
                'is_appropriate': False,
                'reason': 'Spam financiero o publicidad detectada',
                'confidence': 0.95,
                'category': 'spam'
            }
        
        # PRIORIDAD 2: Verificar palabras de odio
        hate_count = 0
        for word in hate_words:
            if word in text_lower:
                hate_count += 1
        
        if hate_count > 0:
            return {
                'is_appropriate': False,
                'reason': f'Lenguaje ofensivo detectado ({hate_count} palabras)',
                'confidence': 0.9,
                'category': 'hate_speech'
            }
        
        # PRIORIDAD 3: Verificar palabras discriminatorias
        discrimination_count = 0
        for phrase in discriminatory_words:
            if phrase in text_lower:
                discrimination_count += 1
        
        if discrimination_count > 0:
            return {
                'is_appropriate': False,
                'reason': 'Lenguaje discriminatorio y ofensivo detectado',
                'confidence': 0.95,
                'category': 'hate_speech'
            }
        
        # PRIORIDAD 4: Verificar contenido fuera de lugar (otros temas)
        off_topic_count = 0
        for indicator in off_topic_indicators:
            if indicator in text_lower:
                off_topic_count += 1
        
        if off_topic_count > 2:  # Más de 2 indicadores de contenido fuera de lugar
            return {
                'is_appropriate': False,
                'reason': 'Contenido fuera de lugar o no relacionado con la empresa',
                'confidence': 0.8,
                'category': 'off_topic'
            }
        
        # Verificar spam (repeticiones excesivas)
        words = text.split()
        if len(words) > 10:
            word_count = {}
            for word in words:
                if len(word) > 3:  # Solo palabras de más de 3 caracteres
                    word_count[word] = word_count.get(word, 0) + 1
                    if word_count[word] > len(words) * 0.25:  # Más del 25% repetición
                        return {
                            'is_appropriate': False,
                            'reason': 'Posible spam detectado (repeticiones excesivas)',
                            'confidence': 0.8,
                            'category': 'spam'
                        }
        
        # NO rechazar por longitud - solo por contenido ofensivo o fuera de lugar
        # Si pasa todas las verificaciones anteriores, aprobar
        return {'is_appropriate': True, 'reason': 'Contenido apropiado', 'confidence': 0.5, 'category': 'appropriate'}
    
    def _detect_off_topic(self, text):
        """Detecta si el contenido está fuera de lugar"""
        off_topic_indicators = [
            'crypto', 'bitcoin', 'inversión', 'forex', 'trading',
            'medicina', 'doctor', 'hospital', 'enfermedad',
            'política', 'gobierno', 'presidente', 'elecciones',
            'deportes', 'fútbol', 'partido', 'equipo'
        ]
        
        text_lower = text.lower()
        off_topic_count = sum(1 for indicator in off_topic_indicators if indicator in text_lower)
        
        return off_topic_count > 2
