from django.urls import include, path

urlpatterns = [
    path("api/", include("store.urls")),
]

handler404 = "store.views.json_not_found"
handler500 = "store.views.json_server_error"
