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
    fare = serializers.SerializerMethodField(read_only=True)

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
            'fare',
        ]

    def create(self, validated_data):
        # Passthrough to viewset logic; trip.request view will assign driver
        return super().create(validated_data)
    
    def get_fare(self, obj):
        if obj.driver:
            active_trips = obj.driver.trips_as_driver.filter(
                status__in=[Trip.STATUS_PENDING, Trip.STATUS_ONGOING]).count()
            base_fare = 1000
            surge_multiplier = 1+(active_trips/10)
            return int(base_fare * surge_multiplier)
        return None
    
    # def get_fare(self, obj):
    #     if obj.driver:
    #         active_trips = obj.driver.trips_as_driver.filter(
    #             status__in=[Trip.STATUS_PENDING, Trip.STATUS_ONGOING]
    #         ).count()
    #         base_fare = 1000
    #         surge_multiplier = 1 + (active_trips / 10)
    #         return int(base_fare * surge_multiplier)
    #     return None
