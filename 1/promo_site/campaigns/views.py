from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Campaign, House, Profile
from .forms import (
    UserRegistrationForm, CampaignForm, HouseForm,
    ApartmentVisitForm, AddParticipantForm
)
from .services import (
    create_campaign, add_house_to_campaign,
    record_visit, get_campaign_statistics
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
    # Гарантируем, что профиль существует (для старых пользователей)
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
            campaign = create_campaign(form.cleaned_data['name'], request.user)
            messages.success(request, 'Кампания создана!')
            return redirect('campaign_detail', campaign_id=campaign.id)
    else:
        form = CampaignForm()
    return render(request, 'campaigns/campaign_form.html', {'form': form})


@login_required
def campaign_detail(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    houses = campaign.houses.all()
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
                username = participant_form.cleaned_data['username']
                try:
                    user_to_add = User.objects.get(username=username)
                    campaign.participants.add(user_to_add)
                    messages.success(request, f'{username} добавлен в кампанию!')
                except User.DoesNotExist:
                    messages.error(request, 'Пользователь не найден.')
                return redirect('campaign_detail', campaign_id=campaign.id)

    return render(request, 'campaigns/campaign_detail.html', {
        'campaign': campaign,
        'houses': houses,
        'house_form': house_form,
        'participant_form': participant_form,
    })


@login_required
def house_detail(request, campaign_id, house_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    house = get_object_or_404(House, id=house_id, campaign=campaign)
    visits = house.visits.order_by('-visited_at')

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
    campaign = get_object_or_404(Campaign, id=campaign_id)
    stats = get_campaign_statistics(campaign)
    stats['campaign'] = campaign
    return render(request, 'campaigns/statistics.html', stats)