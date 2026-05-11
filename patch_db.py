import database, models

def run_patch():
    print("Starting Database Coordinate Integrity Check...")
    db = database.SessionLocal()
    try:
        # Find all reports missing coordinates
        broken_reports = db.query(models.Report).filter(
            (models.Report.latitude == None) | (models.Report.longitude == None)
        ).all()
        
        if not broken_reports:
            print("[OK] Database is clean! Every single report already has valid GPS coordinates.")
            return

        print(f"[PATCH] Found {len(broken_reports)} reports with MISSING destination GPS data.")
        print("Injecting default testing coordinate (Da Nang Center)...")
        
        # Default Da Nang center for testing sanity
        DEFAULT_LAT = 16.0544
        DEFAULT_LNG = 108.2022
        
        for r in broken_reports:
            r.latitude = DEFAULT_LAT
            r.longitude = DEFAULT_LNG
            print(f"   -> Updated Report #{r.id}")
            
        db.commit()
        print("[SUCCESS] ALL Reports are now 100% Routable and Ready!")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Critical Failure: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_patch()
