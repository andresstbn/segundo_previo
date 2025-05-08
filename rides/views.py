from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


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

    @action(detail=False, methods=['post'])
    def request(self, request):
        "2.1.1"
        drivers = User.objects.filter(is_driver=True, is_available=True)

        "2.1.2"
        drivers = drivers.annotate(
            active_trips=Count('trips_as_driver', filter=Q(trips_as_driver__status__in=['PENDING', 'ONGOING']))
        )

        "2.1.3"
        selected_driver = drivers.order_by('active_trips').first()

        if not selected_driver:
            return Response({"detail": "No drivers available."}, status=status.HTTP_400_BAD_REQUEST)

        "2.1.4"
        trip = Trip.objects.create(
            passenger=request.user,
            driver=selected_driver,
            status='PENDING'
        )

        "2.1.5"
        serializer = TripSerializer(trip)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    "2.2.1"
    @action(detail=True, methods=['get'], url_path='status')
    def get_status(self, request, pk=None):
        trip = self.get_object()
        return Response({"status": trip.status}, status=status.HTTP_200_OK)


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
