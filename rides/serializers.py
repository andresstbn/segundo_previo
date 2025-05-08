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
        ]

    def create(self, validated_data):
        # Passthrough to viewset logic; trip.request view will assign driver
        return super().create(validated_data)

    class UserSerializer(serializers.ModelSerializer):
        trip_count = serializers.SerializerMethodField(read_only=True)

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
            'trip_count',
        ]

    def get_trip_count(self, obj):
        if obj.is_driver:
            return obj.trips_as_driver.filter(status='COMPLETED').count()
        return None
