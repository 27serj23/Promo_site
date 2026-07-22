# Представления: принимают запросы, вызывают сервисы, возвращают страницы
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Profile
from .forms import (
    UserRegistrationForm, CampaignForm, HouseForm,
    ApartmentVisitForm, AddParticipantForm
)
from .services import (
    create_campaign, add_house_to_campaign, record_visit,
    get_campaign_statistics, add_participant_to_campaign,
    get_campaign_for_user, get_campaign_detail_data,
    get_house_with_visits, ServiceError
)


def index(request):
    return render(request, 'campaigns/index.html')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'campaigns/register.html', {'form': form})


@login_required
def profile(request):
    campaigns = request.user.campaigns.all()
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'phone': ''})
    return render(request, 'campaigns/profile.html', {
        'campaigns': campaigns,
        'profile': profile,
    })


@login_required
def create_campaign_view(request):
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            try:
                campaign = create_campaign(form.cleaned_data['name'], request.user)
                messages.success(request, 'Кампания создана!')
                return redirect('campaign_detail', campaign_id=campaign.id)
            except ServiceError as e:
                messages.error(request, str(e))
    else:
        form = CampaignForm()
    return render(request, 'campaigns/campaign_form.html', {'form': form})


@login_required
def campaign_detail(request, campaign_id):
    try:
        campaign = get_campaign_for_user(campaign_id, request.user)
    except PermissionError:
        messages.error(request, 'У вас нет доступа к этой кампании.')
        return redirect('profile')

    data = get_campaign_detail_data(campaign)
    house_form = HouseForm()
    participant_form = AddParticipantForm()

    if request.method == 'POST':
        if 'add_house' in request.POST:
            house_form = HouseForm(request.POST)
            if house_form.is_valid():
                try:
                    add_house_to_campaign(campaign, **house_form.cleaned_data)
                    messages.success(request, 'Дом добавлен!')
                except ServiceError as e:
                    messages.error(request, str(e))
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
        'campaign': data['campaign'],
        'houses': data['houses'],
        'house_form': house_form,
        'participant_form': participant_form,
    })


@login_required
def house_detail(request, campaign_id, house_id):
    try:
        campaign = get_campaign_for_user(campaign_id, request.user)
        house, visits = get_house_with_visits(
            campaign, house_id,
            page_number=request.GET.get('page', 1)
        )
    except PermissionError:
        messages.error(request, 'У вас нет доступа к этому дому.')
        return redirect('profile')

    if request.method == 'POST':
        form = ApartmentVisitForm(request.POST)
        if form.is_valid():
            try:
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
            except ServiceError as e:
                messages.error(request, str(e))
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
    try:
        campaign = get_campaign_for_user(campaign_id, request.user)
        stats = get_campaign_statistics(campaign)
        stats['campaign'] = campaign
    except PermissionError:
        messages.error(request, 'У вас нет доступа к этой статистике.')
        return redirect('profile')
    return render(request, 'campaigns/statistics.html', stats)
