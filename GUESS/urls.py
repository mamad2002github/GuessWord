# GUESS/urls.py

from django.contrib import admin
from django.urls import path, include
# ------------- BEGIN NEW/MODIFIED SECTION (Imports for drf-spectacular) -------------
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
# ------------- END NEW/MODIFIED SECTION -------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('game.urls')), # URLهای اپلیکیشن game شما

    # ------------- BEGIN NEW/MODIFIED SECTION (URLs for drf-spectacular) -------------
    # مسیر برای فایل schema ی OpenAPI 3 (معمولاً یک فایل YAML یا JSON)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # رابط کاربری Swagger (توصیه شده)
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # رابط کاربری ReDoc (یک جایگزین دیگر)
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # ------------- END NEW/MODIFIED SECTION -------------
]