#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

import io
import os
import re
from typing import Union

import pyrogram
from pyrogram import raw
from pyrogram import types
from pyrogram import utils
from pyrogram.file_id import FileType


class EditMessageMedia:
    async def edit_message_media(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_id: int,
        media: "types.InputMedia",
        invert_media: bool = None,
        reply_markup: "types.InlineKeyboardMarkup" = None,
        file_name: str = None
    ) -> "types.Message":
        """Edit animation, audio, document, photo or video messages.

        If a message is a part of a message album, then it can be edited only to a photo or a video. Otherwise, the
        message type can be changed arbitrarily.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            message_id (``int``):
                Message identifier in the chat specified in chat_id.

            media (:obj:`~pyrogram.types.InputMedia`):
                One of the InputMedia objects describing an animation, audio, document, photo or video.

            invert_media (``bool``, *optional*):
                Invert media.

            reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup`, *optional*):
                An InlineKeyboardMarkup object.

            file_name (``str``, *optional*):
                File name of the media to be sent. Not applicable to photos.
                Defaults to file's path basename.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the edited message is returned.

        Example:
            .. code-block:: python

                from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaAudio

                # Replace the current media with a local photo
                await app.edit_message_media(chat_id, message_id,
                    InputMediaPhoto("new_photo.jpg"))

                # Replace the current media with a local video
                await app.edit_message_media(chat_id, message_id,
                    InputMediaVideo("new_video.mp4"))

                # Replace the current media with a local audio
                await app.edit_message_media(chat_id, message_id,
                    InputMediaAudio("new_audio.mp3"))
        """
        caption = media.caption
        parse_mode = media.parse_mode
        caption_entities = media.caption_entities

        message, entities = None, None

        if caption is not None:
            message, entities = (await utils.parse_text_entities(self, caption, parse_mode, caption_entities)).values()

        is_bytes_io = isinstance(media.media, io.BytesIO)
        is_uploaded_file = is_bytes_io or os.path.isfile(media.media)

        is_external_url = not is_uploaded_file and re.match("^https?://", media.media)

        if is_bytes_io and not hasattr(media.media, "name"):
            media.media.name = "media"

        if is_uploaded_file:
            filename_attribute = [
                raw.types.DocumentAttributeFilename(
                    file_name=file_name or (media.media.name if is_bytes_io else os.path.basename(media.media))
                )
            ]
        else:
            filename_attribute = []

        if isinstance(media, types.InputMediaPhoto):
            
            if is_uploaded_file:
                uploaded_media = await self.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await self.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedPhoto(
                            file=await self.save_file(media.media),
                            spoiler=media.has_spoiler
                        )
                    )
                )

                media = raw.types.InputMediaPhoto(
                    id=raw.types.InputPhoto(
                        id=uploaded_media.photo.id,
                        access_hash=uploaded_media.photo.access_hash,
                        file_reference=uploaded_media.photo.file_reference
                    ),
                    spoiler=media.has_spoiler
                )
            elif is_external_url:
                media = raw.types.InputMediaPhotoExternal(
                    url=media.media,
                    spoiler=media.has_spoiler
                )
            else:
                media = utils.get_input_media_from_file_id(media.media, FileType.PHOTO, has_spoiler=media.has_spoiler)
        elif isinstance(media, types.InputMediaVideo):
            
            coverfile = None
            start_timestamp = None
            # TODO: remove this duplicate code
            if media.start_timestamp:
                start_timestamp = media.start_timestamp
            if media.cover:
                cover = media.cover

                cover_is_bytes_io = isinstance(cover, io.BytesIO)
                cover_is_uploaded_file = cover_is_bytes_io or os.path.isfile(cover)
                cover_is_external_url = not cover_is_uploaded_file and re.match("^https?://", cover)

                if cover_is_bytes_io and not hasattr(cover, "name"):
                    cover.name = "cover.jpg"
                if cover_is_uploaded_file:
                    coverfile = await self.invoke(
                        raw.functions.messages.UploadMedia(
                            
                            peer=await self.resolve_peer(chat_id),
                            media=raw.types.InputMediaUploadedPhoto(
                                file=await self.save_file(cover)
                            )
                        )
                    )
                    coverfile = raw.types.InputPhoto(
                        id=coverfile.photo.id,
                        access_hash=coverfile.photo.access_hash,
                        file_reference=coverfile.photo.file_reference
                    )
                elif cover_is_external_url:
                    coverfile = await self.invoke(
                        raw.functions.messages.UploadMedia(
                            
                            peer=await self.resolve_peer(chat_id),
                            media=raw.types.InputMediaPhotoExternal(
                                url=cover
                            )
                        )
                    )
                    coverfile = raw.types.InputPhoto(
                        id=coverfile.photo.id,
                        access_hash=coverfile.photo.access_hash,
                        file_reference=coverfile.photo.file_reference
                    )
                else:
                    coverfile = (utils.get_input_media_from_file_id(cover, FileType.PHOTO)).id
            if is_uploaded_file:
                uploaded_media = await self.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await self.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedDocument(
                            mime_type=(None if is_bytes_io else self.guess_mime_type(media.media)) or "video/mp4",
                            thumb=await self.save_file(media.thumb),
                            spoiler=media.has_spoiler,
                            file=await self.save_file(media.media),
                            attributes=[
                                raw.types.DocumentAttributeVideo(
                                    supports_streaming=media.supports_streaming or None,
                                    duration=media.duration,
                                    w=media.width,
                                    h=media.height
                                ),
                            ] + filename_attribute,
                            nosound_video=not media.disable_content_type_detection,
                            force_file=media.disable_content_type_detection or None,
                        )
                    )
                )

                media = raw.types.InputMediaDocument(
                    id=raw.types.InputDocument(
                        id=uploaded_media.document.id,
                        access_hash=uploaded_media.document.access_hash,
                        file_reference=uploaded_media.document.file_reference
                    ),
                    spoiler=media.has_spoiler,
                    video_cover=coverfile,
                    video_timestamp=start_timestamp
                )
            elif is_external_url:
                media = raw.types.InputMediaDocumentExternal(
                    url=media.media,
                    spoiler=media.has_spoiler,
                    video_cover=coverfile,
                    video_timestamp=start_timestamp
                )
            else:
                media = utils.get_input_media_from_file_id(media.media, FileType.VIDEO, has_spoiler=media.has_spoiler)
                media.video_cover = coverfile
                media.video_timestamp = start_timestamp
        elif isinstance(media, types.InputMediaAudio):
            if is_uploaded_file:
                media = await self.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await self.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedDocument(
                            mime_type=(None if is_bytes_io else self.guess_mime_type(media.media)) or "audio/mpeg",
                            thumb=await self.save_file(media.thumb),
                            file=await self.save_file(media.media),
                            attributes=[
                                raw.types.DocumentAttributeAudio(
                                    duration=media.duration,
                                    performer=media.performer,
                                    title=media.title
                                ),
                            ] + filename_attribute,
                        )
                    )
                )

                media = raw.types.InputMediaDocument(
                    id=raw.types.InputDocument(
                        id=media.document.id,
                        access_hash=media.document.access_hash,
                        file_reference=media.document.file_reference
                    )
                )
            elif is_external_url:
                media = raw.types.InputMediaDocumentExternal(
                    url=media.media
                )
            else:
                media = utils.get_input_media_from_file_id(media.media, FileType.AUDIO)
        elif isinstance(media, types.InputMediaAnimation):
            
            if is_uploaded_file:
                uploaded_media = await self.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await self.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedDocument(
                            mime_type=(None if is_bytes_io else self.guess_mime_type(media.media)) or "video/mp4",
                            thumb=await self.save_file(media.thumb),
                            spoiler=media.has_spoiler,
                            file=await self.save_file(media.media),
                            attributes=[
                                raw.types.DocumentAttributeVideo(
                                    supports_streaming=True,
                                    duration=media.duration,
                                    w=media.width,
                                    h=media.height
                                ),
                                raw.types.DocumentAttributeAnimated(),
                            ] + filename_attribute,
                        )
                    )
                )

                media = raw.types.InputMediaDocument(
                    id=raw.types.InputDocument(
                        id=uploaded_media.document.id,
                        access_hash=uploaded_media.document.access_hash,
                        file_reference=uploaded_media.document.file_reference
                    ),
                    spoiler=media.has_spoiler
                )
            elif is_external_url:
                media = raw.types.InputMediaDocumentExternal(
                    url=media.media,
                    spoiler=media.has_spoiler
                )
            else:
                media = utils.get_input_media_from_file_id(media.media, FileType.ANIMATION, has_spoiler=media.has_spoiler)
        elif isinstance(media, types.InputMediaDocument):
            if is_uploaded_file:
                media = await self.invoke(
                    raw.functions.messages.UploadMedia(
                        peer=await self.resolve_peer(chat_id),
                        media=raw.types.InputMediaUploadedDocument(
                            mime_type=(None if is_bytes_io else self.guess_mime_type(media.media)) or "application/zip",
                            thumb=await self.save_file(media.thumb),
                            file=await self.save_file(media.media),
                            attributes=filename_attribute,
                            force_file=media.disable_content_type_detection
                        )
                    )
                )

                media = raw.types.InputMediaDocument(
                    id=raw.types.InputDocument(
                        id=media.document.id,
                        access_hash=media.document.access_hash,
                        file_reference=media.document.file_reference
                    )
                )
            elif is_external_url:
                media = raw.types.InputMediaDocumentExternal(
                    url=media.media
                )
            else:
                media = utils.get_input_media_from_file_id(media.media, FileType.DOCUMENT)

        rpc = raw.functions.messages.EditMessage(
            invert_media=invert_media,
            peer=await self.resolve_peer(chat_id),
            id=message_id,
            message=message,
            media=media,
            reply_markup=await reply_markup.write(self) if reply_markup else None,
            entities=entities,
        )
        r = await self.invoke(rpc)

        for i in r.updates:
            if isinstance(
                i,
                (
                    raw.types.UpdateEditMessage,
                    raw.types.UpdateEditChannelMessage,
                )
            ):
                return await types.Message._parse(
                    self, i.message,
                    {i.id: i for i in r.users},
                    {i.id: i for i in r.chats},
                )