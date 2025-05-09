from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vehicle, Trip, Rating

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
    fare = serializers.SerializerMethodField(read_only=True)  # Campo de solo lectura

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
            'fare',  # Agregar el campo fare al serializer
        ]

    def get_fare(self, obj):
        """
        Calcula la tarifa dinámica basada en los viajes activos del conductor.
        """
        # Obtener el driver (conductor) del viaje actual
        driver = obj.driver

        if not driver:
            return None  # Si no hay conductor asignado, no se calcula la tarifa

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

        return fare

    def create(self, validated_data):
        # Passthrough to viewset logic; trip.request view will assign driver
        return super().create(validated_data)
