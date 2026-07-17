# Тесты для сервисного слоя
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Campaign, House, ApartmentVisit
from .services import create_campaign, add_house_to_campaign, record_visit


class CampaignTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'test123')

    def test_create_campaign(self):
        """Проверяем, что кампания создаётся и владелец становится участником."""
        campaign = create_campaign('Тестовая кампания', self.user)
        self.assertEqual(campaign.name, 'Тестовая кампания')
        self.assertEqual(campaign.owner, self.user)
        self.assertIn(self.user, campaign.participants.all())

    def test_add_house(self):
        """Проверяем правильный подсчёт квартир в доме."""
        campaign = create_campaign('Кампания', self.user)
        house = add_house_to_campaign(campaign, 'Москва', 'Тверская', '10', 3, 4)
        self.assertEqual(house.total_apartments, 12)

    def test_record_visit(self):
        """Проверяем, что обход сохраняется с правильными данными."""
        campaign = create_campaign('Кампания', self.user)
        house = add_house_to_campaign(campaign, 'Москва', 'Тверская', '10', 1, 2)
        visit = record_visit(house, self.user, 1, 1, True, 'positive', 'Иван', '+7999', 'Комментарий')
        self.assertTrue(visit.opened_door)
        self.assertEqual(visit.reaction, 'positive')

    def test_statistics(self):
        """Проверяем, что статистика считается корректно."""
        from .services import get_campaign_statistics
        campaign = create_campaign('Статистика', self.user)
        house = add_house_to_campaign(campaign, 'Москва', 'Ленина', '1', 1, 2)
        record_visit(house, self.user, 1, 1, True, 'positive')
        record_visit(house, self.user, 1, 2, False)
        stats = get_campaign_statistics(campaign)
        self.assertEqual(stats['total_visits'], 2)
        self.assertEqual(stats['opened_doors'], 1)
        self.assertEqual(stats['positive'], 1)
