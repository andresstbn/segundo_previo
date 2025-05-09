from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
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
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        vehicle = self.get_object()
        vehicle.is_available = not vehicle.is_available
        vehicle.save()
        return Response({'is_available': vehicle.is_available}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def models_summary(self, request):
        resumen = (
            Vehicle.objects.values('model')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response(resumen)


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

    @action(detail=False, methods=['get'])
    def trending(self, request):
        conductores = (
            User.objects.filter(is_driver=True)
            .annotate(average_score=Avg('trips_as_driver__rating__score'))
            .order_by('-average_score')[:5]
        )
        data = [
            {
                "id": d.id,
                "username": d.username,
                "average_score": round(d.average_score or 0, 2)
            }
            for d in conductores
        ]
        return Response(data)
    





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

class PassangerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver pasajeros.
    """
    queryset = User.objects.filter(is_passenger=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    @action(detail=True, methods=['get'])
    def trips(self, request, pk=None):
        """
        Listar viajes de un pasajero.
        """
        trips = Trip.objects.filter(passenger_id=pk)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

