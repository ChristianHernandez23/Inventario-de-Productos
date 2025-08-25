from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from config import db_config

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('show.html', products=products,pro=True)
@app.route('/suppliers')
def suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM suppliers")
    suppliers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('show.html',suppliers=suppliers,sup=True)
@app.route('/customers')
def customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('show.html',customers=customers,cus=True)
@app.route('/orders')
def orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('show.html',orders=orders,ord=True)

@app.route('/add/<string:add_id>', methods=['GET', 'POST'])
def add_product(add_id):
    if request.method == 'POST':
        if add_id == "product":
            name = request.form['Product_Name']
            price = request.form['Price']
            quantity = request.form['Quantity']
            brand = request.form['Brand']
            supplier = request.form['ID_Supplier']
            category = request.form['ID_Category']

            conn = get_db_connection()
            cursor = conn.cursor()

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

        elif add_id == "supplier":
            first_name = request.form['First_Name']
            last_name = request.form['Last_Name']
            phone = request.form['Phone']
            email = request.form['Email']
            street = request.form['Street']
            city = request.form['City']
            state = request.form['State']
            zip_c = request.form['Zip_code']

            conn = get_db_connection()
            cursor = conn.cursor()

            # Verificar si ya existe el proveedor
            check_query = "SELECT * FROM suppliers WHERE first_name = %s AND last_name = %s"
            cursor.execute(check_query, (first_name, last_name))
            existing = cursor.fetchone()

            if existing:
                flash(f"El proveedor {first_name} {last_name} ya existía.", "warning")
                cursor.close()
                conn.close()
                return redirect(url_for('add_product', add_id=add_id, updated=True))

            # Insertar nuevo proveedor
            insert_query = """
                INSERT INTO suppliers (first_name, last_name, phone, email, street, city, state, zip_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (first_name, last_name, phone, email, street, city, state, zip_c)
            cursor.execute(insert_query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('add_product', add_id=add_id, added=True))

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

        return render_template('form.html', updated=updated, added=added, pro=True, suppliers=suppliers, categories=categories)

    elif add_id == "supplier":
        updated = request.args.get('updated') == True
        added = request.args.get('added') == True
        return render_template('form.html', updated=updated, added=added, sup=True)


@app.route('/delete/<string:del_id>/<int:id_d>')
def del_product(del_id,id_d):
    conn = get_db_connection()
    cursor = conn.cursor()
    if del_id=="product":
        cursor.execute("DELETE FROM products WHERE id_product = %s", (id_d,))
    elif del_id=="supplier":
        cursor.execute("DELETE FROM suppliers WHERE id_supplier = %s", (id_d,))
    elif del_id=="customer":
        cursor.execute("DELETE FROM customers WHERE id_customer = %s", (id_d,))
    elif del_id=="orders":
        cursor.execute("DELETE FROM orders WHERE id_order = %s", (id_d,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('products'))

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
