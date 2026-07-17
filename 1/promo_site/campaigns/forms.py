# Формы для ввода данных
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Campaign, House, ApartmentVisit, Profile


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации нового пользователя."""
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def save(self, commit=True):
        """Сохраняет пользователя и создаёт профиль с телефоном."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            Profile.objects.create(user=user, phone=self.cleaned_data['phone'])
        return user


class CampaignForm(forms.ModelForm):
    """Форма создания/редактирования кампании."""
    class Meta:
        model = Campaign
        fields = ['name']


class HouseForm(forms.ModelForm):
    """Форма добавления дома."""
    class Meta:
        model = House
        fields = ['city', 'street', 'house_number', 'entrances', 'apartments_per_entrance']


class ApartmentVisitForm(forms.ModelForm):
    """Форма фиксации обхода квартиры."""
    class Meta:
        model = ApartmentVisit
        fields = ['entrance', 'apartment_number', 'opened_door', 'reaction',
                  'contact_name', 'contact_phone', 'comment']
        widgets = {'comment': forms.Textarea(attrs={'rows': 2})}


class AddParticipantForm(forms.Form):
    """Форма для добавления участника в кампанию по логину."""
    username = forms.CharField(max_length=150, label='Имя пользователя (логин)')
