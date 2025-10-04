# ===== CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN =====
# Este archivo ya no contiene configuración de admin.
# Los modelos han sido movidos a sus respectivas aplicaciones:
#
# - UserProfile, OnboardingStatus -> accounts/admin.py
# - Company -> companies/admin.py  
# - Review, PendingReview -> reviews/admin.py
# - WorkHistory -> work_history/admin.py
# - Achievement, UserAchievement -> achievements/admin.py
#
# Este archivo se mantiene por compatibilidad, pero está vacío.

from django.contrib import admin
# Los imports han sido movidos a las aplicaciones específicas