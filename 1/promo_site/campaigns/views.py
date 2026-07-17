# Представления: принимают запросы, вызывают сервисы, возвращают страницы
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404

from .models import Campaign, House, Profile
from .forms import (
    UserRegistrationForm, CampaignForm, HouseForm,
    ApartmentVisitForm, AddParticipantForm
)
from .services import (
    create_campaign, add_house_to_campaign,
    record_visit, get_campaign_statistics, add_participant_to_campaign
)


def index(request):
    """Главная страница."""
    return render(request, 'campaigns/index.html')


def register(request):
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)          # сразу входим после регистрации
            messages.success(request, 'Регистрация успешна!')
            return redirect('profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'campaigns/register.html', {'form': form})


@login_required
def profile(request):
    """Личный кабинет: данные профиля и список кампаний."""
    campaigns = request.user.campaigns.all()
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'phone': ''})
    return render(request, 'campaigns/profile.html', {
        'campaigns': campaigns,
        'profile': profile,
    })


@login_required
def create_campaign_view(request):
    """Создание новой кампании."""
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = create_campaign(form.cleaned_data['name'], request.user)
            messages.success(request, 'Кампания создана!')
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm()
    return render(request, 'campaigns/campaign_form.html', {'form': form})


def _get_campaign_with_access_check(campaign_id, user):
    """
    Получает кампанию и проверяет, что пользователь — владелец или участник.
    Если прав нет — показывает 404.
    """
    campaign = get_object_or_404(
        Campaign.objects.prefetch_related('participants', 'houses__visits'),
        id=campaign_id
    )
    if user != campaign.owner and not campaign.participants.filter(id=user.id).exists():
        raise Http404('Кампания не найдена')
    return campaign


@login_required
def campaign_detail(request, campaign_id):
    """Страница кампании: дома, участники, формы добавления."""
    campaign = _get_campaign_with_access_check(campaign_id, request.user)
    house_form = HouseForm()
    participant_form = AddParticipantForm()

    if request.method == 'POST':
        if 'add_house' in request.POST:
            house_form = HouseForm(request.POST)
            if house_form.is_valid():
                add_house_to_campaign(campaign, **house_form.cleaned_data)
                messages.success(request, 'Дом добавлен!')
                return redirect('campaign_detail', campaign_id=campaign.id)
        elif 'add_participant' in request.POST:
            participant_form = AddParticipantForm(request.POST)
            if participant_form.is_valid():
                success, msg = add_participant_to_campaign(
                    campaign, participant_form.cleaned_data['username']
                )
                if success:
                    messages.success(request, msg)
                else:
                    messages.error(request, msg)
                return redirect('campaign_detail', campaign_id=campaign.id)

    return render(request, 'campaigns/campaign_detail.html', {
        'campaign': campaign,
        'houses': campaign.houses.all(),
        'house_form': house_form,
        'participant_form': participant_form,
    })


@login_required
def house_detail(request, campaign_id, house_id):
    """Страница дома: все обходы (с пагинацией) и форма нового обхода."""
    campaign = _get_campaign_with_access_check(campaign_id, request.user)
    house = get_object_or_404(House, id=house_id, campaign=campaign)
    visits_list = house.visits.order_by('-visited_at')

    # Пагинация: по 10 обходов на странице
    paginator = Paginator(visits_list, 10)
    page_number = request.GET.get('page')
    visits = paginator.get_page(page_number)

    if request.method == 'POST':
        form = ApartmentVisitForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            record_visit(
                house=house,
                visitor=request.user,
                entrance=data['entrance'],
                apartment_number=data['apartment_number'],
                opened_door=data['opened_door'],
                reaction=data.get('reaction'),
                contact_name=data.get('contact_name'),
                contact_phone=data.get('contact_phone'),
                comment=data.get('comment')
            )
            messages.success(request, 'Обход зафиксирован!')
            return redirect('house_detail', campaign_id=campaign.id, house_id=house.id)
    else:
        form = ApartmentVisitForm()

    return render(request, 'campaigns/house_detail.html', {
        'campaign': campaign,
        'house': house,
        'visits': visits,
        'visit_form': form,
    })


@login_required
def campaign_statistics(request, campaign_id):
    """Статистика по кампании."""
    campaign = _get_campaign_with_access_check(campaign_id, request.user)
    stats = get_campaign_statistics(campaign)
    stats['campaign'] = campaign
    return render(request, 'campaigns/statistics.html', stats)
