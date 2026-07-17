# Бизнес-логика приложения (все операции с данными)
from django.db.models import Count
from .models import Campaign, House, ApartmentVisit


def create_campaign(name, owner):
    """Создаёт новую кампанию. Владелец автоматически становится участником."""
    campaign = Campaign.objects.create(name=name, owner=owner)
    campaign.participants.add(owner)
    return campaign


def add_house_to_campaign(campaign, city, street, house_number, entrances, apartments_per_entrance):
    """Добавляет дом в указанную кампанию."""
    return House.objects.create(
        campaign=campaign,
        city=city,
        street=street,
        house_number=house_number,
        entrances=entrances,
        apartments_per_entrance=apartments_per_entrance
    )


def record_visit(house, visitor, entrance, apartment_number, opened_door,
                 reaction=None, contact_name=None, contact_phone=None, comment=None):
    """Сохраняет запись об обходе одной квартиры."""
    return ApartmentVisit.objects.create(
        house=house,
        visitor=visitor,
        entrance=entrance,
        apartment_number=apartment_number,
        opened_door=opened_door,
        reaction=reaction,
        contact_name=contact_name,
        contact_phone=contact_phone,
        comment=comment
    )


def add_participant_to_campaign(campaign, username):
    """Добавляет пользователя в кампанию. Возвращает (успех, сообщение)."""
    from django.contrib.auth.models import User
    try:
        user_to_add = User.objects.get(username=username)
        if user_to_add in campaign.participants.all():
            return False, f'{username} уже является участником.'
        campaign.participants.add(user_to_add)
        return True, f'{username} добавлен в кампанию!'
    except User.DoesNotExist:
        return False, 'Пользователь не найден.'


def get_campaign_statistics(campaign):
    """
    Собирает статистику по кампании: открытия, реакции, контакты.
    Использует предзагрузку данных для скорости.
    """
    houses = campaign.houses.all().prefetch_related('visits')
    visits = ApartmentVisit.objects.filter(house__campaign=campaign)

    total_visits = visits.count()
    opened_doors = visits.filter(opened_door=True).count()
    closed_doors = total_visits - opened_doors
    percent_opened = round((opened_doors / total_visits * 100), 1) if total_visits else 0

    # Считаем реакции
    reactions = visits.filter(opened_door=True).values('reaction').annotate(count=Count('id'))
    reaction_map = {r['reaction']: r['count'] for r in reactions if r['reaction']}
    positive = reaction_map.get('positive', 0)
    neutral = reaction_map.get('neutral', 0)
    negative = reaction_map.get('negative', 0)

    # Считаем собранные контакты
    contacts = visits.filter(contact_name__isnull=False).exclude(contact_name='').count()
    percent_contacts = round((contacts / total_visits * 100), 1) if total_visits else 0

    # Статистика по каждому дому (используем уже загруженные визиты)
    house_stats = []
    for house in houses:
        hv = house.visits.all()
        h_total = len(hv)
        h_opened = sum(1 for v in hv if v.opened_door)
        h_percent = round((h_opened / h_total * 100), 1) if h_total else 0
        house_stats.append({
            'house': house,
            'total_visits': h_total,
            'opened_doors': h_opened,
            'percent_opened': h_percent,
            'positive': sum(1 for v in hv if v.reaction == 'positive'),
            'neutral': sum(1 for v in hv if v.reaction == 'neutral'),
            'negative': sum(1 for v in hv if v.reaction == 'negative'),
            'contacts': sum(1 for v in hv if v.contact_name),
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
        'house_stats': house_stats,
    }
