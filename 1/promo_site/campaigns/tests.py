# Тесты для сервисного слоя
from django.test import TestCase
from django.contrib.auth.models import User
from .services import (
    create_campaign, add_house_to_campaign,
    record_visit, get_campaign_statistics,
    get_campaign_for_user, ServiceError
)


class CampaignCreationTests(TestCase):
    """Тесты создания кампаний."""

    def setUp(self):
        self.campaign_owner = User.objects.create_user('owner', 'owner@test.com', 'owner123')

    def test_create_campaign_success(self):
        """Кампания создаётся, владелец становится участником."""
        campaign = create_campaign('Тестовая кампания', self.campaign_owner)
        self.assertEqual(campaign.name, 'Тестовая кампания')
        self.assertEqual(campaign.owner, self.campaign_owner)
        self.assertIn(self.campaign_owner, campaign.participants.all())

    def test_create_campaign_empty_name(self):
        """Пустое название вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            create_campaign('', self.campaign_owner)

    def test_create_campaign_whitespace_name(self):
        """Название из пробелов вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            create_campaign('   ', self.campaign_owner)

    def test_create_campaign_no_owner(self):
        """Отсутствие владельца вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            create_campaign('Кампания', None)


class HouseAdditionTests(TestCase):
    """Тесты добавления домов."""

    def setUp(self):
        self.campaign_owner = User.objects.create_user('owner', 'owner@test.com', 'owner123')
        self.campaign = create_campaign('Тестовая кампания', self.campaign_owner)

    def test_add_house_success(self):
        """Дом корректно добавляется, квартиры считаются правильно."""
        house = add_house_to_campaign(self.campaign, 'Москва', 'Тверская', '10', 3, 4)
        self.assertEqual(house.city, 'Москва')
        self.assertEqual(house.total_apartments, 12)

    def test_add_house_zero_entrances(self):
        """Ноль подъездов вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            add_house_to_campaign(self.campaign, 'Москва', 'Тверская', '10', 0, 4)

    def test_add_house_zero_apartments(self):
        """Ноль квартир в подъезде вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            add_house_to_campaign(self.campaign, 'Москва', 'Тверская', '10', 1, 0)

    def test_add_house_negative_values(self):
        """Отрицательные значения вызывают ServiceError."""
        with self.assertRaises(ServiceError):
            add_house_to_campaign(self.campaign, 'Москва', 'Тверская', '10', -1, 4)
        with self.assertRaises(ServiceError):
            add_house_to_campaign(self.campaign, 'Москва', 'Тверская', '10', 1, -1)

    def test_add_house_empty_city(self):
        """Пустой город вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            add_house_to_campaign(self.campaign, '', 'Тверская', '10', 1, 4)

    def test_add_house_no_campaign(self):
        """Отсутствие кампании вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            add_house_to_campaign(None, 'Москва', 'Тверская', '10', 1, 4)


class VisitRecordingTests(TestCase):
    """Тесты записи обходов."""

    def setUp(self):
        self.visitor = User.objects.create_user('visitor', 'visitor@test.com', 'visitor123')
        self.campaign = create_campaign('Кампания', self.visitor)
        self.house = add_house_to_campaign(self.campaign, 'Москва', 'Тверская', '10', 1, 5)

    def test_record_visit_success(self):
        """Обход сохраняется с правильными данными."""
        visit = record_visit(self.house, self.visitor, 1, 1, True, 'positive', 'Иван', '+7999', 'Комментарий')
        self.assertTrue(visit.opened_door)
        self.assertEqual(visit.reaction, 'positive')
        self.assertEqual(visit.contact_name, 'Иван')

    def test_record_visit_door_not_opened(self):
        """Если дверь не открыли, реакция не обязательна."""
        visit = record_visit(self.house, self.visitor, 1, 2, False)
        self.assertFalse(visit.opened_door)
        self.assertIsNone(visit.reaction)

    def test_record_visit_no_house(self):
        """Отсутствие дома вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            record_visit(None, self.visitor, 1, 1, True)

    def test_record_visit_negative_entrance(self):
        """Отрицательный подъезд вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            record_visit(self.house, self.visitor, -1, 1, True)

    def test_record_visit_zero_apartment(self):
        """Нулевая квартира вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            record_visit(self.house, self.visitor, 1, 0, True)

    def test_record_visit_contact_name_as_number(self):
        """Если вместо имени передано число, оно не вызовет краша."""
        visit = record_visit(self.house, self.visitor, 1, 1, True, None, 12345, '+7999', None)
        self.assertIsNone(visit.contact_name)  # число не должно сохраниться как имя


