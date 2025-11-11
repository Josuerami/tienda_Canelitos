from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, send_from_directory
import pymysql
import os
import io
import csv
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = 'canelitos_secret_key'

def get_db():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'tienda_canelitos'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def require_role(*roles):
    def wrapper(f):
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash("Acceso denegado.")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return wrapper

# === LOGIN ===
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Si ya hay una sesión activa, redirigir a home
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('user', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        
        if not all([username, name, password]):
            flash('Todos los campos son obligatorios')
            return render_template('register.html')
            
        conn = get_db()
        try:
            with conn.cursor() as cur:
                # Verificar si el usuario ya existe
                cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                if cur.fetchone():
                    flash('Este usuario o email ya está registrado')
                    return render_template('register.html')
                    
                # Crear nuevo usuario como cliente
                hashed_password = generate_password_hash(password)
                cur.execute("""
                    INSERT INTO users (username, name, password, email, role, active, created_at)
                    VALUES (%s, %s, %s, %s, 'client', 1, NOW())
                """, (username, name, hashed_password, email))
            conn.commit()
            flash('Cuenta creada exitosamente')
            return redirect(url_for('login'))
        except Exception as e:
            print("Error en registro:", str(e))
            flash('Error al crear la cuenta')
            conn.rollback()
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya hay una sesión activa, redirigir a home
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        user = request.form.get('user', '').strip()
        pwd = request.form.get('password', '').strip()
        
        if not user or not pwd:
            flash("Por favor ingresa usuario y contraseña")
            return render_template('login.html')
            
        conn = get_db()
        try:
            with conn.cursor() as cur:
                # Buscar usuario activo
                cur.execute("""
                    SELECT id, username, name, role, active, password, email
                    FROM users 
                    WHERE username = %s AND active = 1
                """, (user,))
                u = cur.fetchone()
                
                if u and check_password_hash(u['password'], pwd):
                    # Usuario existe y está activo
                    session.clear()
                    session['user_id'] = u['id']
                    session['user'] = u['username']
                    session['user_name'] = u['name']
                    session['user_role'] = u.get('role', 'client')
                    session['user_email'] = u.get('email')
                    session['cart'] = []  # Inicializar carrito vacío
                    
                    # Registrar el login exitoso
                    cur.execute("""
                        INSERT INTO login_history (user_id, login_date) 
                        VALUES (%s, NOW())
                    """, (u['id'],))
                    conn.commit()
                    
                    # Redirigir a home (que ya maneja la redirección por rol)
                    return redirect(url_for('home'))
                    
            flash("Usuario o contraseña incorrectos")
        except Exception as e:
            print("Error en login:", str(e))
            flash("Error al iniciar sesión. Por favor, intenta de nuevo.")
            conn.rollback()
        finally:
            conn.close()

# === HOME (redirige por rol) ===
@app.route('/home')
def home():
    if 'user_role' not in session:
        return redirect(url_for('login'))
        
    # Redirigir según el rol del usuario
    role = session.get('user_role', 'client')
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'seller':
        return redirect(url_for('seller_dashboard'))
    elif role == 'delivery':
        return redirect(url_for('delivery_orders'))
    
    # Para clientes, mostrar productos
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, price, category, stock, image 
                FROM products 
                WHERE stock > 0
                ORDER BY category, name
            """)
            products = cur.fetchall()
            
            # Asegurar que image tenga un valor válido
            for p in products:
                if not p.get('image'):
                    p['image'] = 'placeholder.svg'
                    
        return render_template('home.html', 
                             products=products,
                             user=session.get('user'),
                             user_name=session.get('user_name'))
    except Exception as e:
        print("Error en home:", str(e))
        flash("Error al cargar productos")
        return render_template('home.html', products=[])
    finally:
        conn.close()

# === CLIENTE: PRODUCTOS Y CARRITO ===
@app.route('/product/<int:pid>')
@require_role('client')
def product_detail(pid):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
        product = cur.fetchone()
    conn.close()
    if not product:
        flash("Producto no encontrado")
        return redirect(url_for('home'))
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart/<int:pid>')
@require_role('client')
def add_to_cart(pid):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products WHERE id = %s AND stock > 0", (pid,))
        p = cur.fetchone()
    conn.close()
    if p:
        session.setdefault('cart', []).append({'id': p['id'], 'name': p['name'], 'price': float(p['price'])})
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart')
@require_role('client')
def cart():
    items = session.get('cart', [])
    total = sum(item['price'] for item in items)
    return render_template('cart.html', cart=items, total=total)

@app.route('/cart/remove/<int:index>', methods=['POST'])
@require_role('client')
def cart_remove(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart/clear', methods=['POST'])
@require_role('client')
def cart_clear():
    session['cart'] = []
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@require_role('client')
def checkout():
    if not session.get('user_id'):
        flash("Por favor inicia sesión para completar la compra")
        return redirect(url_for('login'))
        
    cart = session.get('cart', [])
    method = request.form.get('payment_method')
    delivery_address = request.form.get('delivery_address', '').strip()
    
    if not cart:
        flash("El carrito está vacío")
        return redirect(url_for('cart'))
    if not method:
        flash("Por favor selecciona un método de pago")
        return redirect(url_for('cart'))
    if not delivery_address:
        flash("Por favor ingresa una dirección de entrega")
        return redirect(url_for('cart'))
    
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Calcular total final
            total_order = sum(item['price'] for item in cart)
            
            # Crear orden maestra
            cur.execute("""
                INSERT INTO orders_master (
                    user_id, total_amount, payment_method, 
                    delivery_address, status, created_at
                )
                VALUES (%s, %s, %s, %s, 'Pendiente', NOW())
            """, (session['user_id'], total_order, method, delivery_address))
            master_id = cur.lastrowid
            
            # Verificar y procesar cada item
            items_processed = []
            try:
                for item in cart:
                    # Verificar stock en tiempo real
                    cur.execute("""
                        SELECT id, name, stock, price 
                        FROM products 
                        WHERE id = %s
                        FOR UPDATE
                    """, (item['id'],))
                    product = cur.fetchone()
                    
                    if not product:
                        raise Exception(f"Producto {item['name']} no encontrado")
                    if product['stock'] < 1:
                        raise Exception(f"Producto {item['name']} sin stock")
                    if abs(float(product['price']) - float(item['price'])) > 0.01:
                        raise Exception(f"El precio de {item['name']} ha cambiado")
                    
                    # Insertar detalle de orden
                    cur.execute("""
                        INSERT INTO order_details (
                            order_id, product_id, quantity, 
                            unit_price, total_price
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (master_id, item['id'], 1, 
                         product['price'], product['price']))
                    
                    # Actualizar stock
                    cur.execute("""
                        UPDATE products 
                        SET stock = stock - 1,
                            updated_at = NOW()
                        WHERE id = %s AND stock > 0
                    """, (item['id'],))
                    
                    if cur.rowcount == 0:
                        raise Exception(f"No se pudo actualizar stock de {item['name']}")
                    
                    items_processed.append(item['id'])
                
                # Todo ok - confirmar transacción
                conn.commit()
                session['cart'] = []
                flash("¡Compra confirmada! Gracias por tu pedido.")
                
            except Exception as e:
                # Si algo falla, revertir cambios en los items procesados
                for pid in items_processed:
                    cur.execute("""
                        UPDATE products 
                        SET stock = stock + 1
                        WHERE id = %s
                    """, (pid,))
                raise e
                
    except Exception as e:
        print("Error en checkout:", str(e))
        conn.rollback()
        flash(str(e))
        return redirect(url_for('cart'))
    finally:
        conn.close()
    return redirect(url_for('home'))

# === ADMIN ===
@app.route('/admin')
@require_role('admin')
def admin_dashboard():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) AS ventas FROM orders_master WHERE DATE(created_at) = CURDATE()")
        ventas = cur.fetchone()['ventas']
        cur.execute("SELECT COUNT(*) AS tickets FROM orders_master WHERE DATE(created_at) = CURDATE()")
        tickets = cur.fetchone()['tickets']
        cur.execute("SELECT COUNT(*) AS empleados FROM users WHERE role IN ('seller','delivery') AND active = 1")
        empleados = cur.fetchone()['empleados']
    conn.close()
    return render_template('admin/dashboard.html', ventas=ventas, tickets=tickets, empleados=empleados)

