from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Render has no separate web server, so uploaded files (payment proofs,
    # property images) are served straight from the app process. For durable
    # storage attach a Render disk to MEDIA_ROOT or switch to external
    # storage (e.g. Cloudinary / S3) — uploads are otherwise wiped on deploy.
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
            name="media",
        ),
    ]

