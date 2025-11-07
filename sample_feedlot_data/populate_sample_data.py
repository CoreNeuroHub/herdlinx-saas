#!/usr/bin/env python3
"""
Populate the HerdLinx database with realistic Alberta cattle industry sample data.
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta
from typing import List, Tuple


# Alberta cattle industry realistic data
ALBERTA_FEEDLOTS = [
    "High River Feeders",
    "Lethbridge Cattle Co.",
    "Calgary Feedlot Services",
    "Red Deer Valley Feeders",
    "Medicine Hat Feedlot"
]

FUNDERS = [
    "Alberta Beef Producers",
    "Canadian Cattle Association",
    "Feedlot Financing Inc.",
    "Western Livestock Co.",
    "Prairie Feedlot Partners"
]

BREEDS = [
    "Angus", "Hereford", "Charolais", "Simmental", "Limousin",
    "Red Angus", "Black Angus", "Gelbvieh", "Maine-Anjou", "Shorthorn"
]

TAG_COLORS = ["Red", "Yellow", "Blue", "Green", "White", "Orange"]

PEN_LOCATIONS = [
    "North Section", "South Section", "East Section", "West Section",
    "Central Section", "Northwest Corner", "Southeast Corner"
]

LOT_GROUPS = ["A", "B", "C", "D", "E", "F"]

REPAIR_REASONS = [
    "LF tag lost during handling",
    "UHF tag damaged in pen",
    "LF tag torn off",
    "UHF tag malfunction",
    "Tag replacement due to wear",
    "LF tag unreadable"
]


def generate_lf_tag():
    """Generate a realistic LF tag ID (typically 8-12 digits)."""
    return f"LF{random.randint(1000000, 9999999)}"


def generate_epc():
    """Generate a realistic EPC tag (hex format, typically 24 chars)."""
    return f"EPC{''.join(random.choices('0123456789ABCDEF', k=20))}"


def generate_timestamp(base_date, days_offset=0, hours_offset=0):
    """Generate ISO timestamp."""
    dt = base_date + timedelta(days=days_offset, hours=hours_offset)
    return dt.isoformat() + "Z"


def populate_batches(cursor, count=5):
    """Populate batches table with realistic data."""
    print(f"Creating {count} batches...")
    
    base_date = datetime(2024, 9, 1)
    batches = []
    
    for i in range(count):
        batch_date = base_date + timedelta(days=i * 14)  # Batches every 2 weeks
        batch_name = f"Batch {chr(65 + i)} - {batch_date.strftime('%b %d')}"
        
        batch_data = (
            batch_name,
            random.choice(FUNDERS),
            f"LOT{random.randint(100, 999)}",
            f"PEN{random.randint(1, 50):02d}",
            random.choice(LOT_GROUPS),
            random.choice(PEN_LOCATIONS),
            random.choice(["M", "F", "Mixed"]),
            random.choice(TAG_COLORS),
            f"VIS{random.randint(1000, 9999)}",
            f"Batch notes: {random.choice(['High quality', 'Standard processing', 'Premium grade'])}",
            generate_timestamp(batch_date),
            1 if i == count - 1 else 0  # Last batch is active
        )
        
        cursor.execute("""
            INSERT INTO batches (name, funder, lot, pen, lot_group, pen_location, 
                               sex, tag_color, visual_id, notes, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)
        
        batch_id = cursor.lastrowid
        batches.append((batch_id, batch_name, batch_date))
    
    return batches


