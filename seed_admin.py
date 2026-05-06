import database
import models
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

try:
    db = database.SessionLocal()
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        admin = models.User(
            username="admin",
            hashed_password=hash_password("admin"),
            role="moderator",
            full_name="Cán bộ điều phối",
            department="Trung tâm Điều hành Đô thị"
        )
        db.add(admin)
    else:
        admin.hashed_password = hash_password("admin")
        admin.role = "moderator"
        admin.full_name = "Cán bộ điều phối"
        admin.department = "Trung tâm Điều hành Đô thị"

    # Also let's check or create exec_light, exec_water, exec_traffic
    execs = [
        ("exec_light", "đèn tín hiệu", "Đội Thi công Cầu đường Ngũ Hành Sơn"),
        ("exec_water", "ngập nước", "Đội Công trình Thoát nước Thanh Khê"),
        ("exec_traffic", "ùn tắc giao thông", "Đội Điều phối Đô thị Hải Châu")
    ]
    for username, specialty, full_name in execs:
        u = db.query(models.User).filter(models.User.username == username).first()
        if u:
            u.hashed_password = hash_password("exec123")
            u.specialty = specialty
            u.full_name = full_name
            u.role = "executor"

    db.commit()
    db.close()
    print("Successfully seeded/reset admin & executors in the database!")
except Exception as e:
    print(f"Error seeding database: {e}")
