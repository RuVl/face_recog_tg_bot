from core.database.methods.image import get_client_images
from core.database.methods.service import get_client_services
from core.database.methods.visit import get_visit_with_location, get_client_visits_with_location
from core.database.models import Visit, Service, Image


async def face_info_text(
        client_id: int | str,
        images: list[Image] = None,
        visits: list[Visit] = None,
        services: list[Service] = None
) -> str:
    """ Returns info about client """

    if images is None:
        images = await get_client_images(client_id)

    if visits is None:
        visits = await get_client_visits_with_location(client_id)

    if services is None:
        services = await get_client_services(client_id)

    result = f'*id в базе:* `{client_id}`\n\n'

    images_str = '\n'.join(
        f'`{image.url}`'
        for image in images
        if image.url is not None
    ).strip()

    if images_str != '' and images_str != '``':
        result += ('*Ссылки на фотографии:*\n'
                   f'{images_str}\n\n')

    # All contacts from visits
    contacts_str = '\n'.join(set(
        f'`{contact}`'
        for visit in visits
        if visit.contacts is not None
        for contact in visit.contacts.split('\n')
    )).strip()

    if contacts_str != '':
        result += ('*Контакты:*\n'
                   f'{contacts_str}\n\n')

    # Check if each visit has location
    for i in range(len(visits)):
        if visits[i].location is None:
            visits[i] = await get_visit_with_location(visits[i].id)

    # All names with dates and locations
    name_and_date_str = '\n'.join(
        f"{visit.name} \({visit.date:%H:%M %d\.%m\.%Y}\) \- {visit.location.address if visit.location is not None else 'отсутствует'}"
        for visit in visits
    ).strip()

    if name_and_date_str != '':
        result += ('*Имя и дата:*\n'
                   f'{name_and_date_str}\n\n')
    
    # All services
    services_list = [
        f'{service.title} \({service.date:%H:%M %d\.%m\.%Y}\)'
        for service in services
    ]

    services_str = '\n'.join(services_list).strip()

    if services_str != '':
        result += ('*Сервисы:*\n'
                   f'{services_str}\n\n')

    return result
