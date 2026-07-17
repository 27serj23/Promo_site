# Модели базы данных для промо-сайта
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Дополнительные данные пользователя (телефон)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


class Campaign(models.Model):
    """Промо-кампания: название, владелец, участники."""
    name = models.CharField(max_length=200, verbose_name='Название')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns', verbose_name='Владелец')
    participants = models.ManyToManyField(User, related_name='participated_campaigns', blank=True, verbose_name='Участники')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Кампания'
        verbose_name_plural = 'Кампании'

    def __str__(self):
        return self.name


class House(models.Model):
    """Дом, который обходят в рамках кампании."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='houses', verbose_name='Кампания')
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=200, verbose_name='Улица')
    house_number = models.CharField(max_length=20, verbose_name='Номер дома')
    entrances = models.PositiveIntegerField(verbose_name='Количество подъездов')
    apartments_per_entrance = models.PositiveIntegerField(verbose_name='Квартир в подъезде')

    @property
    def total_apartments(self):
        """Общее количество квартир в доме."""
        return self.entrances * self.apartments_per_entrance

    class Meta:
        verbose_name = 'Дом'
        verbose_name_plural = 'Дома'

    def __str__(self):
        return f'{self.city}, {self.street}, {self.house_number}'


class ApartmentVisit(models.Model):
    """Запись об одном поквартирном обходе."""
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='visits', verbose_name='Дом')
    entrance = models.PositiveIntegerField(verbose_name='Подъезд')
    apartment_number = models.PositiveIntegerField(verbose_name='Номер квартиры')
    opened_door = models.BooleanField(verbose_name='Дверь открыли')
    reaction = models.CharField(
        max_length=20,
        choices=[('positive', 'Позитивно'), ('neutral', 'Нейтрально'), ('negative', 'Негативно')],
        blank=True, null=True,
        verbose_name='Реакция'
    )
    contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя контакта')
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон контакта')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    visited_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время обхода')
    visitor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Кто обошёл')

    class Meta:
        verbose_name = 'Поквартирный обход'
        verbose_name_plural = 'Поквартирные обходы'

    def __str__(self):
        return f'{self.house} – кв.{self.apartment_number}'