@app.route('/admin/users')
@require_role('admin')
def admin_users():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE role != 'admin'")
        users = cur.fetchall()
    conn.close()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@require_role('admin')
def admin_create_user():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        if role not in ['client', 'seller', 'delivery']:
            flash("Rol inválido.")
            return redirect(url_for('admin_create_user'))
        conn = get_db()
        try:
            with conn.cursor() as cur:
                hashed_password = generate_password_hash(password)
                cur.execute("INSERT INTO users (username, name, password, role) VALUES (%s, %s, %s, %s)",
                           (username, name, hashed_password, role))
            conn.commit()
            flash("Usuario creado.")
            return redirect(url_for('admin_users'))
        except:
            flash("Error: usuario ya existe.")
        finally:
            conn.close()
    return render_template('admin/create_user.html')

@app.route('/admin/products')
@require_role('admin', 'seller')
def admin_products():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM products")
        products = cur.fetchall()
    conn.close()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/create', methods=['GET', 'POST'])
@require_role('admin', 'seller')
def admin_create_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        stock = request.form['stock']
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO products (name, price, category, stock, image)
                    VALUES (%s, %s, %s, %s, 'placeholder.svg')
                """, (name, price, category, stock))
            conn.commit()
            flash("Producto creado.")
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash("Error al crear producto.")
        finally:
            conn.close()
    return render_template('admin/create_product.html')

@app.route('/admin/orders')
@require_role('admin', 'seller', 'delivery')
def admin_orders():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT o.*, u.name as cliente, p.name as producto
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN products p ON o.product_id = p.id
            ORDER BY o.created_at DESC
        """)
        orders = cur.fetchall()
    conn.close()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/update/<int:oid>', methods=['POST'])
