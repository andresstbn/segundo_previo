from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vehicle, Trip, Rating

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    average_score = serializers.FloatField(read_only=True, required=False)
    
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
            'average_score',
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
        return super().create(validated_data)
    
    def get_fare(self, obj):
        base_fare = 1000
        
        if obj.driver:
            active_trips_of_driver = Trip.objects.filter(
                driver=obj.driver, 
                status__in=[Trip.STATUS_PENDING, Trip.STATUS_ONGOING]
            ).count()
            
            surge_multiplier = 1 + (active_trips_of_driver / 10)
            fare = int(base_fare * surge_multiplier)
        else:
            fare = base_fare
            
        return fare