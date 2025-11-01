from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:14082002@localhost:5432/mymarket'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# MODELOS
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    fecha_registro = db.Column(db.Date, nullable=False)
    ubicacion = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    verificado = db.Column(db.Boolean, default=False)
    productos = db.relationship('Producto', backref='usuario', lazy=True)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    productos = db.relationship('Producto', backref='categoria', lazy=True)

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50))
    fecha_publicacion = db.Column(db.Date, nullable=False)
    fecha_creacion = db.Column(db.Date, nullable=False)
    imagenes = db.relationship('Imagen', backref='producto', lazy=True)
    comentarios = db.relationship('Comentario', backref='producto', lazy=True)
    resenas = db.relationship('Resena', backref='producto', lazy=True)
    ofertas = db.relationship('Oferta', backref='producto', lazy=True)
    pagos = db.relationship('Pago', backref='producto', lazy=True)
    transacciones = db.relationship('Transaccion', backref='producto', lazy=True)

class Imagen(db.Model):
    __tablename__ = 'imagenes'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    archivo = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    texto = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Resena(db.Model):
    __tablename__ = 'resenas'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    texto = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Oferta(db.Model):
    __tablename__ = 'ofertas'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    monto = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    monto = db.Column(db.Float)
    estado = db.Column(db.String(20))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Transaccion(db.Model):
    __tablename__ = 'transacciones'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    pago_id = db.Column(db.Integer, db.ForeignKey('pagos.id'))
    estado = db.Column(db.String(20))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Verificacion(db.Model):
    __tablename__ = 'verificaciones'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(50))
    valor = db.Column(db.String(100))
    verificado = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('index.html', productos=[])
    productos = Producto.query.order_by(Producto.fecha_publicacion.desc()).all()
    return render_template('index.html', productos=productos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        ubicacion = request.form.get('ubicacion')
        foto = request.files.get('foto')

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('El correo electrónico no es válido.')
            return redirect(url_for('register'))

        # Validar si el usuario o correo ya existen
        usuario_existente = Usuario.query.filter((Usuario.username == username) | (Usuario.email == email)).first()
        if usuario_existente:
            flash('El usuario o correo ya están registrados.')
            return redirect(url_for('register'))

        
        foto_filename = None
        if foto and foto.filename:
            foto_filename = foto.filename
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))

       
        nuevo_usuario = Usuario(
            username=username,
            password=generate_password_hash(password),
            email=email,
            ubicacion=ubicacion,
            fecha_registro=datetime.utcnow(),
            verificado=False
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
       

        flash('Usuario registrado exitosamente. Inicia sesión.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Bienvenido, ' + user.username)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.')
    return redirect(url_for('index'))

@app.route('/publicar', methods=['GET', 'POST'])
def publicar():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para publicar productos.')
        return redirect(url_for('login'))
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form.get('precio', 0)
        estado = request.form.get('estado', '')
        categoria_id = request.form.get('categoria', categorias[0].id if categorias else 1)
        producto = Producto(
            usuario_id=session['user_id'],
            categoria_id=categoria_id,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            estado=estado,
            fecha_publicacion=datetime.utcnow(),
            fecha_creacion=datetime.utcnow()
        )
        db.session.add(producto)
        db.session.commit()
        # Guardar imagen si se subió
        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename:
            filename = imagen_file.filename
            imagen_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagen = Imagen(producto_id=producto.id, usuario_id=session['user_id'], archivo=filename)
            db.session.add(imagen)
            db.session.commit()
        flash('Producto publicado exitosamente.')
        return redirect(url_for('index'))
    return render_template('publicar.html', categorias=categorias)

@app.route('/producto/<int:producto_id>', methods=['GET', 'POST'])
def producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if request.method == 'POST':
        if 'comentario' in request.form:
            texto = request.form['comentario']
            comentario = Comentario(producto_id=producto.id, usuario_id=session.get('user_id'), texto=texto)
            db.session.add(comentario)
            db.session.commit()
            flash('Comentario agregado.')
        elif 'resena' in request.form:
            texto = request.form['resena']
            resena = Resena(producto_id=producto.id, usuario_id=session.get('user_id'), texto=texto)
            db.session.add(resena)
            db.session.commit()
            flash('Reseña agregada.')
        elif 'oferta' in request.form:
            monto = float(request.form['oferta'])
            oferta = Oferta(producto_id=producto.id, usuario_id=session.get('user_id'), monto=monto)
            db.session.add(oferta)
            db.session.commit()
            flash('Oferta enviada.')
        elif 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen.filename:
                filename = imagen.filename
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen.save(path)
                img = Imagen(producto_id=producto.id, usuario_id=session.get('user_id'), archivo=filename)
                db.session.add(img)
                db.session.commit()
                flash('Imagen subida.')
        elif 'pago' in request.form:
            monto = float(request.form['pago'])
            pago = Pago(producto_id=producto.id, usuario_id=session.get('user_id'), monto=monto, estado='Pagado')
            db.session.add(pago)
            db.session.commit()
            flash('Pago realizado.')
    comentarios = Comentario.query.filter_by(producto_id=producto.id).order_by(Comentario.fecha.desc()).all()
    resenas = Resena.query.filter_by(producto_id=producto.id).order_by(Resena.fecha.desc()).all()
    imagenes = Imagen.query.filter_by(producto_id=producto.id).order_by(Imagen.fecha.desc()).all()
    ofertas = Oferta.query.filter_by(producto_id=producto.id).order_by(Oferta.fecha.desc()).all()
    pagos = Pago.query.filter_by(producto_id=producto.id).order_by(Pago.fecha.desc()).all()
    return render_template('producto.html', producto=producto, comentarios=comentarios, resenas=resenas, imagenes=imagenes, ofertas=ofertas, pagos=pagos)

@app.route('/historial')
def historial():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tu historial.')
        return redirect(url_for('login'))
    productos = Producto.query.filter_by(usuario_id=session['user_id']).all()
    return render_template('historial.html', productos=productos)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, host='0.0.0.0')
