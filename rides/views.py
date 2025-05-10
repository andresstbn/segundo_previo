from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import Rating, Trip, Vehicle
from .serializers import (
    RatingSerializer,
    TripSerializer,
    UserSerializer,
    VehicleSerializer,
)

User = get_user_model()


class HomeView(TemplateView):
    """
    Vista de inicio de la aplicación.
    """
    template_name = 'rides/home.html'


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de vehículos.
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    
    @action(detail=False, methods=['get'], url_path='models-summary')
    def models_summary(self, request):
        
        summary = Vehicle.objects.values('model').annotate(count=Count('model'))
        return Response(summary)
    
    @action(detail=True, methods=['post'], url_path='toggle-availability')
    def toggle_availability(self, request, pk=None):
        
        vehicle = Vehicle.objects.get(pk=pk)
        vehicle.driver.is_available = not vehicle.driver.is_available
        vehicle.driver.save()
        vehicle.save()
        return Response({"is_available": vehicle.driver.is_available})


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar trips.

    Soporta filtro por driver con ?driver=<id>.
    """
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['driver']


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class RatingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para listar, detallar y actualizar ratings, pero no borrar.
    """
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
