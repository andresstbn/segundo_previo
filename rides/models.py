from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    """
    Extiende el modelo de usuario para distinguir roles en la app de ride-sharing.
    """
    is_driver = models.BooleanField(
        default=False,
        help_text="¿Es un usuario que puede actuar como conductor?"
    )
    is_passenger = models.BooleanField(
        default=True,
        help_text="¿Es un usuario que actúa como pasajero?"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="¿Está disponible para recibir solicitudes de viaje?"
    )

    def __str__(self):
        return self.get_full_name() or self.username

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['username']


class Vehicle(models.Model):
    """
    Vehículo asociado a un conductor (User con is_driver=True).
    """
    driver = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='vehicle'
    )
    license_plate = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=4)

    def __str__(self):
        return f'{self.model} ({self.license_plate})'

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['license_plate']


class Trip(models.Model):
    """
    Viaje solicitado por un pasajero y asignado a un conductor.
    Estado: PENDING, ONGOING, COMPLETED, CANCELLED.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_ONGOING = 'ONGOING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_ONGOING,   'Ongoing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    passenger = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='trips_as_passenger'
    )
    driver = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips_as_driver'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    start_time   = models.DateTimeField(null=True, blank=True)
    end_time     = models.DateTimeField(null=True, blank=True)
    status       = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    def __str__(self):
        driver_name = self.driver.get_full_name() if self.driver else "unassigned"
        passenger_name = self.passenger.get_full_name()
        return f'Trip {self.id}: {passenger_name} → {driver_name}'

    class Meta:
        verbose_name = "Viaje"
        verbose_name_plural = "Viajes"
        ordering = ['-requested_at']


class Rating(models.Model):
    """
    Valoración de un viaje: relación uno a uno con Trip.
    Score de 1 a 5.
    """
    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='rating'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Rating {self.score} for Trip {self.trip.id}'

    class Meta:
        verbose_name = "Valoración"
        verbose_name_plural = "Valoraciones"
        ordering = ['-created_at']