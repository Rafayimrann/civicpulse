"""
Idempotent seed script: loads >=30 realistic complaints so the dashboard
demo isn't against an empty table.

Idempotency strategy: each seed complaint carries a stable, deterministic
UUID derived from its text (uuid5 against a fixed namespace), so running
this script twice INSERTs the same 30+ rows once and then no-ops on the
second run rather than duplicating them.

Usage:
    python -m scripts.seed
"""
from __future__ import annotations

import asyncio
import uuid

from app.db import session_scope
from app.models import Category, Complaint, Priority, Status

_SEED_NAMESPACE = uuid.UUID("6f2b1e3a-2f2a-4c9a-9a1e-2f6a9c3e7b10")

# Realistic, Urdu-influenced-English complaints spread across every category
# and priority, the way an actual municipal intake queue looks.
_SEED_COMPLAINTS: list[dict] = [
    {"text": "Burst water main flooding Street 12 since fajr, water entering ground floors of three houses.",
     "location": "Street 12, Block C", "category": Category.water, "priority": Priority.high},
    {"text": "No water supply in our gali for the last three days, tanker also not coming, please send help.",
     "location": "Gali 4, Model Town", "category": Category.water, "priority": Priority.high},
    {"text": "Sewage water is mixing with drinking water line near the masjid, bohat bura smell aa raha hai.",
     "location": "Near Jamia Masjid, Sector F", "category": Category.water, "priority": Priority.high},
    {"text": "Water pipe leaking slowly outside house number 45 for two weeks, wasting a lot of water daily.",
     "location": "House 45, Street 7", "category": Category.water, "priority": Priority.normal},
    {"text": "Low water pressure in whole colony since new connection was given to the housing society nearby.",
     "location": "Green Town Phase 2", "category": Category.water, "priority": Priority.low},
    {"text": "Transformer sparking loudly near the park, children play there daily, very dangerous please fix urgently.",
     "location": "Park Road, Sector G-9", "category": Category.electricity, "priority": Priority.high},
    {"text": "Complete power cut in our area since yesterday evening, no announcement was made by WAPDA.",
     "location": "Satellite Town, Block B", "category": Category.electricity, "priority": Priority.high},
    {"text": "Exposed electric wire hanging low over the footpath, ek bachi ko lagi thi, koi bara accident ho sakta hai.",
     "location": "Main Bazaar Road", "category": Category.electricity, "priority": Priority.high},
    {"text": "Frequent load shedding in evening hours, 4 to 5 hours daily, disturbing children's studies.",
     "location": "Chaklala Scheme 3", "category": Category.electricity, "priority": Priority.normal},
    {"text": "Street electricity meter box is open and rusted, needs cover repair before rain season starts.",
     "location": "Bahria Town Phase 4", "category": Category.electricity, "priority": Priority.low},
    {"text": "Garbage not collected from our street for ten days now, bohat ganda smell phail raha hai everywhere.",
     "location": "Street 9, Dhoke Kashmirian", "category": Category.sanitation, "priority": Priority.high},
    {"text": "Open drain overflowing near the school gate, bachay walk kar ke jate hain, health risk for students.",
     "location": "Near Govt Girls School, Sector I-8", "category": Category.sanitation, "priority": Priority.high},
    {"text": "Trash bins overflowing near the market since last week, stray dogs are spreading garbage everywhere.",
     "location": "Raja Bazaar", "category": Category.sanitation, "priority": Priority.normal},
    {"text": "Sanitation truck skips our lane every Tuesday, we have complained before but koi improvement nahi hua.",
     "location": "Street 3, Wapda Town", "category": Category.sanitation, "priority": Priority.normal},
    {"text": "Public toilet near the bus stand is very dirty and has no water, needs urgent cleaning and repair.",
     "location": "Pirwadhai Bus Terminal", "category": Category.sanitation, "priority": Priority.normal},
    {"text": "Large pothole in the middle of the road causing accidents, do motorcycles already gir chuki hain is hafte.",
     "location": "GT Road near Faizabad", "category": Category.roads, "priority": Priority.high},
    {"text": "Traffic signal not working at busy intersection for three days, causing bohat traffic jam har waqt.",
     "location": "Committee Chowk", "category": Category.roads, "priority": Priority.high},
    {"text": "Road collapsed partially after last rain near the culvert, dangerous for cars at night without any warning sign.",
     "location": "Service Road, Sector G-11", "category": Category.roads, "priority": Priority.high},
    {"text": "Speed breaker on main road is too high and unmarked, several bikes have skidded there in the dark.",
     "location": "Adiala Road", "category": Category.roads, "priority": Priority.normal},
    {"text": "Footpath tiles are broken in front of the park, elderly log ko chalne mein bohat mushkil hoti hai.",
     "location": "F-10 Markaz", "category": Category.roads, "priority": Priority.low},
    {"text": "Long stretch of road has cracks developing after the gas pipeline work, needs proper resurfacing.",
     "location": "Murree Road", "category": Category.roads, "priority": Priority.normal},
    {"text": "Streetlights not working on our entire street for two weeks, bohat andhera hota hai raat ko, women scared to walk.",
     "location": "Street 6, Dhoke Ratta", "category": Category.streetlights, "priority": Priority.high},
    {"text": "Streetlight pole is leaning dangerously after the storm, might fall on parked cars anytime.",
     "location": "Bank Road", "category": Category.streetlights, "priority": Priority.high},
    {"text": "Half of the streetlights on the main avenue flicker on and off randomly every night.",
     "location": "Mall Road", "category": Category.streetlights, "priority": Priority.normal},
    {"text": "New streetlights installed last month but two poles near the park were skipped, please add them too.",
     "location": "Fatima Jinnah Park Road", "category": Category.streetlights, "priority": Priority.low},
    {"text": "Streetlight timer seems wrong, lights turn off around midnight and stay off till morning, needs adjustment.",
     "location": "Sadiqabad Street 2", "category": Category.streetlights, "priority": Priority.low},
    {"text": "Stray dogs gathering near the children's park every evening, parents are afraid to let kids go out and play.",
     "location": "Askari Park", "category": Category.other, "priority": Priority.normal},
    {"text": "Illegal construction blocking half the street, trucks cannot pass through during the day anymore.",
     "location": "Street 14, Chaklala Scheme 1", "category": Category.other, "priority": Priority.normal},
    {"text": "Noise pollution from wedding hall generator running all night, residents unable to sleep properly.",
     "location": "Near Shadi Hall, Sector E-11", "category": Category.other, "priority": Priority.low},
    {"text": "Public park equipment is broken and rusted, swing chain snapped last week, unsafe for children.",
     "location": "Liaquat Bagh", "category": Category.other, "priority": Priority.normal},
    {"text": "Illegal parking outside the hospital gate blocking ambulance entry, emergency ho to bara masla ho sakta hai.",
     "location": "DHQ Hospital Gate", "category": Category.other, "priority": Priority.high},
    {"text": "Encroachment by vendors on the main footpath forces pedestrians to walk on the busy road instead.",
     "location": "Commercial Market, Block D", "category": Category.roads, "priority": Priority.normal},
]


async def seed() -> None:
    inserted = 0
    async with session_scope() as session:
        for item in _SEED_COMPLAINTS:
            stable_id = uuid.uuid5(_SEED_NAMESPACE, item["text"])

            existing = await session.get(Complaint, stable_id)
            if existing is not None:
                continue

            complaint = Complaint(
                id=stable_id,
                text=item["text"],
                location=item["location"],
                reporter_contact=None,
                category=item["category"],
                priority=item["priority"],
                status=Status.open,
                ai_summary=item["text"][:137] + ("..." if len(item["text"]) > 137 else ""),
                triaged_by="rules:seed",
                triage_latency_ms=0,
            )
            session.add(complaint)
            inserted += 1

    print(f"Seed complete: {inserted} new complaints inserted, "
          f"{len(_SEED_COMPLAINTS) - inserted} already present (skipped).")


if __name__ == "__main__":
    asyncio.run(seed())
