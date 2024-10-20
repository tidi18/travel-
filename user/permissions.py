from django.http import HttpResponse


def check_user_blocked(profile):
    """
    Проверяет, заблокирован ли пользователь.
    Если заблокирован, возвращает HttpResponse с сообщением об ошибке.
    """
    if profile.is_blocked:
        return HttpResponse("Ваш аккаунт заблокирован. Вы не можете создавать посты.", status=403)
    return None


def check_user_can_create(profile):
    """
    Проверяет, может ли пользователь создавать посты.
    Если не может, возвращает HttpResponse с сообщением об ошибке.
    """
    if not profile.is_create:
        return HttpResponse("У вас нет прав на создание постов.", status=403)
    return None