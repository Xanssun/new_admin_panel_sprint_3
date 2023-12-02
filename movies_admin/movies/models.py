import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(_('Created'), blank=True, null=True)
    updated_at = models.DateTimeField(_('Modified'), blank=True,
                                      null=True, auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(_('ID'), primary_key=True,
                          default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_('Full Name'), max_length=255)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')


class Filmwork(UUIDMixin, TimeStampedMixin):
    MOVIE = 'movie'
    TV_SHOW = 'tv_show'

    TYPE_CHOICES = [
        (MOVIE, _('Movies')),
        (TV_SHOW, _('TV Shows')),
    ]

    title = models.TextField(_('title'), blank=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    creation_date = models.DateField(_('Premiere Date'), null=True)
    rating = models.FloatField(_('Rating'), null=True, blank=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])
    type = models.TextField(
        _('Type'),
        max_length=8,
        choices=TYPE_CHOICES,
        default=MOVIE
    )
    genres = models.ManyToManyField(Genre, through='GenreFilmwork')
    persons = models.ManyToManyField(Person, through='PersonFilmwork')

    def __str__(self):
        return self.title

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = _('Movies/TV Shows')
        verbose_name_plural = _('Movies and TV Shows')


class FilmRole(models.TextChoices):
    DIRECTOR = 'director', _('Director')
    WRITER = 'writer', _('Writer')
    ACTOR = 'actor', _('Actor')


class PersonFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.CharField(
        _('Role'),
        max_length=255,
        choices=FilmRole.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = db_table = "content\".\"person_film_work"
        verbose_name = _('Participation in Film')
        verbose_name_plural = _('Participation in Films')
        unique_together = ('film_work', 'person', 'role')


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        verbose_name = _('Movie Genre')
        verbose_name_plural = _('Movie Genres')
        unique_together = ('film_work', 'genre')
