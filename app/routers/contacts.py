# backend/app/routers/contacts.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.database import get_db
from ..db.models import User, Contact
from ..utils.security import verify_firebase_token
from ..schemas.contacts import ContactAddRequest, ContactResponse

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])

@router.post("/", response_model=dict)
async def add_contact(
    req: ContactAddRequest, 
    db: AsyncSession = Depends(get_db), 
    token: dict = Depends(verify_firebase_token)
):
    """Saves a Personly ID with a custom label to the authenticated user's contact list."""
    owner_uid = token.get("uid")
    
    # Verify the target user exists in the system
    result = await db.execute(select(User).where(User.personly_id == req.personly_id))
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="No user exists with this Personly ID.")
        
    # Prevent adding yourself
    owner_result = await db.execute(select(User).where(User.firebase_uid == owner_uid))
    owner = owner_result.scalars().first()
    if owner and owner.personly_id == req.personly_id:
        raise HTTPException(status_code=400, detail="You cannot add your own Personly ID as a contact.")

    # Prevent duplicate additions
    exists_query = await db.execute(
        select(Contact).where(
            Contact.owner_uid == owner_uid, 
            Contact.contact_personly_id == req.personly_id
        )
    )
    existing_contact = exists_query.scalars().first()
    
    if existing_contact:
        # Update label if already exists
        existing_contact.custom_label = req.custom_label
        await db.commit()
        return {"message": "Contact updated successfully."}
        
    new_contact = Contact(
        owner_uid=owner_uid, 
        contact_personly_id=req.personly_id,
        custom_label=req.custom_label
    )
    db.add(new_contact)
    await db.commit()
    
    return {"message": "Contact saved successfully."}

@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    db: AsyncSession = Depends(get_db), 
    token: dict = Depends(verify_firebase_token)
):
    """Retrieves all saved contacts for the authenticated user."""
    owner_uid = token.get("uid")
    result = await db.execute(select(Contact).where(Contact.owner_uid == owner_uid))
    contacts = result.scalars().all()
    
    return [
        ContactResponse(personly_id=c.contact_personly_id, custom_label=c.custom_label)
        for c in contacts
    ]

@router.delete("/{personly_id}")
async def remove_contact(
    personly_id: int, 
    db: AsyncSession = Depends(get_db), 
    token: dict = Depends(verify_firebase_token)
):
    """Removes a contact from the authenticated user's list."""
    owner_uid = token.get("uid")
    result = await db.execute(
        select(Contact).where(
            Contact.owner_uid == owner_uid, 
            Contact.contact_personly_id == personly_id
        )
    )
    contact = result.scalars().first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")
        
    await db.delete(contact)
    await db.commit()
    return {"message": "Contact removed successfully."}