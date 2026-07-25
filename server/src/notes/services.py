from typing import Optional

from django.db.models import Q, QuerySet
from django.utils import timezone

from _sdk.exceptions import ResourceNotFoundException, ValidationException
from notes.models import Note, NoteFolder


def _soft_delete(instance) -> None:
    instance.deleted_at = timezone.now()
    instance.save(update_fields=["deleted_at", "updated_at"])


class NoteService:
    # ---- folders ----

    @staticmethod
    def list_folders(user) -> list[NoteFolder]:
        return list(NoteFolder.objects.filter(user=user).order_by("sort_order", "id"))

    @staticmethod
    def get_folder(user, folder_id: int) -> NoteFolder:
        folder = NoteFolder.objects.filter(user=user, id=folder_id).first()
        if not folder:
            raise ResourceNotFoundException(message="Folder not found")
        return folder

    @staticmethod
    def create_folder(
        user,
        *,
        name: str,
        color: str = "#7c3aed",
        parent_id: Optional[int] = None,
        sort_order: int = 0,
    ) -> NoteFolder:
        name = name.strip()
        if not name:
            raise ValidationException(message="Folder name is required")

        parent = None
        if parent_id is not None:
            parent = NoteService.get_folder(user, parent_id)

        return NoteFolder.objects.create(
            user=user,
            name=name,
            color=color or "#7c3aed",
            parent=parent,
            sort_order=sort_order,
        )

    @staticmethod
    def update_folder(user, folder_id: int, **fields) -> NoteFolder:
        folder = NoteService.get_folder(user, folder_id)

        if "name" in fields and fields["name"] is not None:
            name = fields["name"].strip()
            if not name:
                raise ValidationException(message="Folder name is required")
            folder.name = name

        if "color" in fields and fields["color"] is not None:
            folder.color = fields["color"] or "#7c3aed"

        if "sort_order" in fields and fields["sort_order"] is not None:
            folder.sort_order = fields["sort_order"]

        if "parent_id" in fields:
            parent_id = fields["parent_id"]
            if parent_id is None:
                folder.parent = None
            else:
                if parent_id == folder.id:
                    raise ValidationException(message="Folder cannot be its own parent")
                folder.parent = NoteService.get_folder(user, parent_id)

        folder.save()
        return folder

    @staticmethod
    def delete_folder(user, folder_id: int) -> None:
        folder = NoteService.get_folder(user, folder_id)
        # Keep notes; just detach them
        Note.objects.filter(user=user, folder=folder).update(folder=None)
        _soft_delete(folder)

    @staticmethod
    def serialize_folder(folder: NoteFolder) -> dict:
        return {
            "id": folder.id,
            "name": folder.name,
            "color": folder.color,
            "parent_id": folder.parent_id,
            "sort_order": folder.sort_order,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
        }

    # ---- notes ----

    @staticmethod
    def get_note(user, note_id: int) -> Note:
        note = Note.objects.filter(user=user, id=note_id).first()
        if not note:
            raise ResourceNotFoundException(message="Note not found")
        return note

    @staticmethod
    def list_notes(
        user,
        *,
        folder_id: Optional[int] = None,
        unfiled: bool = False,
        archived: str = "active",
        pinned_only: bool = False,
        q: Optional[str] = None,
    ) -> list[Note]:
        """
        archived: active | archived | all
        """
        qs: QuerySet[Note] = Note.objects.filter(user=user)

        if archived == "active":
            qs = qs.filter(is_archived=False)
        elif archived == "archived":
            qs = qs.filter(is_archived=True)
        elif archived != "all":
            raise ValidationException(
                message="archived must be one of: active, archived, all"
            )

        if pinned_only:
            qs = qs.filter(is_pinned=True)

        if unfiled:
            qs = qs.filter(folder__isnull=True)
        elif folder_id is not None:
            # Ensure folder belongs to user
            NoteService.get_folder(user, folder_id)
            qs = qs.filter(folder_id=folder_id)

        if q:
            query = q.strip()
            if query:
                qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query))

        return list(qs.order_by("-is_pinned", "sort_order", "-updated_at", "id"))

    @staticmethod
    def create_note(
        user,
        *,
        title: str,
        content: str = "",
        folder_id: Optional[int] = None,
        is_pinned: bool = False,
        sort_order: int = 0,
    ) -> Note:
        title = title.strip()
        if not title:
            raise ValidationException(message="Note title is required")

        folder = None
        if folder_id is not None:
            folder = NoteService.get_folder(user, folder_id)

        return Note.objects.create(
            user=user,
            title=title,
            content=content,
            folder=folder,
            is_pinned=is_pinned,
            sort_order=sort_order,
        )

    @staticmethod
    def update_note(user, note_id: int, **fields) -> Note:
        note = NoteService.get_note(user, note_id)

        if "title" in fields and fields["title"] is not None:
            title = fields["title"].strip()
            if not title:
                raise ValidationException(message="Note title is required")
            note.title = title

        if "content" in fields and fields["content"] is not None:
            note.content = fields["content"]

        if "is_pinned" in fields and fields["is_pinned"] is not None:
            note.is_pinned = fields["is_pinned"]

        if "is_archived" in fields and fields["is_archived"] is not None:
            note.is_archived = fields["is_archived"]

        if "sort_order" in fields and fields["sort_order"] is not None:
            note.sort_order = fields["sort_order"]

        if "folder_id" in fields:
            folder_id = fields["folder_id"]
            if folder_id is None:
                note.folder = None
            else:
                note.folder = NoteService.get_folder(user, folder_id)

        note.save()
        return note

    @staticmethod
    def pin_note(user, note_id: int, pinned: bool = True) -> Note:
        return NoteService.update_note(user, note_id, is_pinned=pinned)

    @staticmethod
    def archive_note(user, note_id: int, archived: bool = True) -> Note:
        return NoteService.update_note(user, note_id, is_archived=archived)

    @staticmethod
    def delete_note(user, note_id: int) -> None:
        note = NoteService.get_note(user, note_id)
        _soft_delete(note)

    @staticmethod
    def serialize_note(note: Note, *, include_content: bool = True) -> dict:
        data = {
            "id": note.id,
            "title": note.title,
            "folder_id": note.folder_id,
            "is_pinned": note.is_pinned,
            "is_archived": note.is_archived,
            "sort_order": note.sort_order,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
        }
        if include_content:
            data["content"] = note.content
        else:
            # Lightweight list preview
            preview = (note.content or "").strip().replace("\n", " ")
            data["preview"] = preview[:160]
        return data
