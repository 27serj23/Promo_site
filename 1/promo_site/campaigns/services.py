# Бизнес-логика приложения (все операции с данными)
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.db import transaction
from django.http import Http404
from django.core.paginator import Paginator
from .models import Campaign, House, ApartmentVisit


# ---------- Кампании ----------

@transaction.atomic
def create_campaign(name, owner):
    """
    Создаёт новую кампанию. Владелец автоматически становится участником.
    Выполняется в транзакции для целостности данных.
    """
    if not name or not name.strip():
        raise ValueError('Название кампании не может быть пустым')
    if not owner:
        raise ValueError('Владелец кампании обязателен')

    campaign = Campaign.objects.create(name=name.strip(), owner=owner)
    campaign.participants.add(owner)
    return campaign


def get_campaign_for_user(campaign_id, user):
    """
    Получает кампанию по ID с проверкой прав доступа.
    Если пользователь не владелец и не участник — ошибка 404.
    """
    if not campaign_id:
        raise ValueError('ID кампании обязателен')
    if not user or not user.is_authenticated:
        raise Http404('Кампания не найдена')

    campaign = get_object_or_404(Campaign, id=campaign_id)
    if user != campaign.owner and not campaign.participants.filter(id=user.id).exists():
        raise Http404('Кампания не найдена')
    return campaign


def get_campaign_detail_data(campaign):
    """
    Возвращает данные для страницы кампании: дома, участники.
    Использует prefetch_related для оптимизации.
    """
    if not campaign:
        raise ValueError('Кампания обязательна')

    campaign = Campaign.objects.prefetch_related(
        'houses', 'participants'
    ).get(id=campaign.id)
    return {
        'campaign': campaign,
        'houses': campaign.houses.all(),
        'participants': campaign.participants.all(),
    }


def add_participant_to_campaign(campaign, username):
    """
    Добавляет пользователя в кампанию.
    Возвращает (успех, сообщение).
    """
    from django.contrib.auth.models import User

    if not campaign:
        return False, 'Кампания не указана.'
    if not username or not username.strip():
        return False, 'Имя пользователя не может быть пустым.'

    try:
        user_to_add = User.objects.get(username=username.strip())
        if user_to_add in campaign.participants.all():
            return False, f'{username} уже является участником.'
        campaign.participants.add(user_to_add)
        return True, f'{username} добавлен в кампанию!'
    except User.DoesNotExist:
        return False, 'Пользователь не найден.'


# ---------- Дома ----------

def add_house_to_campaign(campaign, city, street, house_number, entrances, apartments_per_entrance):
    """
    Добавляет дом в указанную кампанию.
    Проверяет обязательные поля и корректность значений.
    """
    if not campaign:
        raise ValueError('Кампания обязательна')
    if not city or not city.strip():
        raise ValueError('Город обязателен')
    if not street or not street.strip():
        raise ValueError('Улица обязательна')
    if not house_number or not house_number.strip():
        raise ValueError('Номер дома обязателен')
    if entrances < 1:
        raise ValueError('Количество подъездов должно быть положительным')
    if apartments_per_entrance < 1:
        raise ValueError('Количество квартир в подъезде должно быть положительным')

    return House.objects.create(
        campaign=campaign,
        city=city.strip(),
        street=street.strip(),
        house_number=house_number.strip(),
        entrances=entrances,
        apartments_per_entrance=apartments_per_entrance
    )


def get_house_with_visits(campaign, house_id, page_number=1, per_page=10):
    """
    Возвращает дом с пагинированными обходами.
    Использует select_related для оптимизации.
    """
    if not campaign:
        raise ValueError('Кампания обязательна')
    if not house_id:
        raise ValueError('ID дома обязателен')

    house = get_object_or_404(House, id=house_id, campaign=campaign)
    visits_qs = house.visits.select_related('visitor').order_by('-visited_at')

    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
    except (ValueError, TypeError):
        page_number = 1

    paginator = Paginator(visits_qs, per_page)
    visits = paginator.get_page(page_number)

    return house, visits


# ---------- Обходы ----------

def record_visit(house, visitor, entrance, apartment_number, opened_door,
                 reaction=None, contact_name=None, contact_phone=None, comment=None):
    """
    Сохраняет запись об обходе одной квартиры.
    Проверяет обязательные поля.
    """
    if not house:
        raise ValueError('Дом обязателен')
    if not visitor:
        raise ValueError('Посетитель обязателен')
    if entrance < 1:
        raise ValueError('Номер подъезда должен быть положительным')
    if apartment_number < 1:
        raise ValueError('Номер квартиры должен быть положительным')

    return ApartmentVisit.objects.create(
        house=house,
        visitor=visitor,
        entrance=entrance,
        apartment_number=apartment_number,
        opened_door=opened_door,
        reaction=reaction if reaction else None,
        contact_name=contact_name.strip() if contact_name else None,
        contact_phone=contact_phone.strip() if contact_phone else None,
        comment=comment.strip() if comment else None
    )


# ---------- Статистика ----------

def get_campaign_statistics(campaign):
    """
    Собирает статистику по кампании агрегациями на стороне БД.
    Не делает N+1 запросов.
    """
    if not campaign:
        raise ValueError('Кампания обязательна')

    visits = ApartmentVisit.objects.filter(house__campaign=campaign)

    total_visits = visits.count()
    opened_doors = visits.filter(opened_door=True).count()
    closed_doors = total_visits - opened_doors
    percent_opened = round((opened_doors / total_visits * 100), 1) if total_visits else 0

    reactions = visits.filter(opened_door=True).values('reaction').annotate(count=Count('id'))
    reaction_map = {r['reaction']: r['count'] for r in reactions if r['reaction']}
    positive = reaction_map.get('positive', 0)
    neutral = reaction_map.get('neutral', 0)
    negative = reaction_map.get('negative', 0)

    contacts = visits.filter(contact_name__isnull=False).exclude(contact_name='').count()
    percent_contacts = round((contacts / total_visits * 100), 1) if total_visits else 0

    house_stats = House.objects.filter(campaign=campaign).annotate(
        h_total=Count('visits'),
        h_opened=Count('visits', filter=Q(visits__opened_door=True)),
        h_positive=Count('visits', filter=Q(visits__reaction='positive')),
        h_neutral=Count('visits', filter=Q(visits__reaction='neutral')),
        h_negative=Count('visits', filter=Q(visits__reaction='negative')),
        h_contacts=Count('visits', filter=Q(visits__contact_name__isnull=False) & ~Q(visits__contact_name='')),
    ).values(
        'id', 'city', 'street', 'house_number',
        'h_total', 'h_opened', 'h_positive', 'h_neutral', 'h_negative', 'h_contacts'
    )

    house_stats_list = []
    for hs in house_stats:
        h_total = hs['h_total']
        h_opened = hs['h_opened']
        h_percent = round((h_opened / h_total * 100), 1) if h_total else 0
        house_stats_list.append({
            'house': {
                'id': hs['id'],
                'street': hs['street'],
                'house_number': hs['house_number'],
            },
            'total_visits': h_total,
            'opened_doors': h_opened,
            'percent_opened': h_percent,
            'positive': hs['h_positive'],
            'neutral': hs['h_neutral'],
            'negative': hs['h_negative'],
            'contacts': hs['h_contacts'],
        })

    return {
        'total_visits': total_visits,
        'opened_doors': opened_doors,
        'closed_doors': closed_doors,
        'percent_opened': percent_opened,
        'positive': positive,
        'neutral': neutral,
        'negative': negative,
        'contacts_collected': contacts,
        'percent_contacts': percent_contacts,
        'house_stats': house_stats_list,
    }
