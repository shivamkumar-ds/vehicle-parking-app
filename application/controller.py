from flask import flash 
from flask import jsonify
from flask import render_template, redirect, request, session,url_for
from datetime import datetime, timedelta
from .models import User, Booking, ParkingSpot, db
from flask import current_app as app
from sqlalchemy import func
from application.database import db
from application.models import User
from flask import url_for
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

from application.controller import *
from .models import *  # Import models if needed
import random
import string
from datetime import datetime
import calendar


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        this_user = User.query.filter_by(email=email).first()  # Fetch user from database

        if this_user:
            if this_user.type == "admin":
                if this_user.password == password:
                    session["user_name"] = this_user.name
                    session["user_id"] = this_user.id
                    return redirect(url_for('admin_dashboard'))

            elif this_user.type == "user":
                if bcrypt.check_password_hash(this_user.password, password):
                    session["user_name"] = this_user.name
                    session["user_id"] = this_user.id
                    return redirect(url_for('user_dashboard'))

            return render_template("incorrect_password.html")  # ✅ Fix: Handle incorrect password properly

        return render_template("not_exist.html")  # ✅ Fix: Users are properly checked

    return render_template("login.html")


@app.route("/signup",methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        address = request.form.get("address")
        pincode = request.form.get("pincode")

        if not email or not password or not name or not address or not pincode:
            return render_template("signup.html", error="All fields are required.")
        # Validation
        if not all([email, password, name, address, pincode]):
            return render_template("signup.html", error="All fields are required.")
        if len(password) < 4:
            return render_template("signup.html", error="Password must be at least 4 characters long.")
        if len(pincode) != 6 or not pincode.isdigit():
            return render_template("signup.html", error="Pincode must be a 6-digit number.")
        if "@" not in email or "." not in email.split("@")[-1]:
            return render_template("signup.html", error="Invalid email format.")
        
        user_email = User.query.filter_by(email=email).first()
        if user_email:
            return render_template("already.html")
        else:
            new_user = User(email=email,password=password,name=name,address=address,pincode=pincode,type="user")
            new_user.password = bcrypt.generate_password_hash(new_user.password).decode('utf-8')
            db.session.add(new_user)
            db.session.commit()
            return render_template("registration_success.html", redirect_url=url_for("login"))
    return render_template("signup.html")

@app.route("/adminprofile", methods=["GET", "POST"])
def adminprofile():
    if "user_name" not in session:
        return redirect(url_for("login"))
    this_user = User.query.filter_by(name=session["user_name"]).first()
    if request.method == "POST":
        this_user.name = request.form.get("name")
        this_user.email = request.form.get("email")
        this_user.address = request.form.get("address")
        this_user.pincode = request.form.get("pincode")
        db.session.commit()
        session["user_name"] = this_user.name
        return redirect(url_for("admin_dashboard"))     
    return render_template("adminprofile.html",user=this_user)

@app.route("/userprofile", methods=["GET", "POST"])
def userprofile():
    if "user_name" not in session:
        return redirect(url_for("login"))
    this_user = User.query.filter_by(name=session["user_name"]).first()
    if request.method=="POST":
        this_user.name = request.form.get("name")
        this_user.email = request.form.get("email")
        this_user.address = request.form.get("address")
        this_user.pincode = request.form.get("pincode")
        new_password = request.form.get("password")
        if new_password:
            this_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        session["user_name"] = this_user.name
        return redirect(url_for("user_dashboard"))
    return render_template("userprofile.html", user=this_user)

@app.route("/delete_profile", methods=["POST"])
def delete_profile():
    if "user_name" not in session:
        return redirect(url_for("login"))

    this_user = User.query.filter_by(name=session["user_name"]).first()
    
    if this_user:
        db.session.delete(this_user)
        db.session.commit()
        session.pop("user_name", None) 

    return redirect(url_for("login"))

@app.route("/admin_dashboard")
def admin_dashboard():
    parking_lots=ParkingLot.query.all()
    # message="New parking lot added successfully."
    return render_template("admin_dashboard.html", parking_lots=parking_lots)

@app.route("/users")
def users():
    all_users = User.query.all()
    return render_template("users.html", users=all_users)

@app.route("/search")
def search():
    q = request.args.get("query", "").strip()

    user_results = User.query.filter(
        (User.name.ilike(f"%{q}%")) |
        (User.email.ilike(f"%{q}%")) |
        (User.address.ilike(f"%{q}%")) |
        (User.pincode.ilike(f"%{q}%"))
    ).all()

    lot_results = ParkingLot.query.filter(
        (ParkingLot.location_name.ilike(f"%{q}%")) |
        (ParkingLot.address.ilike(f"%{q}%")) |
        (ParkingLot.pincode.ilike(f"%{q}%"))
    ).all()

    return render_template("search_results.html", query=q, user_results=user_results, lot_results=lot_results)



@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        flash("Please log in to view your dashboard.")
        return redirect(url_for("login"))
    parking_lots = ParkingLot.query.all()
    return render_template("user_dashboard.html", parking_lots=parking_lots)



@app.route("/newlot", methods=["GET", "post"])
def newlot():
    if request.method == "POST": 
        location = request.form["location_name"]
        address = request.form["address"]
        pincode = request.form["pincode"]
        price_per_hour = request.form["price_per_hour"]
        max_spots = request.form["max_spots"]
        new_lot = ParkingLot(location_name=location, address=address, pincode=pincode, price_per_hour=price_per_hour, max_spots=max_spots)
        db.session.add(new_lot)
        db.session.commit()
        for _ in range(int(max_spots)):
            new_spot = ParkingSpot(status="available", parking_lot_id=new_lot.id)
            db.session.add(new_spot)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("newlot.html")

@app.route("/delete_lot/<int:lot_id>")
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    # Delete associated parking spots
    ParkingSpot.query.filter_by(parking_lot_id=lot.id).delete()

    # Optionally delete bookings/history if you want full cleanup
    Booking.query.filter_by(parking_lot_id=lot.id).delete()
    ParkingHistory.query.filter_by(parking_lot_id=lot.id).delete()

    db.session.delete(lot)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))


