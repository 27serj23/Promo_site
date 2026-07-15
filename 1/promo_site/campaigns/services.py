from django.db.models import Count
from .models import Campaign, House, ApartmentVisit


def create_campaign(name, owner):
    campaign = Campaign.objects.create(name=name, owner=owner)
    campaign.participants.add(owner)
    return campaign


def add_house_to_campaign(campaign, city, street, house_number, entrances, apartments_per_entrance):
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


def get_campaign_statistics(campaign):
    houses = campaign.houses.all()
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

    house_stats = []
    for house in houses:
        hv = house.visits.all()
        h_total = hv.count()
        h_opened = hv.filter(opened_door=True).count()
        h_percent = round((h_opened / h_total * 100), 1) if h_total else 0
        house_stats.append({
            'house': house,
            'total_visits': h_total,
            'opened_doors': h_opened,
            'percent_opened': h_percent,
            'positive': hv.filter(reaction='positive').count(),
            'neutral': hv.filter(reaction='neutral').count(),
            'negative': hv.filter(reaction='negative').count(),
            'contacts': hv.filter(contact_name__isnull=False).exclude(contact_name='').count(),
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