def populate_livestock_and_events(cursor, batches: List[Tuple], animals_per_batch=50):
    """Populate livestock, induction events, pairing events, and check-in events."""
    print(f"Creating {len(batches) * animals_per_batch} cattle records with events...")
    
    livestock_id = 1
    
    for batch_id, batch_name, batch_date in batches:
        print(f"  Processing batch: {batch_name}")
        
        # Create animals for this batch
        for animal_num in range(animals_per_batch):
            # Induction event timestamp (within batch date)
            induction_timestamp = generate_timestamp(
                batch_date,
                days_offset=random.randint(0, 2),
                hours_offset=random.randint(8, 16)
            )
            
            # Create livestock record first (without induction_event_id)
            cursor.execute("""
                INSERT INTO livestock (induction_event_id, current_lf_id, current_epc, 
                                     metadata, created_at, updated_at)
                VALUES (NULL, NULL, NULL, ?, ?, ?)
            """, (
                random.choice(BREEDS),
                induction_timestamp,
                induction_timestamp
            ))
            
            livestock_id = cursor.lastrowid
            
            # Create induction event
            cursor.execute("""
                INSERT INTO induction_events (livestock_id, batch_id, timestamp)
                VALUES (?, ?, ?)
            """, (livestock_id, batch_id, induction_timestamp))
            
            induction_event_id = cursor.lastrowid
            
            # Update livestock with induction_event_id
            cursor.execute("""
                UPDATE livestock SET induction_event_id = ? WHERE id = ?
            """, (induction_event_id, livestock_id))
            
            # Pairing event (usually happens same day or next day)
            pairing_datetime = batch_date + timedelta(
                days=random.randint(0, 1),
                hours=random.randint(9, 17)
            )
            pairing_timestamp = generate_timestamp(pairing_datetime)
            
            lf_id = generate_lf_tag()
            epc = generate_epc()
            initial_weight = random.uniform(200.0, 350.0)  # Initial weight in kg
            
            cursor.execute("""
                INSERT INTO pairing_events (livestock_id, lf_id, epc, weight_kg, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (livestock_id, lf_id, epc, initial_weight, pairing_timestamp))
            
            # Update livestock with current tags
            cursor.execute("""
                UPDATE livestock SET current_lf_id = ?, current_epc = ?, updated_at = ?
                WHERE id = ?
            """, (lf_id, epc, pairing_timestamp, livestock_id))
            
            # Create check-in events (weight measurements over time)
            # First check-in is at pairing
            cursor.execute("""
                INSERT INTO checkin_events (livestock_id, lf_id, epc, weight_kg, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (livestock_id, lf_id, epc, initial_weight, pairing_timestamp))
            
            # Additional check-ins (every 2-4 weeks after pairing)
            current_weight = initial_weight
            last_checkin_date = pairing_datetime
            
            for checkin_num in range(random.randint(2, 5)):  # 2-5 additional check-ins
                # Calculate next check-in date (14-28 days after last check-in)
                days_until_next = random.randint(14, 28)
                checkin_date = last_checkin_date + timedelta(days=days_until_next)
                
                # Weight gain: 0.8-1.5 kg per day
                weight_gain = days_until_next * random.uniform(0.8, 1.5)
                current_weight += weight_gain
                
                checkin_timestamp = generate_timestamp(
                    checkin_date,
                    days_offset=0,
                    hours_offset=random.randint(8, 16)
                )
                
                cursor.execute("""
                    INSERT INTO checkin_events (livestock_id, lf_id, epc, weight_kg, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (livestock_id, lf_id, epc, round(current_weight, 2), checkin_timestamp))
                
                last_checkin_date = checkin_date
            
            # Some animals have repair events (about 5% chance)
            if random.random() < 0.05:
                repair_date = batch_date + timedelta(days=random.randint(30, 90))
                repair_timestamp = generate_timestamp(repair_date, hours_offset=random.randint(8, 16))
                
                repair_type = random.choice(["lf", "uhf", "both"])
                old_lf_id = lf_id if repair_type in ["lf", "both"] else None
                new_lf_id = generate_lf_tag() if repair_type in ["lf", "both"] else None
                old_epc = epc if repair_type in ["uhf", "both"] else None
                new_epc = generate_epc() if repair_type in ["uhf", "both"] else None
                
                cursor.execute("""
                    INSERT INTO repair_events (livestock_id, old_lf_id, new_lf_id, 
                                             old_epc, new_epc, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (livestock_id, old_lf_id, new_lf_id, old_epc, new_epc,
                      random.choice(REPAIR_REASONS), repair_timestamp))
                
                # Update livestock with new tags
                if new_lf_id:
                    lf_id = new_lf_id
                if new_epc:
                    epc = new_epc
                
                cursor.execute("""
                    UPDATE livestock SET current_lf_id = ?, current_epc = ?, updated_at = ?
                    WHERE id = ?
                """, (lf_id, epc, repair_timestamp, livestock_id))


def main():
    """Main function to populate the database."""
    db_path = "herdlinx.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Please run db_init.py first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM batches")
    batch_count = cursor.fetchone()[0]
    
    if batch_count > 0:
        response = input(f"Database already contains {batch_count} batches. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            conn.close()
            return
        
        # Clear existing data
        print("Clearing existing data...")
        cursor.execute("DELETE FROM repair_events")
        cursor.execute("DELETE FROM checkin_events")
        cursor.execute("DELETE FROM pairing_events")
        cursor.execute("DELETE FROM induction_events")
        cursor.execute("DELETE FROM livestock")
        cursor.execute("DELETE FROM batches")
        conn.commit()
    
    # Populate data
    batches = populate_batches(cursor, count=5)
    conn.commit()
    
    populate_livestock_and_events(cursor, batches, animals_per_batch=50)
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT COUNT(*) FROM batches")
    batch_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM livestock")
    livestock_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM induction_events")
    induction_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pairing_events")
    pairing_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM checkin_events")
    checkin_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM repair_events")
    repair_count = cursor.fetchone()[0]
    
    print("\n" + "="*50)
    print("Database Population Summary")
    print("="*50)
    print(f"Batches:           {batch_count}")
    print(f"Livestock:         {livestock_count}")
    print(f"Induction Events:  {induction_count}")
    print(f"Pairing Events:    {pairing_count}")
    print(f"Check-in Events:   {checkin_count}")
    print(f"Repair Events:      {repair_count}")
    print("="*50)
    
    conn.close()
    print(f"\nSample data populated successfully in {db_path}")


if __name__ == "__main__":
    main()

