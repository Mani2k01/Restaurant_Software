import json
import os
import random
from db import Database
from datetime import datetime
from flask import Flask, redirect, render_template, url_for, request, session, jsonify


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
db = Database("restaurant")

@app.route('/')
def home():
    return render_template("Home.html")

@app.route('/table_order', methods = ["GET", "POST"])
def table_order():
    tables = fetch_table_status()
    if request.method == 'POST':
        table_id = request.form.get('table_id')
        persons = request.form.get('persons')
        print("Table:", table_id, "Persons:", persons)
        session["current_table"] = {
            "table": table_id,
            "persons": persons,
            "status": "YET TO ORDER"
        }
        session.modified = True
        query = "update Dine_Tables set table_status = %s, persons = %s where table_id = %s"
        values = ("YET TO ORDER", persons, table_id)
        result = db.update_data(query, values)
        return redirect(url_for('order_entry'))
    return render_template("Table_order.html", tables = tables)


@app.route('/order_entry', methods=["GET", "POST"])
def order_entry():
    # Get selected table from session
    table_ctx = session.get("current_table")
    order_id = session.get("order_id")
    print(table_ctx)
    if not table_ctx:
        return redirect(url_for("table_order"))  # redirect if no table selected

    table_id = table_ctx["table"]
    order_person = session.get("order_name", "")

    # Fetch existing orders from session, default empty dict
    orders_by_table = session.get("orders_by_table", {})
    active_order = orders_by_table.get(table_id, {})

    # Food list
    foods = [
        # South Indian – Veg
        {"name": "Masala Dosa", "price": 120, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1600628422019-4b1ec7c85c10"},
        {"name": "Plain Dosa", "price": 90, "veg": True, "category": "South Indian", "img": "https://images.unsplash.com/photo-1668236544324-43a2c5c49f65"},
        {"name": "Idli (2 pcs)", "price": 60, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1589302168068-964664d93dc0"},
        {"name": "Vada (2 pcs)", "price": 70, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56"},
        {"name": "Pongal", "price": 80, "veg": True, "category": "South Indian", "img": "https://images.unsplash.com/photo-1600628422019-df1b5b2ddca5"},
        {"name": "Veg Meals", "price": 150, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1626509653291-57d9eaa6f0f2"},

        # Starters
        {"name": "Gobi 65", "price": 140, "veg": True, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1600628422020-6b43b0c2a2a1"},
        {"name": "Paneer 65", "price": 160, "veg": True, "category": "Starters", "img": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46"},
        {"name": "Chicken 65", "price": 180, "veg": False, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1604908554161-4d6b32f8e04f"},
        {"name": "Chicken Lollipop", "price": 220, "veg": False, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1606756790138-261d2b21cd75"},

        # Main Course – Non Veg
        {"name": "Chicken Biryani", "price": 220, "veg": False, "category": "Main Course", "popular": True, "img": "https://images.unsplash.com/photo-1600628422019-4e4f3c0c33a3"},
        {"name": "Mutton Biryani", "price": 280, "veg": False, "category": "Main Course", "img": "https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a"},

        # Beverages
        {"name": "Filter Coffee", "price": 40, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1509042239860-f550ce710b93"},
        {"name": "Tea", "price": 30, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1511920170033-f8396924c348"},
        {"name": "Fresh Lime Soda", "price": 50, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1542444459-db5c1f1cbbf2"},
        {"name": "Butter Milk", "price": 30, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1626203050468-3d0c0f1e7d4f"},

        # Combos
        {"name": "Mini Tiffin Combo", "price": 160, "veg": True, "category": "Combos", "combo": True, "img": "https://images.unsplash.com/photo-1600628422019-0f8bdbf4f5bb"},
        {"name": "Chicken Feast Combo", "price": 320, "veg": False, "category": "Combos", "combo": True, "img": "https://images.unsplash.com/photo-1604908554161-4d6b32f8e04f"}
    ]

    if request.method == "POST":
        order_name = request.form.get("order_name")
        action = request.form.get("action")
        order_data = json.loads(request.form.get("order_data"))

        # mark all items as ORDERED
        for item in order_data.values():
            item["status"] = "ORDERED"

        order_total = sum(item["total"] for item in order_data.values())
        session["order_name"] = order_name

        # Save order in session per table
        orders_by_table[table_id] = {
            "order": order_data,
            "order_total": order_total,
            "person": order_name
        }
        session["orders_by_table"] = orders_by_table
        session.modified = True

        # Save in DB if submitting
        if action == "submit":
            query = "INSERT INTO food_order (table_id, Name, order_amount, order_items, order_type) VALUES (%s,%s,%s,%s,%s)"
            data = (table_id, order_name, order_total, json.dumps(order_data), "TABLE")
            result = db.insert_data(query, data)
            if result:
                # Update table status
                db.update_data("UPDATE Dine_Tables SET table_status=%s WHERE table_id=%s", ("OCCUPIED", table_id))
                session["current_table"]["status"] = "Occupied"
                order_id = fetch_order_id(table_id)
                session["order_id"] = order_id
                return redirect(url_for("order_entry"))

        elif action == "pay":
            current = orders_by_table.get(table_id)
            if not current:
                session["js_alert"] = "No active order"
                return redirect(url_for("order_entry"))

            # Mark table cleaning
            db.update_data("UPDATE Dine_Tables SET table_status='CLEANING', persons=0 WHERE table_id=%s", (table_id,))
            # Remove order from session
            orders_by_table.pop(table_id, None)
            session["orders_by_table"] = orders_by_table
            session["js_alert"] = "Payment successful. Order closed."
            return redirect(url_for("order_entry"))
    active_order = orders_by_table.get(table_id, {}).get("order", {})
    print("active_order :" , orders_by_table )
    
    print("order : ", table_ctx)
    return render_template(
        "Order_Entry.html",
        order=table_ctx,
        foods=foods,
        active_order=active_order,
        order_person=order_person,
        order_id=order_id
    )







# @app.route('/order_entry', methods = ["GET", "POST"])
# def order_entry():
#     table_ctx = session.get("current_table")
#     active_order = session.get("active_order")
#     current_order = session.get("current_order")
#     order_person = session.get("order_name")
#     print("active order: ", active_order)
#     print("current _order: ", current_order)
#     foods = [
#         # South Indian – Veg
#         {"name": "Masala Dosa", "price": 120, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1600628422019-4b1ec7c85c10"},
#         {"name": "Plain Dosa", "price": 90, "veg": True, "category": "South Indian", "img": "https://images.unsplash.com/photo-1668236544324-43a2c5c49f65"},
#         {"name": "Idli (2 pcs)", "price": 60, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1589302168068-964664d93dc0"},
#         {"name": "Vada (2 pcs)", "price": 70, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56"},
#         {"name": "Pongal", "price": 80, "veg": True, "category": "South Indian", "img": "https://images.unsplash.com/photo-1600628422019-df1b5b2ddca5"},
#         {"name": "Veg Meals", "price": 150, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1626509653291-57d9eaa6f0f2"},

#         # Starters
#         {"name": "Gobi 65", "price": 140, "veg": True, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1600628422020-6b43b0c2a2a1"},
#         {"name": "Paneer 65", "price": 160, "veg": True, "category": "Starters", "img": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46"},
#         {"name": "Chicken 65", "price": 180, "veg": False, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1604908554161-4d6b32f8e04f"},
#         {"name": "Chicken Lollipop", "price": 220, "veg": False, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1606756790138-261d2b21cd75"},

#         # Main Course – Non Veg
#         {"name": "Chicken Biryani", "price": 220, "veg": False, "category": "Main Course", "popular": True, "img": "https://images.unsplash.com/photo-1600628422019-4e4f3c0c33a3"},
#         {"name": "Mutton Biryani", "price": 280, "veg": False, "category": "Main Course", "img": "https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a"},

#         # Beverages
#         {"name": "Filter Coffee", "price": 40, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1509042239860-f550ce710b93"},
#         {"name": "Tea", "price": 30, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1511920170033-f8396924c348"},
#         {"name": "Fresh Lime Soda", "price": 50, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1542444459-db5c1f1cbbf2"},
#         {"name": "Butter Milk", "price": 30, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1626203050468-3d0c0f1e7d4f"},

#         # Combos
#         {"name": "Mini Tiffin Combo", "price": 160, "veg": True, "category": "Combos", "combo": True, "img": "https://images.unsplash.com/photo-1600628422019-0f8bdbf4f5bb"},
#         {"name": "Chicken Feast Combo", "price": 320, "veg": False, "category": "Combos", "combo": True, "img": "https://images.unsplash.com/photo-1604908554161-4d6b32f8e04f"}
#     ]
#     if request.method == "POST":
#         order_name = request.form.get("order_name")
#         table_no = request.form.get("table_no")
#         action = request.form.get("action")
#         order = json.loads(request.form.get("order_data"))
#         for item in order.values():
#             item["status"] = "ORDERED"
#         order_total = sum(item["total"] for item in order.values())
#         print(order_name, order)
#         print("table_no:", table_no)
#         print("order_total :", order_total)
#         order_items_json = json.dumps(order)
#         if action == "submit":
#             session.setdefault("active_orders", {})
#             session["active_orders"][table_id] = order

#             session["order_name"] = order_name
            
#             query = "insert into food_order (table_id, Name, order_amount, order_items, order_type) values (%s, %s, %s, %s, %s)"
#             data = (table_no, order_name, order_total, order_items_json, "TABLE")
#             result = db.insert_data(query, data)
#             if result:
#                 session["js_alert"] = "Order Placed Successfully"
#                 order_id=fetch_order_id(table_no)
#                 query = "update Dine_Tables set table_status = %s where table_id = %s" 
#                 values = ("OCCUPIED", table_no)
#                 session["order"]["status"] = "Occupied"
#                 session["current_order"] = [{"table_id" : table_no, "order_id" : order_id, "order" : order}]
#                 db.update_data(query, values)
#                 return redirect(url_for('order_entry'))

#         elif action == "pay":
#             current = session.get("current_order")

#             if not current:
#                 session["js_alert"] = "No active order"
#                 return redirect(url_for("order_entry"))
            
#             current = current[0] 
#             order_id = current["order_id"]
#             table_id = current["table_id"]

#             if not can_pay_order(order_id):
#                 session["js_alert"] = "Order not fully served yet"
#                 return redirect(url_for("order_entry"))


#             db.update_data(
#                 "UPDATE Dine_Tables SET table_status='CLEANING', persons= %s WHERE table_id=%s",
#                 (0, table_id)
#             )

#             # session.clear()
#             session["js_alert"] = "Payment successful. Order closed."
#             return redirect(url_for('order_entry'))
#         if "active_orders" not in session:
#             session["active_orders"] = {}

#         session["active_orders"][table_id] = order
#         session.modified = True

#     # table_id = request.args.get("table")

#     # active_orders = session.get("active_orders", {})
#     # active_order = active_orders.get(table_id, {})
#     table_id = table_ctx["table"]
#     print("table_id : ", table_id)
#     return render_template("Order_Entry.html", order = table_id, foods = foods, active_order = active_order, person = order_person)

@app.route('/parcel', methods = ["GET", "POST"])
def parcel():
    foods = [
        # South Indian – Veg
        {"name": "Masala Dosa", "price": 120, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1600628422019-4b1ec7c85c10"},
        {"name": "Plain Dosa", "price": 90, "veg": True, "category": "South Indian", "img": "https://images.unsplash.com/photo-1668236544324-43a2c5c49f65"},
        {"name": "Idli (2 pcs)", "price": 60, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1589302168068-964664d93dc0"},
        {"name": "Vada (2 pcs)", "price": 70, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56"},
        {"name": "Pongal", "price": 80, "veg": True, "category": "South Indian", "img": "https://images.unsplash.com/photo-1600628422019-df1b5b2ddca5"},
        {"name": "Veg Meals", "price": 150, "veg": True, "category": "South Indian", "popular": True, "img": "https://images.unsplash.com/photo-1626509653291-57d9eaa6f0f2"},

        # Starters
        {"name": "Gobi 65", "price": 140, "veg": True, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1600628422020-6b43b0c2a2a1"},
        {"name": "Paneer 65", "price": 160, "veg": True, "category": "Starters", "img": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46"},
        {"name": "Chicken 65", "price": 180, "veg": False, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1604908554161-4d6b32f8e04f"},
        {"name": "Chicken Lollipop", "price": 220, "veg": False, "category": "Starters", "popular": True, "img": "https://images.unsplash.com/photo-1606756790138-261d2b21cd75"},

        # Main Course – Non Veg
        {"name": "Chicken Biryani", "price": 220, "veg": False, "category": "Main Course", "popular": True, "img": "https://images.unsplash.com/photo-1600628422019-4e4f3c0c33a3"},
        {"name": "Mutton Biryani", "price": 280, "veg": False, "category": "Main Course", "img": "https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a"},

        # Beverages
        {"name": "Filter Coffee", "price": 40, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1509042239860-f550ce710b93"},
        {"name": "Tea", "price": 30, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1511920170033-f8396924c348"},
        {"name": "Fresh Lime Soda", "price": 50, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1542444459-db5c1f1cbbf2"},
        {"name": "Butter Milk", "price": 30, "veg": True, "category": "Beverages", "img": "https://images.unsplash.com/photo-1626203050468-3d0c0f1e7d4f"},

        # Combos
        {"name": "Mini Tiffin Combo", "price": 160, "veg": True, "category": "Combos", "combo": True, "img": "https://images.unsplash.com/photo-1600628422019-0f8bdbf4f5bb"},
        {"name": "Chicken Feast Combo", "price": 320, "veg": False, "category": "Combos", "combo": True, "img": "https://images.unsplash.com/photo-1604908554161-4d6b32f8e04f"}
    ]    
    if request.method == "POST":
        order_name = request.form.get("order_name")
        action = request.form.get("action")
        order = json.loads(request.form.get("order_data"))
        order_total = sum(item["total"] for item in order.values())
        order_items_json = json.dumps(order)
        if action == "submit":
            session["active_order"] = order
            session["order_name"] = order_name
            order_type = request.form.get("order_mode")
            raw_mode = request.form.get("order_mode", "").upper()
            order_type = "ONLINE" if raw_mode == "ONLINE" else "PARCEL"
            print("order type : ", order_type)

            address =  request.form.get("delivery_address")
            parcel_id = random.randint(100, 999)
            query = "insert into food_order (table_id, Name, order_amount, order_items, order_type, delivery_address) values (%s,%s, %s, %s, %s, %s)"
            data = (parcel_id, order_name, order_total, order_items_json, order_type, address)
            result = db.insert_data(query, data)
            if result:
                order_id = fetch_order_id(parcel_id)
                session["js_alert"] = "Order Placed Successfully"
                # session["order"]["status"] = "Occupied"
                session["parcel_order"] = {
                    "order_id": order_id,
                    "customer": order_name,
                    "items": order,
                    "total": order_total,
                    "status": "OPEN"
                }
                return redirect(url_for('parcel'))

        elif action == "pay":
            current = session.get("parcel_order")
            if not current:
                session["js_alert"] = "No active order"
                return redirect(url_for("order_entry"))
            order_id = current["order_id"]

            if not can_pay_order(order_id):
                session["js_alert"] = "Order not fully served yet"
                return redirect(url_for("parcel"))

            session.clear()
            session["js_alert"] = "Payment successful. Order closed."
            return redirect(url_for('parcel'))

    return render_template("parcel.html", foods =foods, parcel=session.get("parcel_order")
)

@app.route('/table')
def table():
    return render_template("table.html")

@app.route('/distribution')
def distribution():
    fetched_orders = fetch_orders() 
    for order in fetched_orders:
        items = order.get("items", {})

        for item in items.values():
            item.setdefault("status", "ORDERED")
    print("fetched_orders :", fetched_orders)   
    # dq = session.get("distribution_queue", {})
    # print("DISTRIBUTION QUEUE:", dq)
    return render_template("Distribution.html", orders = fetched_orders)



@app.route('/kitchen')
def Kitchen():
    fetched_orders = fetch_orders()
    print("fetched_orders: ", fetched_orders)
    return render_template("kitchen.html", orders = fetched_orders)


@app.route("/kitchen/send-to-distribution", methods=["POST"])
def send_to_distribution():
    print("serve item called")
    data = request.json
    order_id = data["order_id"]
    item_name = data["item_name"]

    # fetch items
    query = "SELECT order_items FROM food_order WHERE order_id=%s"
    result = db.fetch_all_data(query, (order_id,))
    items = json.loads(result[0][0])

    # ensure status exists
    for item in items.values():
        item.setdefault("status", "ORDERED")

    # update clicked item
    items[item_name]["status"] = "READY"

    # check if all items are done
    all_done = all(
        item["status"] in ("READY", "CANCELLED")
        for item in items.values()
    )

    if all_done:
        db.update_data(
            "UPDATE food_order SET order_items=%s, order_status='DISTRIBUTION' WHERE order_id=%s",
            (json.dumps(items), order_id)
        )
        print("database updated for the order_status")
    else:
        db.update_data(
            "UPDATE food_order SET order_items=%s WHERE order_id=%s",
            (json.dumps(items), order_id)
        )

    return jsonify(success=True, moved_to_distribution=all_done)


@app.route("/distribution/serve-item", methods=["POST"])
def serve_item():
    data = request.json
    order_id = data["order_id"]
    item_name = data["item_name"]

    query = "SELECT order_items FROM food_order WHERE order_id=%s"
    result = db.fetch_all_data(query, (order_id,))
    items = json.loads(result[0][0])

    items[item_name]["status"] = "SERVED"

    db.update_data(
        "UPDATE food_order SET order_items=%s WHERE order_id=%s",
        (json.dumps(items), order_id)
    )

    # check if all served
    if all(i["status"] == "SERVED" or i["status"] == "CANCELLED"
           for i in items.values()):
        db.update_data(
            "UPDATE food_order SET order_status='DISTRIBUTED' WHERE order_id=%s",
            (order_id,)
        )

    return jsonify(success=True)



@app.route("/order/cancel-item", methods=["POST"])
def cancel_item_api():
    print("food canceled")
    data = request.json
    order_id = data["order_id"]
    item_name = data["item_name"]
    print("order_id ", order_id)
    print("item name", item_name)

    query = "SELECT order_items FROM food_order WHERE order_id=%s"
    result = db.fetch_all_data(query, (order_id,))
    if not result:
        return jsonify(success=False, msg="Order not found")

    items = json.loads(result[0][0])

    if item_name not in items:
        return jsonify(success=False, msg="Item not found")

    if items[item_name].get("status") == "served":
        return jsonify(success=False, msg="Item already served")

    items[item_name]["status"] = "CANCELLED"

    new_total = sum(
        i["total"] for i in items.values()
        if i.get("status") != "CANCELLED"
    )

    db.update_data(
        "UPDATE food_order SET order_items=%s, order_amount=%s WHERE order_id=%s",
        (json.dumps(items), new_total, order_id)
    )
    print("order removed from db")

    orders_by_table = session.get("orders_by_table", {})
    print("orders by table : ", orders_by_table)
    table_id = str(data.get("table_id") or data.get("table"))  
    print("table id ", table_id)
    if table_id in orders_by_table:
        session_order = orders_by_table[table_id]["order"]
        if item_name in session_order:
            session_order[item_name]["status"] = "CANCELLED"
            session.modified = True
            print("item removed from the session")

    return jsonify(success=True)

@app.route("/table/set-available", methods=["POST"])
def set_table_available():
    data = request.get_json()
    table_id = data.get("table_id")
    
    if not table_id:
        return {"success": False, "msg": "Table ID missing"}

    db.update_data("UPDATE Dine_Tables SET table_status='AVAILABLE', persons=0 WHERE table_id=%s", (table_id,))

    current_table = session.get("current_table")
    if current_table and current_table.get("table") == table_id:
        current_table["status"] = "AVAILABLE"
        session["current_table"] = current_table
        session.modified = True

    return {"success": True, "new_status": "AVAILABLE"}



@app.route("/clear-session")
def clear_session():
    session.clear()
    return "✅ Session cleared completely"


def insert_data(table_count):
    tables = table_count
    print(tables)
    for table_id in range(1, table_count + 1):
        query = "INSERT INTO Dine_Tables (table_id) VALUES (%s)"
        values = (table_id, )
        db.insert_data(query, values)

# insert_data(10)
def fetch_table_status():
    query = "Select table_id, table_status, persons from Dine_Tables"
    result = db.fetch_data_without_value(query)
    tables = []
    for r in result:
        tables.append({
            "id": r[0],
            "state": r[1].lower(),   # for CSS classes
            "persons": r[2]
        })
    # print(tables)
    return tables

def fetch_orders():
    query = "select * from food_order where order_status != 'DISTRIBUTED'"
    result = db.fetch_data_without_value(query)
    orders = []
    for order in result:
        orders.append({
            "order_id": order[0],
            "table_id": order[1],
            "name": order[2],
            "amount": order[3],
            "items": json.loads(order[4]),  
            "status": order[6],
            "order_type" : order[10],
            "address" : order[11]
        })
    return orders

def fetch_order_id(table_id):
    table_no = int(table_id)
    query = "select order_id from food_order where table_id = %s and order_status != 'DISTRIBUTED' order by order_id desc limit 1 "
    values = (table_no, )
    result = db.fetch_data(query, values)
    print("order id")
    print(result[0])
    if result[0]:
        return result[0]
    else: return None

def can_pay_order(order_id):
    query = """
        SELECT order_status 
        FROM food_order 
        WHERE order_id = %s
    """
    result = db.fetch_all_data(query, (order_id,))
    return result and result[0][0] == "DISTRIBUTED"


# fetch_order_id(1)
# fetch_table_status()
if __name__ == "__main__":
    app.run(debug=True)