@app.route("/updatelot/<int:lot_id>", methods=["GET", "POST"])
def updatelot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == "POST":
        lot.location_name = request.form["location_name"]
        lot.address = request.form["address"]
        lot.pincode = request.form["pincode"]
        lot.price_per_hour = float(request.form["price_per_hour"])
        lot.max_spots = int(request.form["max_spots"])

        # Update parking spots
        current_spots = ParkingSpot.query.filter_by(parking_lot_id=lot.id).count()
        new_spots_count = lot.max_spots

        if new_spots_count > current_spots:
            for _ in range(new_spots_count - current_spots):
                new_spot = ParkingSpot(status="available", parking_lot_id=lot.id)
                db.session.add(new_spot)
        elif new_spots_count < current_spots:
            spots_to_remove = ParkingSpot.query.filter_by(parking_lot_id=lot.id).limit(current_spots - new_spots_count).all()
            for spot in spots_to_remove:
                db.session.delete(spot)

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("updatelot.html", lot=lot)


@app.route("/occupied")
def occupied():
    return render_template("occupied.html")

@app.route("/incorrect_password")
def incorrect_password():
    return render_template("incorrect_password.html")

@app.route("/not_exist")
def not_exist():
    return render_template("not_exist.html")

@app.route("/book/<int:spot_id>", methods=["GET", "POST"])
def book(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    lot = ParkingLot.query.get(spot.parking_lot_id)
    user_id = session.get("user_id")

    if not user_id:
        flash("Session expired. Please log in again.")
        return redirect(url_for("login"))

    if request.method == "POST":
        vehicle_number = request.form.get("vehicle_number")

        if not vehicle_number:
            flash("Vehicle number is required.")
            return redirect(url_for("book", spot_id=spot_id))

        # Update spot
        spot.status = "occupied"
        spot.customer_id = user_id
        spot.vehicle_number = vehicle_number
        spot.date_time_of_parking = datetime.utcnow()

        # Create booking
        new_booking = Booking(
            user_id=user_id,
            parking_lot_id=lot.id,
            parking_spot_id=spot.id,
            vehicle_number=vehicle_number
        )
        db.session.add(new_booking)
        db.session.commit()

        flash("Slot booked successfully!")
        return redirect(url_for("user_dashboard"))

    return render_template("book.html", spot=spot, lot=lot, user_id=user_id)


@app.route("/release/<int:spot_id>", methods=["GET", "POST"])
def release(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    user_id = session.get("user_id")

    if spot.customer_id != user_id:
        return "Unauthorized", 403

    lot = ParkingLot.query.get(spot.parking_lot_id)
    booking = Booking.query.filter_by(
        parking_spot_id=spot.id, 
        user_id=user_id
    ).order_by(Booking.booking_time.desc()).first()

    if request.method == "GET":
        # ⏱️ Accurate cost preview using per-second logic
        seconds = (datetime.utcnow() - spot.date_time_of_parking).total_seconds()
        cost_per_second = lot.price_per_hour / 3600
        preview_cost = round(max(seconds * cost_per_second, 0.01), 2)

        return render_template("release.html", spot=spot, booking=booking, lot=lot, preview_cost=preview_cost)

    # 🚀 On POST: finalize release & charge
    release_time = datetime.utcnow()
    seconds = (release_time - spot.date_time_of_parking).total_seconds()
    cost_per_second = lot.price_per_hour / 3600
    final_cost = round(max(seconds * cost_per_second, 0.01), 2)

    booking.release_time = release_time
    booking.total_cost = final_cost

    history = ParkingHistory(
        user_id=user_id,
        parking_lot_id=lot.id,
        vehicle_number=spot.vehicle_number,
        action="released"
    )
    db.session.add(history)

    spot.status = "available"
    spot.customer_id = None
    spot.vehicle_number = None
    spot.date_time_of_parking = None

    db.session.commit()

    return redirect(url_for("payment", amount=final_cost))




@app.route("/payment")
def payment():
    amount = request.args.get("amount")
    return render_template("payment.html", amount=amount)

@app.route("/paymentsuccess")
def paymentsuccess():
    return render_template("paymentsuccess.html")

@app.route("/history")
def history():
    user_id = session.get("user_id")
    records = ParkingHistory.query.filter_by(user_id=user_id).order_by(ParkingHistory.timestamp.desc()).all()
    return render_template("history.html", records=records)

@app.route('/adminsummary')
def admin_summary():
    total_users = User.query.count()
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    total_bookings_today = Booking.query.filter(
        db.func.date(Booking.booking_time) == today
    ).count()
    total_bookings_week = Booking.query.filter(
        db.func.date(Booking.booking_time) >= week_ago
    ).count()
    active_vehicles = Booking.query.filter(Booking.release_time == None).count()

    revenue = db.session.query(
        db.func.sum(Booking.total_cost)
    ).scalar() or 0  # Prevent None

    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status='occupied').count()
    available_spots = total_spots - occupied_spots

    return render_template("adminsummary.html",
                           total_users=total_users,
                           total_bookings_today=total_bookings_today,
                           total_bookings_week=total_bookings_week,
                           active_vehicles=active_vehicles,
                           revenue=round(revenue, 2),
                           occupied_spots=occupied_spots,
                           available_spots=available_spots)


@app.route('/admin/spot/<int:spot_id>')
def get_spot_info(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status == 'occupied':
        booking = Booking.query.filter_by(parking_spot_id=spot_id, release_time=None).first()
        estimated = calculate_estimated_cost(booking)
        return {
            'occupied': True,
            'spot_id': spot.id,
            'customer_id': spot.customer_id,
            'vehicle_number': booking.vehicle_number,
            'booking_time': str(booking.booking_time),
            'estimated_cost': estimated
        }
    return {
        'occupied': False,
        'spot_id': spot.id
    }
@app.route('/admin/spot/delete/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status == 'occupied':
        flash("Cannot delete an occupied spot.")
        return redirect('/admin_dashboard')
    db.session.delete(spot)
    db.session.commit()
    flash("Spot deleted.")
    return redirect('/admin_dashboard')

def calculate_estimated_cost(booking):
    if not booking or not booking.booking_time:
        return 0
    now = datetime.utcnow()
    duration = now - booking.booking_time
    hours = duration.total_seconds() / 3600
    rate = booking.total_cost
    return rate

from flask import session

@app.route('/user_summary')
def user_summary():
    user_id = session.get("user_id")  # 👈 Logged-in user ID from session
    if not user_id:
        return redirect("/login")  # if not logged in

    raw_bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_time.desc()).all()

    history = []
    for b in raw_bookings:
        lot = ParkingLot.query.get(b.parking_lot_id)
        spot = ParkingSpot.query.get(b.parking_spot_id)
        history.append({
            'vehicle_number': b.vehicle_number,
            'lot_name': lot.location_name if lot else 'Unknown',
            'spot_id': spot.id if spot else 'Unknown',
            'booking_time': b.booking_time,
            'release_time': b.release_time,
            'total_cost': b.total_cost or 0
        })

    return render_template("user_summary.html", history=history)

@app.route('/admin/spot/<int:spot_id>', methods=['GET'])
def admin_spot_info(spot_id):
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        return jsonify({'error': 'Slot not found'})

    if spot.status == 'occupied':
        booking = Booking.query.filter_by(parking_spot_id=spot_id, release_time=None).first()
        now = datetime.utcnow()
        parked_at = booking.booking_time if booking else (spot.date_time_of_parking or now)
        hours = max((now - parked_at).total_seconds() / 3600, 0.01)
        cost_per_hour = spot.lot.price_per_hour
        est_cost = round(hours * cost_per_hour, 2)

        return jsonify({
            'occupied': True,
            'spot_id': spot.id,
            'lot_id': spot.parking_lot_id,
            'customer_id': spot.customer_id,
            'vehicle_number': spot.vehicle_number,
            'parking_time': parked_at.strftime('%Y-%m-%d %H:%M'),
            'estimated_cost': est_cost
        })
    else:
        return jsonify({'occupied': False, 'spot_id': spot.id})

