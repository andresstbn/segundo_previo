from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vehicle, Trip, Rating
from django.db.models import Count

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_driver',
            'is_passenger',
            'is_available',
        ]


class VehicleSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'driver',
            'license_plate',
            'model',
            'capacity',
        ]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = [
            'id',
            'trip',
            'score',
            'comment',
            'created_at',
        ]


class TripSerializer(serializers.ModelSerializer):
    passenger = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)
    rating = RatingSerializer(read_only=True)
    fare = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'passenger',
            'driver',
            'requested_at',
            'start_time',
            'end_time',
            'status',
            'rating',
            'fare',  # Incluido el campo fare
        ]

    def get_fare(self, obj):
        """
        Método para calcular la tarifa de un viaje en base a los viajes activos del conductor.
        """
        base_fare = 1000  # Tarifa base
        active_trips_of_driver = Trip.objects.filter(
            driver=obj.driver, status__in=['PENDING', 'ONGOING']
        ).count()  # Contamos los viajes activos del conductor

        # Calculamos el multiplicador basado en los viajes activos
        surge_multiplier = 1 + (active_trips_of_driver / 10)
        fare = int(base_fare * surge_multiplier)  # Cálculo final de la tarifa
        return fare

    def create(self, validated_data):
        # Passthrough to viewset logic; trip.request view will assign driver
        return super().create(validated_data)
