# core/services/review_verification.py
import logging
import re

logger = logging.getLogger(__name__)

# Intentar importar dependencias de ML
try:
    import torch
    from transformers import pipeline
    ML_AVAILABLE = True
    logger.debug("ML libraries (torch, transformers) successfully imported")
except ImportError as e:
    ML_AVAILABLE = False
    logger.warning(f"torch or transformers not available: {e}. Will use basic checks only.")

class ReviewVerificationService:
    """
    Servicio Singleton para verificación de reseñas con modelos de Hugging Face.
    Los modelos se cargan una sola vez al crear la primera instancia y se reutilizan.
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Patrón Singleton: solo una instancia en toda la aplicación"""
        if cls._instance is None:
            cls._instance = super(ReviewVerificationService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Solo inicializar una vez, aunque se llame múltiples veces"""
        if not ReviewVerificationService._initialized:
            self.toxicity_pipeline = None
            self.sentiment_pipeline = None
            self.models_loaded = False
            self._load_models()  # ← Se carga SOLO la primera vez
            ReviewVerificationService._initialized = True
    
    def _load_models(self):
        if not ML_AVAILABLE:
            logger.info("⚠️ ML libraries not available, skipping model loading. Using basic checks only.")
            self.models_loaded = False
            return
            
        try:
            logger.info("🔄 Loading Hugging Face models... This may take a few minutes on first run.")
            
            # Modelo para toxicidad y odio
            # Usar device=-1 para CPU (más compatible) o 0 para GPU si está disponible
            try:
                self.toxicity_pipeline = pipeline(
                    "text-classification",
                    model="unitary/toxic-bert",
                    device=-1  # CPU para evitar problemas de GPU
                )
                logger.info("✅ Toxicity model (unitary/toxic-bert) loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading toxicity model: {e}")
                self.toxicity_pipeline = None
            
            # Modelo para sentimiento extremo
            try:
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    device=-1  # CPU para evitar problemas de GPU
                )
                logger.info("✅ Sentiment model (cardiffnlp/twitter-roberta-base-sentiment-latest) loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading sentiment model: {e}")
                self.sentiment_pipeline = None
            
            # Verificar que al menos uno de los modelos se cargó
            if self.toxicity_pipeline is not None or self.sentiment_pipeline is not None:
                self.models_loaded = True
                logger.info("✅ Hugging Face models loaded successfully. ML verification is now ACTIVE.")
            else:
                self.models_loaded = False
                logger.warning("⚠️ Failed to load any ML models. Using basic checks only.")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}", exc_info=True)
            self.models_loaded = False
            logger.warning("Falling back to basic content checks only.")
    
    def verify_review(self, text):
        """
        Verifica si una reseña es apropiada - Anti-odio y anti-contenido fuera de lugar
        """
        # Log inicial muy visible - USAR WARNING para que se vea en consola
        logger.warning("=" * 80)
        logger.warning("🔍 INICIANDO VERIFICACIÓN DE RESEÑA")
        logger.warning(f"📝 Texto a verificar (primeros 100 chars): {text[:100]}...")
        logger.warning(f"🤖 Modelos ML cargados: {self.models_loaded}")
        logger.warning(f"🤖 Toxicity pipeline disponible: {self.toxicity_pipeline is not None}")
        logger.warning(f"🤖 Sentiment pipeline disponible: {self.sentiment_pipeline is not None}")
        logger.warning("=" * 80)
        
        # Solo rechazar si es completamente vacío
        if not text or len(text.strip()) < 1:
            logger.warning("❌ Texto vacío - RECHAZADO")
            return {
                'is_appropriate': False,
                'reason': 'Texto vacío',
                'confidence': 1.0,
                'category': 'insufficient_content'
            }
        
        try:
            # Verificaciones básicas primero
            logger.warning("🔎 Ejecutando verificaciones básicas...")
            basic_check = self._comprehensive_content_check(text)
            if not basic_check['is_appropriate']:
                logger.warning("=" * 80)
                logger.warning(f"❌❌❌ RECHAZADO por verificaciones básicas ❌❌❌")
                logger.warning(f"   Razón: {basic_check['reason']}")
                logger.warning(f"   Confianza: {basic_check['confidence']}")
                logger.warning(f"   Categoría: {basic_check['category']}")
                logger.warning("=" * 80)
                return basic_check
            logger.warning("✅✅✅ Verificaciones básicas PASADAS - Continuando con ML...")
            
            # Si los modelos no se cargaron, usar solo verificaciones básicas
            if not self.models_loaded:
                logger.warning("=" * 80)
                logger.warning("⚠️⚠️⚠️ MODELOS ML NO CARGADOS - USANDO SOLO VERIFICACIONES BÁSICAS ⚠️⚠️⚠️")
                logger.warning("=" * 80)
                return {
                    'is_appropriate': basic_check['is_appropriate'],
                    'reason': basic_check['reason'],
                    'confidence': basic_check['confidence'],
                    'category': basic_check['category']
                }
            
            # Log muy visible para confirmar que se está usando ML - USAR WARNING
            logger.warning("=" * 80)
            logger.warning("🤖🤖🤖 USANDO MODELOS ML PARA VERIFICACIÓN 🤖🤖🤖")
            logger.warning(f"✅ Toxicity pipeline: {self.toxicity_pipeline is not None}")
            logger.warning(f"✅ Sentiment pipeline: {self.sentiment_pipeline is not None}")
            logger.warning("=" * 80)
            
            # Verificar toxicidad y odio con el modelo
            try:
                toxicity_score = 0
                toxic_categories = []
                sentiment_score = 0
                sentiment_label = 'NEUTRAL'
                
                # Verificar toxicidad si el modelo está disponible
                if self.toxicity_pipeline is not None:
                    try:
                        toxicity_result = self.toxicity_pipeline(text, top_k=None)  # Obtener todos los resultados
                        
                        # El modelo unitary/toxic-bert puede devolver diferentes formatos
                        # Puede ser una lista de diccionarios o un diccionario único
                        if toxicity_result:
                            # Normalizar a lista si es necesario
                            if not isinstance(toxicity_result, list):
                                toxicity_result = [toxicity_result]
                            
                            # Procesar todos los resultados
                            for result in toxicity_result:
                                if isinstance(result, dict):
                                    label = str(result.get('label', '')).upper()
                                    score = float(result.get('score', 0))
                                    
                                    # Categorías tóxicas que queremos detectar
                                    toxic_labels = ['TOXIC', 'SEVERE_TOXIC', 'THREAT', 'INSULT', 'IDENTITY_ATTACK', 'OBSCENE', 'HATE']
                                    
                                    # Verificar si el label contiene alguna categoría tóxica
                                    is_toxic = False
                                    for toxic_label in toxic_labels:
                                        if toxic_label in label:
                                            is_toxic = True
                                            if score > toxicity_score:
                                                toxicity_score = score
                                            if label not in toxic_categories:
                                                toxic_categories.append(label)
                                            break
                                    
                                    # Si no es una categoría conocida pero el score es alto, también considerarlo
                                    if not is_toxic and score > 0.6:
                                        toxicity_score = max(toxicity_score, score)
                                        if label not in toxic_categories:
                                            toxic_categories.append(label)
                                    
                                    # También considerar cualquier score alto como potencialmente tóxico
                                    if score > 0.5:
                                        toxicity_score = max(toxicity_score, score)
                                        
                    except Exception as tox_error:
                        logger.warning(f"Error in toxicity detection: {tox_error}", exc_info=True)
                        # Continuar con otros checks
                
                # Verificar sentimiento extremo si el modelo está disponible
                if self.sentiment_pipeline is not None:
                    try:
                        sentiment_result = self.sentiment_pipeline(text, top_k=None)  # Obtener todos los resultados
                        if sentiment_result and len(sentiment_result) > 0:
                            # El modelo puede devolver múltiples resultados, buscar el más negativo
                            if isinstance(sentiment_result, list):
                                # Buscar el resultado más negativo
                                for res in sentiment_result:
                                    if isinstance(res, dict):
                                        label = str(res.get('label', '')).upper()
                                        score = float(res.get('score', 0))
                                        # Si es negativo y tiene score alto, usarlo
                                        if any(neg in label for neg in ['NEGATIVE', 'NEG', 'LABEL_2', 'LABEL_1']) and score > sentiment_score:
                                            sentiment_score = score
                                            sentiment_label = label
                                        # Si no encontramos negativo, usar el primero
                                        elif sentiment_score == 0:
                                            sentiment_score = score
                                            sentiment_label = label
                            else:
                                sentiment_score = float(sentiment_result.get('score', 0))
                                sentiment_label = str(sentiment_result.get('label', 'NEUTRAL'))
                        
                        # Log para debugging - USAR WARNING
                        logger.warning(f"📊 ML Sentiment analysis - Score: {sentiment_score}, Label: {sentiment_label}")
                    except Exception as sent_error:
                        logger.warning(f"Error in sentiment analysis: {sent_error}")
                        # Continuar con otros checks
                
                # Log para debugging - USAR WARNING
                logger.warning(f"📊 ML Toxicity analysis - Score: {toxicity_score}, Categories: {toxic_categories}")
                
                # Lógica de decisión más estricta
                is_appropriate = True
                reason = "Reseña apropiada"
                confidence = 0.5
                category = 'appropriate'
                
                # Normalizar etiqueta de sentimiento para comparación
                sentiment_label_upper = str(sentiment_label).upper()
                is_negative_sentiment = any(neg in sentiment_label_upper for neg in ['NEGATIVE', 'NEG', 'LABEL_2', 'LABEL_1', 'LABEL_0'])
                
                # Detectar palabras clave muy negativas en el texto (fallback adicional)
                text_lower = text.lower()
                very_negative_keywords = ['fraude', 'estafan', 'incompetentes', 'desastre', 'terrible', 'horrible', 
                                        'desastrosa', 'fraudulento', 'estafa', 'mentirosos', 'mediocre', 'asombroso',
                                        'peor experiencia', 'completo desastre', 'pérdida de tiempo']
                has_very_negative_keywords = any(keyword in text_lower for keyword in very_negative_keywords)
                
                # Detectar odio y contenido ofensivo - UMBRALES MÁS AGRESIVOS
                # Prioridad 1: Toxicidad moderada/alta
                if toxicity_score > 0.4:  # Umbral más bajo: 0.4
                    is_appropriate = False
                    reason = f"Contenido tóxico detectado: {', '.join(toxic_categories) if toxic_categories else 'contenido ofensivo'}"
                    confidence = min(toxicity_score, 0.99)
                    category = 'toxic'
                    logger.warning(f"Review rejected by ML - Toxicity: {toxicity_score}")
                # Prioridad 2: Sentimiento muy negativo (umbral más bajo)
                elif sentiment_score > 0.55 and is_negative_sentiment:  # Umbral más bajo: 0.55
                    is_appropriate = False
                    reason = "Sentimiento extremadamente negativo y agresivo detectado"
                    confidence = min(sentiment_score, 0.99)
                    category = 'hate_speech'
                    logger.warning(f"Review rejected by ML - Sentiment: {sentiment_score}, Label: {sentiment_label}")
                # Prioridad 3: Palabras clave muy negativas + sentimiento negativo
                elif has_very_negative_keywords and is_negative_sentiment and sentiment_score > 0.5:
                    is_appropriate = False
                    reason = "Contenido extremadamente negativo con lenguaje inapropiado detectado"
                    confidence = max(sentiment_score, 0.7)
                    category = 'hate_speech'
                    logger.warning(f"Review rejected by ML - Very negative keywords + sentiment: {sentiment_score}")
                # Prioridad 4: Toxicidad baja pero con sentimiento negativo fuerte
                elif toxicity_score > 0.25 and is_negative_sentiment and sentiment_score > 0.6:  # Umbral más bajo
                    is_appropriate = False
                    reason = "Contenido potencialmente ofensivo detectado"
                    confidence = (toxicity_score + sentiment_score) / 2
                    category = 'toxic'
                    logger.warning(f"Review rejected by ML - Combined: toxicity={toxicity_score}, sentiment={sentiment_score}")
                # Prioridad 5: Solo sentimiento muy negativo (sin toxicidad)
                elif sentiment_score > 0.7 and is_negative_sentiment:
                    is_appropriate = False
                    reason = "Sentimiento extremadamente negativo detectado"
                    confidence = min(sentiment_score, 0.99)
                    category = 'hate_speech'
                    logger.warning(f"Review rejected by ML - Very negative sentiment only: {sentiment_score}")
                
                result = {
                    'is_appropriate': is_appropriate,
                    'reason': reason,
                    'confidence': confidence,
                    'category': category,
                    'toxicity_score': toxicity_score,
                    'sentiment_score': sentiment_score,
                    'sentiment_label': str(sentiment_label),
                    'toxic_categories': toxic_categories,
                    'ml_models_used': self.models_loaded
                }
                
                # Log final del resultado - MUY VISIBLE - USAR WARNING
                logger.warning("=" * 80)
                if is_appropriate:
                    logger.warning("✅✅✅ ML VERIFICACIÓN: APROBADA ✅✅✅")
                    logger.warning(f"   Razón: {reason}")
                    logger.warning(f"   Confianza: {confidence}")
                    logger.warning(f"   Toxicity Score: {toxicity_score}")
                    logger.warning(f"   Sentiment Score: {sentiment_score} ({sentiment_label})")
                else:
                    logger.warning("❌❌❌ ML VERIFICACIÓN: RECHAZADA ❌❌❌")
                    logger.warning(f"   Razón: {reason}")
                    logger.warning(f"   Confianza: {confidence}")
                    logger.warning(f"   Categoría: {category}")
                    logger.warning(f"   Toxicity Score: {toxicity_score}")
                    logger.warning(f"   Sentiment Score: {sentiment_score} ({sentiment_label})")
                    logger.warning(f"   Toxic Categories: {toxic_categories}")
                logger.warning("=" * 80)
                
                return result
                
            except Exception as model_error:
                logger.error("=" * 80)
                logger.error("❌❌❌ ERROR AL USAR MODELOS ML ❌❌❌")
                logger.error(f"   Error: {str(model_error)}")
                logger.error(f"   Traceback completo:")
                import traceback
                logger.error(traceback.format_exc())
                logger.error("   ⚠️ Usando fallback a verificaciones básicas")
                logger.error("=" * 80)
                # Fallback a verificaciones básicas
                return basic_check
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌❌❌ ERROR GENERAL EN VERIFICACIÓN ❌❌❌")
            logger.error(f"   Error: {str(e)}")
            logger.error(f"   Traceback completo:")
            import traceback
            logger.error(traceback.format_exc())
            logger.error("   ⚠️ Aprobando reseña por defecto para no bloquear contenido legítimo")
            logger.error("=" * 80)
            # En caso de error, aprobar la reseña para no rechazar contenido legítimo
            return {
                'is_appropriate': True,
                'reason': f'Error en verificación automática, aprobada por defecto',
                'confidence': 0.5,
                'category': 'error'
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