class AccessControlTests(TestCase):
    """Тесты контроля доступа."""

    def setUp(self):
        self.campaign_owner = User.objects.create_user('owner', 'owner@test.com', 'owner123')
        self.another_user = User.objects.create_user('other', 'other@test.com', 'other123')
        self.campaign = create_campaign('Приватная кампания', self.campaign_owner)

    def test_owner_has_access(self):
        """Владелец имеет доступ к своей кампании."""
        result = get_campaign_for_user(self.campaign.id, self.campaign_owner)
        self.assertEqual(result, self.campaign)

    def test_another_user_denied(self):
        """Чужой пользователь не может получить доступ."""
        with self.assertRaises(PermissionError):
            get_campaign_for_user(self.campaign.id, self.another_user)

    def test_participant_has_access(self):
        """Добавленный участник получает доступ."""
        self.campaign.participants.add(self.another_user)
        result = get_campaign_for_user(self.campaign.id, self.another_user)
        self.assertEqual(result, self.campaign)

    def test_unauthenticated_user_denied(self):
        """Неаутентифицированный пользователь не имеет доступа."""
        with self.assertRaises(PermissionError):
            get_campaign_for_user(self.campaign.id, None)


class StatisticsTests(TestCase):
    """Тесты статистики."""

    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'test123')
        self.campaign = create_campaign('Статистика', self.user)
        self.house1 = add_house_to_campaign(self.campaign, 'Москва', 'Ленина', '1', 1, 3)
        self.house2 = add_house_to_campaign(self.campaign, 'Москва', 'Мира', '2', 1, 2)

    def test_statistics_empty_campaign(self):
        """Пустая кампания (без обходов) возвращает нули."""
        stats = get_campaign_statistics(self.campaign)
        self.assertEqual(stats['total_visits'], 0)
        self.assertEqual(stats['opened_doors'], 0)
        self.assertEqual(stats['positive'], 0)

    def test_statistics_with_visits(self):
        """Статистика корректно считает обходы и реакции."""
        # Дом 1: два обхода
        record_visit(self.house1, self.user, 1, 1, True, 'positive')
        record_visit(self.house1, self.user, 1, 2, False)

        # Дом 2: один обход
        record_visit(self.house2, self.user, 1, 1, True, 'negative')

        stats = get_campaign_statistics(self.campaign)
        self.assertEqual(stats['total_visits'], 3)
        self.assertEqual(stats['opened_doors'], 2)
        self.assertEqual(stats['positive'], 1)
        self.assertEqual(stats['negative'], 1)
        self.assertEqual(len(stats['house_stats']), 2)

    def test_statistics_with_contacts(self):
        """Статистика считает собранные контакты."""
        record_visit(self.house1, self.user, 1, 1, True, 'positive', 'Иван', '+7999')
        record_visit(self.house1, self.user, 1, 2, True, 'neutral', 'Мария', '+7888')

        stats = get_campaign_statistics(self.campaign)
        self.assertEqual(stats['contacts_collected'], 2)
        # 2 контакта из 2 визитов = 100%
        self.assertEqual(stats['percent_contacts'], 100.0)

    def test_statistics_percent_opened(self):
        """Процент открытых дверей считается верно."""
        record_visit(self.house1, self.user, 1, 1, True)
        record_visit(self.house1, self.user, 1, 2, False)
        record_visit(self.house1, self.user, 1, 3, True)

        stats = get_campaign_statistics(self.campaign)
        # 2 открытых из 3 = 66.7%
        self.assertEqual(stats['percent_opened'], 66.7)

    def test_statistics_division_by_zero_safe(self):
        """Статистика не падает при делении на ноль."""
        stats = get_campaign_statistics(self.campaign)
        self.assertEqual(stats['percent_opened'], 0)
        self.assertEqual(stats['percent_contacts'], 0)
        self.assertIsInstance(stats['house_stats'], list)


class EdgeCaseTests(TestCase):
    """Тесты граничных случаев."""

    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'test123')

    def test_statistics_none_campaign(self):
        """None вместо кампании вызывает ServiceError."""
        with self.assertRaises(ServiceError):
            get_campaign_statistics(None)
