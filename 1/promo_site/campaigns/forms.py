from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Campaign, House, ApartmentVisit, Profile


class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        label='Логин'
    )
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    email = forms.EmailField(required=True, label='Электронная почта')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            Profile.objects.create(user=user, phone=self.cleaned_data['phone'])
        return user


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['name']
        labels = {'name': 'Название кампании'}


class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['city', 'street', 'house_number', 'entrances', 'apartments_per_entrance']
        labels = {
            'city': 'Город',
            'street': 'Улица',
            'house_number': 'Номер дома',
            'entrances': 'Количество подъездов',
            'apartments_per_entrance': 'Квартир в подъезде',
        }


class ApartmentVisitForm(forms.ModelForm):
    class Meta:
        model = ApartmentVisit
        fields = ['entrance', 'apartment_number', 'opened_door', 'reaction',
                  'contact_name', 'contact_phone', 'comment']
        labels = {
            'entrance': 'Подъезд',
            'apartment_number': 'Номер квартиры',
            'opened_door': 'Дверь открыли',
            'reaction': 'Реакция',
            'contact_name': 'Имя контакта',
            'contact_phone': 'Телефон контакта',
            'comment': 'Комментарий',
        }
        widgets = {'comment': forms.Textarea(attrs={'rows': 2})}


class AddParticipantForm(forms.Form):
    username = forms.CharField(max_length=150, label='Имя пользователя (логин)')