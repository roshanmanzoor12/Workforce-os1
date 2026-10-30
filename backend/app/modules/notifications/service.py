from __future__ import annotations



import uuid



from sqlalchemy.ext.asyncio import (

    AsyncSession,

)



from app.core.exceptions import (

    ValidationError,

)

from app.modules.notifications.models import (

    NOTIFICATION_PRIORITIES,

    Notification,

)

from app.modules.notifications.realtime import (

    NotificationRealtimePublisher,

    get_notification_realtime_publisher,

)

from app.modules.notifications.repository import (

    NotificationRepository,

)

from app.modules.notifications.schemas import (

    NotificationCreate,

    NotificationListResponse,

    NotificationMarkAllReadResponse,

    NotificationMutationResponse,

    NotificationPreferenceResponse,

    NotificationPreferenceUpdate,

    NotificationRealtimeEvent,

    NotificationResponse,

    NotificationUnreadCountResponse,

)





class NotificationNotFoundError(

    LookupError

):

    pass





class NotificationService:

    def __init__(

        self,

        session: AsyncSession,

        *,

        workspace_id: uuid.UUID,

        publisher: (

            NotificationRealtimePublisher

            | None

        ) = None,

    ) -> None:

        self.session = session



        self.workspace_id = (

            workspace_id

        )



        self.repository = (

            NotificationRepository(

                session

            )

        )



        self.publisher = (

            publisher

            or (

                get_notification_realtime_publisher()

            )

        )



    # =====================================================

    # SERIALIZATION

    # =====================================================



    @staticmethod

    def _response(

        notification: Notification,

    ) -> NotificationResponse:

        return (

            NotificationResponse

            .model_validate(

                notification

            )

        )



    # =====================================================

    # CREATE — INTERNAL DOMAIN API

    # =====================================================



    async def create(

        self,

        payload: NotificationCreate,

    ) -> NotificationResponse:

        priority = (

            payload.priority

            .strip()

            .lower()

        )



        if (

            priority

            not in NOTIFICATION_PRIORITIES

        ):

            raise ValidationError(

                "Invalid notification priority."

            )



        preference = await (

            self.repository

            .get_or_create_preferences(

                user_id=(

                    payload

                    .recipient_user_id

                )

            )

        )



        muted_types = set(

            preference.muted_types

            or []

        )



        # Muting one notification type prevents new

        # in-app rows for that type.

        if (

            not preference.in_app_enabled

            or payload.notification_type

            in muted_types

        ):

            raise ValidationError(

                "Recipient has disabled this "

                "notification type."

            )



        notification = Notification(

            recipient_user_id=(

                payload.recipient_user_id

            ),

            notification_type=(

                payload.notification_type

                .strip()

            ),

            title=payload.title.strip(),

            body=payload.body,

            priority=priority,

            entity_type=(

                payload.entity_type

            ),

            entity_id=(

                payload.entity_id

            ),

            action_url=(

                payload.action_url

            ),

            payload=dict(

                payload.payload

            ),

        )



        notification = await (

            self.repository.create(

                notification

            )

        )



        await self.session.commit()



        response = self._response(

            notification

        )



        unread_count = await (

            self.repository.unread_count(

                recipient_user_id=(

                    payload

                    .recipient_user_id

                )

            )

        )



        await self.publisher.publish(

            NotificationRealtimeEvent(

                event="notification.created",

                workspace_id=(

                    self.workspace_id

                ),

                recipient_user_id=(

                    payload

                    .recipient_user_id

                ),

                notification=response,

                unread_count=(

                    unread_count

                ),

            )

        )



        return response



    # =====================================================

    # LIST

    # =====================================================



    async def list_for_user(

        self,

        *,

        user_id: uuid.UUID,

        unread_only: bool,

        notification_type: (

            str | None

        ),

        limit: int,

        offset: int,

    ) -> NotificationListResponse:

        (

            items,

            total,

        ) = await (

            self.repository

            .list_for_recipient(

                recipient_user_id=(

                    user_id

                ),

                unread_only=unread_only,

                notification_type=(

                    notification_type

                ),

                limit=limit,

                offset=offset,

            )

        )



        unread_count = await (

            self.repository.unread_count(

                recipient_user_id=(

                    user_id

                )

            )

        )



        return NotificationListResponse(

            items=[

                self._response(

                    item

                )

                for item in items

            ],

            total=total,

            unread_count=(

                unread_count

            ),

            limit=limit,

            offset=offset,

        )



    # =====================================================

    # UNREAD COUNT

    # =====================================================



    async def unread_count(

        self,

        *,

        user_id: uuid.UUID,

    ) -> NotificationUnreadCountResponse:

        count = await (

            self.repository.unread_count(

                recipient_user_id=(

                    user_id

                )

            )

        )



        return (

            NotificationUnreadCountResponse(

                unread_count=count

            )

        )



    # =====================================================

    # MARK READ

    # =====================================================



    async def mark_read(

        self,

        *,

        notification_id: uuid.UUID,

        user_id: uuid.UUID,

    ) -> NotificationMutationResponse:

        notification = await (

            self.repository

            .get_for_recipient(

                notification_id=(

                    notification_id

                ),

                recipient_user_id=(

                    user_id

                ),

            )

        )



        if notification is None:

            raise NotificationNotFoundError(

                "Notification was not found."

            )



        notification = await (

            self.repository.mark_read(

                notification=(

                    notification

                )

            )

        )



        await self.session.commit()



        unread_count = await (

            self.repository.unread_count(

                recipient_user_id=(

                    user_id

                )

            )

        )



        await self.publisher.publish(

            NotificationRealtimeEvent(

                event="notification.read",

                workspace_id=(

                    self.workspace_id

                ),

                recipient_user_id=(

                    user_id

                ),

                notification=(

                    self._response(

                        notification

                    )

                ),

                unread_count=(

                    unread_count

                ),

            )

        )



        return (

            NotificationMutationResponse(

                id=notification.id,

                read_at=(

                    notification.read_at

                ),

            )

        )



    # =====================================================

    # MARK UNREAD

    # =====================================================



    async def mark_unread(

        self,

        *,

        notification_id: uuid.UUID,

        user_id: uuid.UUID,

    ) -> NotificationMutationResponse:

        notification = await (

            self.repository

            .get_for_recipient(

                notification_id=(

                    notification_id

                ),

                recipient_user_id=(

                    user_id

                ),

            )

        )



        if notification is None:

            raise NotificationNotFoundError(

                "Notification was not found."

            )



        notification = await (

            self.repository.mark_unread(

                notification=(

                    notification

                )

            )

        )



        await self.session.commit()



        unread_count = await (

            self.repository.unread_count(

                recipient_user_id=(

                    user_id

                )

            )

        )



        await self.publisher.publish(

            NotificationRealtimeEvent(

                event=(

                    "notification.unread"

                ),

                workspace_id=(

                    self.workspace_id

                ),

                recipient_user_id=(

                    user_id

                ),

                notification=(

                    self._response(

                        notification

                    )

                ),

                unread_count=(

                    unread_count

                ),

            )

        )



        return (

            NotificationMutationResponse(

                id=notification.id,

                read_at=(

                    notification.read_at

                ),

            )

        )



    # =====================================================

    # MARK ALL READ

    # =====================================================



    async def mark_all_read(

        self,

        *,

        user_id: uuid.UUID,

    ) -> NotificationMarkAllReadResponse:

        updated_count = await (

            self.repository.mark_all_read(

                recipient_user_id=(

                    user_id

                )

            )

        )



        await self.session.commit()



        await self.publisher.publish(

            NotificationRealtimeEvent(

                event=(

                    "notification.all_read"

                ),

                workspace_id=(

                    self.workspace_id

                ),

                recipient_user_id=(

                    user_id

                ),

                unread_count=0,

            )

        )



        return (

            NotificationMarkAllReadResponse(

                updated_count=(

                    updated_count

                )

            )

        )



    # =====================================================

    # PHASE 22 PUBLIC COMPATIBILITY API

    async def list_notifications(self, **kwargs):
        return await self.list_for_user(**kwargs)

    async def create_notification(self, payload: NotificationCreate) -> NotificationResponse:
        return await self.create(payload)

    async def delete_notification(self, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationMutationResponse:
        notification = await self.repository.get_for_user(notification_id=notification_id, user_id=user_id)
        if notification is None:
            raise NotificationNotFoundError("Notification was not found.")
        await self.repository.delete_for_user(notification_id=notification_id, user_id=user_id)
        await self.session.commit()
        return NotificationMutationResponse(id=notification.id, read_at=notification.read_at)

    # PREFERENCES

    # =====================================================



    async def preferences(

        self,

        *,

        user_id: uuid.UUID,

    ) -> NotificationPreferenceResponse:

        preference = await (

            self.repository

            .get_or_create_preferences(

                user_id=user_id

            )

        )



        await self.session.commit()



        return (

            NotificationPreferenceResponse

            .model_validate(

                preference

            )

        )



    async def update_preferences(

        self,

        *,

        user_id: uuid.UUID,

        payload: (

            NotificationPreferenceUpdate

        ),

    ) -> NotificationPreferenceResponse:

        preference = await (

            self.repository

            .get_or_create_preferences(

                user_id=user_id

            )

        )



        updates = (

            payload.model_dump(

                exclude_none=True

            )

        )



        if "muted_types" in updates:

            updates[

                "muted_types"

            ] = sorted(

                {

                    item.strip()

                    for item

                    in updates[

                        "muted_types"

                    ]

                    if item.strip()

                }

            )



        for (

            field,

            value,

        ) in updates.items():

            setattr(

                preference,

                field,

                value,

            )



        await self.session.commit()



        await self.session.refresh(

            preference

        )



        return (

            NotificationPreferenceResponse

            .model_validate(

                preference

            )

        )





__all__ = [

    "NotificationNotFoundError",

    "NotificationService",

]