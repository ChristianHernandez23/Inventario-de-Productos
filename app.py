from flask import Flask, flash,render_template, request, redirect, url_for
import mysql.connector
from config import db_config
import secrets


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/view/<string:view_id>/', defaults={'order_id': None})
@app.route('/view/<string:view_id>/<int:order_id>')
def view(view_id, order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if view_id == "pro":
        cursor.execute("SELECT * FROM products")
        table = cursor.fetchall()

    elif view_id == "sup":
        cursor.execute("SELECT * FROM suppliers")
        table = cursor.fetchall()

    elif view_id == "cus":
        cursor.execute("SELECT * FROM customers")
        table = cursor.fetchall()

    elif view_id == "ord":
        cursor.execute("SELECT * FROM orders")
        table = cursor.fetchall()

    elif view_id == "ord_it" and order_id is not None:
        cursor.execute("""
            SELECT o.id_order, p.id_product, p.product_name, p.brand, o.order_date, i.quantity, i.price 
            FROM orders o 
            JOIN order_items i ON o.id_order = i.id_order 
            JOIN products p ON i.id_product = p.id_product
            WHERE o.id_order = %s
        """, (order_id,))
        table = cursor.fetchall()
    else:
        table = []  # En caso de error o view_id inválido

    cursor.close()
    conn.close()
    return render_template('show.html', table=table, flag=view_id)



@app.route('/add/<string:add_id>', methods=['GET', 'POST'])
def add_product(add_id):
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        if add_id == "product":
            name = request.form['Product_Name']
            price = request.form['Price']
            quantity = request.form['Quantity']
            brand = request.form['Brand']
            supplier = request.form['ID_Supplier']
            category = request.form['ID_Category']
            # Verificar si ya existe el producto
            check_query = "SELECT * FROM products WHERE product_name = %s AND brand = %s"
            cursor.execute(check_query, (name, brand))
            existing = cursor.fetchone()

            if existing:
                # Actualizar producto existente
                flash(f"El producto {name} de {brand} ya existía, se actualizó la cantidad y el precio.", "warning")

                update_query = """
                    UPDATE products
                    SET quantity = quantity + %s, price = %s
                    WHERE product_name = %s AND brand = %s
                """
                values = (quantity, price, name, brand)
                cursor.execute(update_query, values)
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for('add_product', add_id=add_id, updated=True))

            # Insertar nuevo producto
            insert_query = """
                INSERT INTO products (product_name, price, quantity, brand, id_category, id_supplier)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (name, price, quantity, brand, category, supplier)
            cursor.execute(insert_query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('add_product', add_id=add_id, added=True))

        elif add_id == "supplier" or add_id =='customers':
            first_name = request.form['First_Name']
            last_name = request.form['Last_Name']
            phone = request.form['Phone']
            email = request.form['Email']
            street = request.form['Street']
            city = request.form['City']
            state = request.form['State']
            zip_c = request.form['Zip_code']

            # Verificar si ya existe el proveedor

            check_query = "SELECT * FROM suppliers WHERE first_name = %s AND last_name = %s"

            if add_id=='customers':
                check_query = "SELECT * FROM customers WHERE first_name = %s AND last_name = %s"
            cursor.execute(check_query, (first_name, last_name))
            existing = cursor.fetchone()

            if existing:
                flash(f"El registro con el nombre {first_name} {last_name} ya existía.", "warning")
                cursor.close()
                conn.close()
                return redirect(url_for('add_product', add_id=add_id, updated=True))

            # Insertar nuevo proveedor
            insert_query = """
                INSERT INTO suppliers (first_name, last_name, phone, email, street, city, state, zip_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            if add_id=='customers':
                insert_query = """
                    INSERT INTO customers (first_name, last_name, phone, email, street, city, state, zip_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
            values = (first_name, last_name, phone, email, street, city, state, zip_c)
            cursor.execute(insert_query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('add_product', add_id=add_id, added=True))
        elif add_id == 'orders':
            id_customer = request.form.get('id_customer')

            raw_data = request.form.to_dict(flat=False)
            products = []
            index = 0
            while f'products[{index}][id_product]' in raw_data:
                products.append({
                    'id_product': int(raw_data[f'products[{index}][id_product]'][0]),
                    'quantity': int(raw_data[f'products[{index}][quantity]'][0]),
                    'price': float(raw_data[f'products[{index}][price]'][0])
                })
                index += 1

            if not id_customer or not products:
                flash("Datos incompletos", "danger")
                return redirect(url_for('add_product', add_id='orders'))

            # Totales
            total_qty = sum(p['quantity'] for p in products)
            total_price = sum(p['quantity'] * p['price'] for p in products)

            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar orden
            cursor.execute(
                "INSERT INTO orders (id_customer, total_quantity, total_price) VALUES (%s, %s, %s)",
                (id_customer, total_qty, total_price)
            )
            id_order = cursor.lastrowid

            # Insertar productos y actualizar stock
            for p in products:
                cursor.execute(
                    "INSERT INTO order_items (id_order, id_product, quantity, price) VALUES (%s, %s, %s, %s)",
                    (id_order, p['id_product'], p['quantity'], p['price'])
                )
                cursor.execute(
                    "UPDATE products SET quantity = quantity - %s WHERE id_product = %s",
                    (p['quantity'], p['id_product'])
                )

            conn.commit()
            cursor.close()
            conn.close()

            flash("Orden creada exitosamente", "success")
            return redirect(url_for('add_product', add_id='orders', added=True))

    # GET
    if add_id == "product":
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_supplier, first_name, last_name FROM suppliers")
        suppliers = cursor.fetchall()
        cursor.execute("SELECT id_category, category_name FROM categories")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()

        updated = request.args.get('updated') == True
        added = request.args.get('added') == True

        return render_template('form.html', updated=updated, added=added, add_id=add_id, suppliers=suppliers, categories=categories)

    elif add_id == "supplier" or add_id == 'customers':
        updated = request.args.get('updated') == True
        added = request.args.get('added') == True
        if add_id =='customers':
            add_id='customers'
        return render_template('form.html', updated=updated, added=added, add_id=add_id)
    elif add_id=="orders":
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_customer, first_name, last_name FROM customers")
        customers = cursor.fetchall()
        cursor.execute("SELECT id_product, product_name,brand,price,quantity FROM products")
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        updated = request.args.get('updated') == True
        added = request.args.get('added') == True
        return render_template('form.html',updated=updated,added=added,add_id=add_id,customers=customers,products=products)


@app.route('/delete/<string:del_id>/<int:id_d>')
def del_product(del_id,id_d):
    conn = get_db_connection()
    cursor = conn.cursor()
    if del_id=="products":
        cursor.execute("DELETE FROM products WHERE id_product = %s", (id_d,))
    elif del_id=="suppliers":
        cursor.execute("DELETE FROM suppliers WHERE id_supplier = %s", (id_d,))
    elif del_id=="customers":
        cursor.execute("DELETE FROM customers WHERE id_customer = %s", (id_d,))
    elif del_id=="orders":
        cursor.execute("DELETE FROM order_items WHERE id_order = %s", (id_d,))
        cursor.execute("DELETE FROM orders WHERE id_order = %s", (id_d,))
    elif del_id=="order_items":
        cursor.execute("DELETE FROM order_items WHERE id_product=%s", (id_d,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Obtener los datos del formulario editado
        name = request.form['Product_Name']
        price = request.form['Price']
        brand = request.form['Brand']
        amount = request.form['Amount']
        supplier = request.form['ID_Supplier']
        category = request.form['ID_Category']

        # Actualizar en la base de datos
        update_query = """
            UPDATE Products
            SET Product_Name=%s, Price=%s, Brand=%s, Amount=%s,
                ID_Supplier=%s, ID_Category=%s
            WHERE ID_Product = %s
        """
        values = (name, price, brand, amount, supplier, category, product_id)
        cursor.execute(update_query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('products'))

    # GET: obtener los datos del producto y mostrar el formulario lleno
    cursor.execute("SELECT * FROM Products WHERE ID_Product = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit.html', product=product)


if __name__ == '__main__':
    app.run(debug=True)
