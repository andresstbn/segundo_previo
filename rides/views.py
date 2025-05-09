from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.db.models import Avg
from .models import Rating, Trip, Vehicle
from .serializers import (
    RatingSerializer,
    TripSerializer,
    UserSerializer,
    VehicleSerializer,
)
from rest_framework import permissions, viewsets
from .models import Trip
from .serializers import TripSerializer
from rest_framework import serializers
from .models import Trip
from .models import Rating
from django.db import models
from .models import Rating
from django.contrib.auth import get_user_model



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
    permission_classes = [permissions.IsAuthenticated] 

    @action(detail=True, methods=['post'], url_path='toggle-availability')
    def toggle_availability(self, request, pk=None):
        """
        Cambia el estado de disponibilidad del vehículo.
        """
        vehicle = self.get_object()
        vehicle.is_available = not vehicle.is_available
        vehicle.save()
        return Response({'is_available': vehicle.is_available})

    @action(detail=False, methods=['get'], url_path='models-summary')
    def models_summary(self, request):
        """
        Devuelve una lista con el número de vehículos por modelo.
        """
        summary = (
            Vehicle.objects
            .values('model')
            .annotate(count=Count('id'))
            .order_by('model')
        )
        return Response(summary)

class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar trips.
    Soporta filtro por driver con ?driver=<id>.
    """
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['driver', 'status']

    @action(detail=False, methods=['get'], url_path='active-count')
    def active_count(self, request):
        """
        Devuelve un objeto con el número de viajes en estado PENDING y ONGOING.
        Ejemplo de respuesta: { "pending": 12, "ongoing": 5 }
        """
        pending_count = Trip.objects.filter(status='PENDING').count()
        ongoing_count = Trip.objects.filter(status='ONGOING').count()
        
        return Response({
            "pending": pending_count,
            "ongoing": ongoing_count
        })


    
'''class TripSerializer(serializers.ModelSerializer):
    """
    Serializador para los viajes.
    """
    fare = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = '__all__'  # Incluye todos los campos del modelo, excepto 'fare' que se agrega por separado.

    def get_fare(self, obj):
        """
        Calcula la tarifa dinámica basada en los viajes activos del conductor.
        """
        # Obtener el driver (conductor) del viaje actual
        driver = obj.driver

        # Contar los viajes activos (PENDING y ONGOING) del conductor
        active_trips_of_driver = Trip.objects.filter(
            driver=driver,
            status__in=['PENDING', 'ONGOING']
        ).count()

        # Calcular el multiplicador de la tarifa basado en los viajes activos
        surge_multiplier = 1 + (active_trips_of_driver / 10)

        # Calcular la tarifa final
        base_fare = 1000
        fare = int(base_fare * surge_multiplier)

        return fare'''


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] 

    @action(detail=False, methods=['get'], url_path='trending')
    def trending_drivers(self, request):
        """
        Endpoint que devuelve los 5 conductores con el mayor average_score,
        calculado como el promedio de los puntajes de rating.
        """
        # Calcular el average_score por conductor, ordenar por él y limitar a los 5 primeros
        trending_drivers = (
            User.objects.filter(is_driver=True)
            .annotate(average_score=Avg('ratings__score'))  # Asume que Rating tiene un campo 'score'
            .order_by('-average_score')  # Ordenar de mayor a menor
            .values('id', 'username', 'average_score')[:5]  # Limitar a los 5 primeros
        )

        # Devuelve los resultados
        return Response(trending_drivers)

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

from django_filters import rest_framework as filters

class TripFilter(filters.FilterSet):
    driver = filters.NumberFilter(field_name='driver')
    status = filters.CharFilter(field_name='status', lookup_expr='exact')

    class Meta:
        model = Trip
        fields = ['driver', 'status']
