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


class PassengerViewSet(viewsets.ReadOnlyModelViewSet):
   
    queryset = User.objects.filter(is_driver=False)  
    serializer_class = UserSerializer
   

    @action(detail=True, methods=['get'], url_path='trips')
    def trips(self, request, pk=None):
        
        trips = Trip.objects.filter(passenger_id=pk) 
        serializer = TripSerializer(trips, many=True)  
        return Response(serializer.data)


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar trips.

    Soporta filtro por driver con ?driver=<id>.
    """
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    filter_backends = [DjangoFilterBackend]

    filterset_fields = ['driver']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['driver']

    @action(detail=False, methods=['get'], url_path='active-count')
    def active_count(self, request):
        """
        Endpoint para contar los viajes en estado PENDING y ONGOING.
        """
        pending_count = Trip.objects.filter(status=Trip.STATUS_PENDING).count()
        ongoing_count = Trip.objects.filter(status=Trip.STATUS_ONGOING).count()

        return Response({
            "pending": pending_count,
            "ongoing": ongoing_count
        })

class DriverViewSet(viewsets.ReadOnlyModelViewSet):
   
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    
    

    @action(detail=False, methods=['get'], url_path='top-rated')
    def top_rated(self, request):
        drivers = (
            User.objects.filter(is_driver=True)
            .annotate(average_score=Avg('trips_as_driver__rating__score'))  # Traverse relationships
            .order_by('-average_score')[:5] 
        )

        # Prepare the response data
        response_data = []
        for driver in drivers:
            response_data.append({
                "id": driver.id,
                "name": driver.get_full_name() if hasattr(driver, 'get_full_name') else driver.username,
                "average_score": driver.average_score or 0
            })

        return Response(response_data)


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