@require_role('admin', 'seller', 'delivery')
def update_order_status(oid):
    status = request.form['status']
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("UPDATE orders_master SET status = %s WHERE id = %s", (status, oid))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_orders'))

@app.route('/admin/report')
@require_role('admin')
def admin_report():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT om.created_at, u.name as cliente, om.total_amount as total, om.payment_method
            FROM orders_master om
            JOIN users u ON om.user_id = u.id
            WHERE DATE(om.created_at) = CURDATE()
        """)
        orders = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Cliente', 'Total', 'Método de Pago'])
    for o in orders:
        writer.writerow([o['created_at'], o['cliente'], o['total'], o['payment_method']])
    output.seek(0)

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='reporte_ventas.csv')

# === VENDEDOR ===
@app.route('/seller')
@require_role('seller')
def seller_dashboard():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) AS ventas FROM orders_master WHERE DATE(created_at) = CURDATE()")
        ventas = cur.fetchone()['ventas']
        cur.execute("SELECT COUNT(*) AS tickets FROM orders_master WHERE DATE(created_at) = CURDATE()")
        tickets = cur.fetchone()['tickets']
    conn.close()
    return render_template('seller/dashboard.html', ventas=ventas, tickets=tickets)

# === REPARTIDOR ===
@app.route('/delivery')
@require_role('delivery')
def delivery_orders():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT om.*, u.name as cliente
            FROM orders_master om
            JOIN users u ON om.user_id = u.id
            WHERE om.status IN ('Pendiente', 'En camino')
            ORDER BY om.created_at DESC
        """)
        orders = cur.fetchall()

        # Obtener detalles de cada orden
        for order in orders:
            cur.execute("""
                SELECT od.*, p.name as product_name
                FROM order_details od
                JOIN products p ON od.product_id = p.id
                WHERE od.order_id = %s
            """, (order['id'],))
            order['details'] = cur.fetchall()

    conn.close()
    return render_template('delivery/orders.html', orders=orders)

# === PERFIL ===
@app.route('/profile')
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Obtener datos del usuario
            cur.execute("""
                SELECT id, username, name, email, role, created_at
                FROM users
                WHERE id = %s
            """, (session['user_id'],))
            user = cur.fetchone()
            
            if not user:
                session.clear()
                return redirect(url_for('login'))
            
            # Obtener pedidos del usuario
            cur.execute("""
                SELECT om.*, 
                       CASE 
                           WHEN om.status = 'Pendiente' THEN 'warning'
                           WHEN om.status = 'En Proceso' THEN 'info'
                           WHEN om.status = 'En Camino' THEN 'primary'
                           WHEN om.status = 'Entregado' THEN 'success'
                           WHEN om.status = 'Cancelado' THEN 'danger'
                           ELSE 'secondary'
                       END as status_color
                FROM orders_master om
                WHERE om.user_id = %s
                ORDER BY om.created_at DESC
            """, (session['user_id'],))
            orders = cur.fetchall()
            
            # Obtener detalles de cada orden
            for order in orders:
                cur.execute("""
                    SELECT od.*, p.name as product_name
                    FROM order_details od
                    JOIN products p ON od.product_id = p.id
                    WHERE od.order_id = %s
                """, (order['id'],))
                order['details'] = cur.fetchall()
                
        return render_template('profile.html',
                             user=user,
                             orders=orders)
                             
    except Exception as e:
        print("Error en profile:", str(e))
        flash("Error al cargar datos del perfil")
        return redirect(url_for('home'))
    finally:
        conn.close()

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    contact = request.form.get('contact', '').strip()
    
    if not name or not email:
        flash("Nombre y email son obligatorios")
        return redirect(url_for('profile'))
        
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Verificar si el email ya existe
            cur.execute("""
                SELECT id FROM users 
                WHERE email = %s AND id != %s
            """, (email, session['user_id']))
            if cur.fetchone():
                flash("Este email ya está registrado")
                return redirect(url_for('profile'))
            
            # Actualizar datos
            cur.execute("""
                UPDATE users 
                SET name = %s, email = %s, contact = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (name, email, contact, session['user_id']))
            
        conn.commit()
        session['user_name'] = name
        flash("Perfil actualizado exitosamente")
        
    except Exception as e:
        print("Error al actualizar perfil:", str(e))
        flash("Error al actualizar el perfil")
        conn.rollback()
        
    finally:
        conn.close()
        
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# === SERVICIO DE IMÁGENES ===
@app.route('/img/<path:filename>')
def img(filename):
    if '..' in filename:
        return "Invalid path", 400
    return send_file(os.path.join('static', 'img', filename))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)