from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg

from .models import Rating, Trip, Vehicle
from .serializers import (
    RatingSerializer,
    TripSerializer,
    UserSerializer,
    VehicleSerializer,
)

User = get_user_model()


class HomeView(TemplateView):
    template_name = 'rides/home.html'


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        vehicle = self.get_object()
        driver = vehicle.driver
        driver.is_available = not driver.is_available
        driver.save()
        return Response({'is_available': driver.is_available})
    
    @action(detail=False, methods=['get'])
    def models_summary(self, request):
        summary = Vehicle.objects.values('model').annotate(count=Count('id'))
        return Response(summary)


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['driver']
    
    @action(detail=False, methods=['get'])
    def active_count(self, request):
        pending_count = Trip.objects.filter(status=Trip.STATUS_PENDING).count()
        ongoing_count = Trip.objects.filter(status=Trip.STATUS_ONGOING).count()
        
        return Response({
            'pending': pending_count,
            'ongoing': ongoing_count
        })


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        top_drivers = User.objects.filter(
            is_driver=True, 
            trips_as_driver__rating__isnull=False
        ).annotate(
            average_score=Avg('trips_as_driver__rating__score')
        ).order_by('-average_score')[:5]
        
        serializer = self.get_serializer(top_drivers, many=True)
        return Response(serializer.data)


class PassengerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_passenger=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def trips(self, request, pk=None):
        passenger = self.get_object()
        trips = Trip.objects.filter(passenger=passenger)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)


class RatingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]