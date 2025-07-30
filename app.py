from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from config import db_config

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['Product_Name']
        price = request.form['Price']
        brand = request.form['Brand']
        amount = request.form['Amount']
        supplier = request.form['ID_Supplier']
        category = request.form['ID_Category']

        conn = get_db_connection()
        cursor = conn.cursor()
        
        check_query = "SELECT * FROM Products WHERE Product_Name = %s"
        cursor.execute(check_query, (name,))
        existing = cursor.fetchone()

        if existing:
            # Producto existente → actualizar
            update_query = """
                UPDATE Products
                SET Amount = Amount + %s, Price = %s
                WHERE Product_Name = %s AND Brand = %s
            """
            values = (amount, price, name, brand)
            cursor.execute(update_query, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('add_product', updated='true'))

        # Producto nuevo → insertar
        insert_query = """
            INSERT INTO Products (Product_Name, Price, Brand, Amount, ID_Supplier, ID_Category)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (name, price, brand, amount, supplier, category)
        cursor.execute(insert_query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('add_product', added='true'))

    # GET: mostrar formulario
    updated = request.args.get('updated') == 'true'
    added = request.args.get('added') == 'true'
    return render_template('form.html', updated=updated, added=added)


@app.route('/delete/<int:product_id>')
def del_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Products WHERE ID_Product = %s", (product_id,))
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
        return redirect(url_for('index'))

    # GET: obtener los datos del producto y mostrar el formulario lleno
    cursor.execute("SELECT * FROM Products WHERE ID_Product = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit.html', product=product)



if __name__ == '__main__':
    app.run(debug=True)
