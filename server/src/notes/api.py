from typing import List, Optional

from ninja import Router

from _sdk.decorators import require_auth
from notes.schemas import (
    FolderCreateSchema,
    FolderResponseSchema,
    FolderUpdateSchema,
    NoteCreateSchema,
    NoteListItemSchema,
    NoteResponseSchema,
    NoteUpdateSchema,
)
from notes.services import NoteService

notes_router = Router(tags=["Notes"])


# ---- folders (register before /{note_id}) ----

@notes_router.get("/folders", response={200: List[FolderResponseSchema]})
@require_auth
def list_folders(request):
    folders = NoteService.list_folders(request.auth_user)
    return [NoteService.serialize_folder(folder) for folder in folders]


@notes_router.post("/folders", response={200: FolderResponseSchema})
@require_auth
def create_folder(request, payload: FolderCreateSchema):
    folder = NoteService.create_folder(
        request.auth_user,
        **payload.model_dump(),
    )
    return NoteService.serialize_folder(folder)


@notes_router.patch("/folders/{folder_id}", response={200: FolderResponseSchema})
@require_auth
def update_folder(request, folder_id: int, payload: FolderUpdateSchema):
    folder = NoteService.update_folder(
        request.auth_user,
        folder_id,
        **payload.model_dump(exclude_unset=True),
    )
    return NoteService.serialize_folder(folder)


@notes_router.delete("/folders/{folder_id}", response={200: dict})
@require_auth
def delete_folder(request, folder_id: int):
    NoteService.delete_folder(request.auth_user, folder_id)
    return {"message": "Folder deleted"}


# ---- notes ----

@notes_router.get("", response={200: List[NoteListItemSchema]})
@require_auth
def list_notes(
    request,
    folder_id: Optional[int] = None,
    unfiled: bool = False,
    archived: str = "active",
    pinned_only: bool = False,
    q: Optional[str] = None,
):
    notes = NoteService.list_notes(
        request.auth_user,
        folder_id=folder_id,
        unfiled=unfiled,
        archived=archived,
        pinned_only=pinned_only,
        q=q,
    )
    return [
        NoteService.serialize_note(note, include_content=False) for note in notes
    ]


@notes_router.post("", response={200: NoteResponseSchema})
@require_auth
def create_note(request, payload: NoteCreateSchema):
    note = NoteService.create_note(
        request.auth_user,
        **payload.model_dump(),
    )
    return NoteService.serialize_note(note)


@notes_router.get("/{note_id}", response={200: NoteResponseSchema})
@require_auth
def get_note(request, note_id: int):
    note = NoteService.get_note(request.auth_user, note_id)
    return NoteService.serialize_note(note)


@notes_router.patch("/{note_id}", response={200: NoteResponseSchema})
@require_auth
def update_note(request, note_id: int, payload: NoteUpdateSchema):
    note = NoteService.update_note(
        request.auth_user,
        note_id,
        **payload.model_dump(exclude_unset=True),
    )
    return NoteService.serialize_note(note)


@notes_router.delete("/{note_id}", response={200: dict})
@require_auth
def delete_note(request, note_id: int):
    NoteService.delete_note(request.auth_user, note_id)
    return {"message": "Note deleted"}


@notes_router.post("/{note_id}/pin", response={200: NoteResponseSchema})
@require_auth
def pin_note(request, note_id: int):
    note = NoteService.pin_note(request.auth_user, note_id, pinned=True)
    return NoteService.serialize_note(note)


@notes_router.post("/{note_id}/unpin", response={200: NoteResponseSchema})
@require_auth
def unpin_note(request, note_id: int):
    note = NoteService.pin_note(request.auth_user, note_id, pinned=False)
    return NoteService.serialize_note(note)


@notes_router.post("/{note_id}/archive", response={200: NoteResponseSchema})
@require_auth
def archive_note(request, note_id: int):
    note = NoteService.archive_note(request.auth_user, note_id, archived=True)
    return NoteService.serialize_note(note)


@notes_router.post("/{note_id}/unarchive", response={200: NoteResponseSchema})
@require_auth
def unarchive_note(request, note_id: int):
    note = NoteService.archive_note(request.auth_user, note_id, archived=False)
    return NoteService.serialize_note(note)
