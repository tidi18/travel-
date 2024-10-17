from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название страны')
    top_level_domain = models.CharField(max_length=255, blank=True, verbose_name='Топ-уровневый домен')
    alpha2_code = models.CharField(max_length=255, unique=True, verbose_name='Двухбуквенный код страны')
    alpha3_code = models.CharField(max_length=255, unique=True, verbose_name='Трехбуквенный код страны')
    calling_code = models.CharField(max_length=255, blank=True, verbose_name='Телефонный код')
    capital = models.CharField(max_length=255, blank=True, verbose_name='Столица')
    alt_spellings = models.TextField(blank=True, verbose_name='Альтернативные написания')
    region = models.CharField(max_length=255, blank=True, verbose_name='Регион')

    def __str__(self):
        return self.name
