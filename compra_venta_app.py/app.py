from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

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
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    ubicacion = db.Column(db.String(100))
    fecha_registro = db.Column(db.Date, default=datetime.utcnow)
    verificado = db.Column(db.Boolean, default=False)
    productos = db.relationship('Producto', backref='usuario', lazy=True)
    comentarios = db.relationship('Comentario', backref='usuario', lazy=True)
    resenas = db.relationship('Resena', backref='usuario', lazy=True)
    imagenes = db.relationship('Imagen', backref='usuario', lazy=True)
    ofertas = db.relationship('Oferta', backref='usuario', lazy=True)
    pagos = db.relationship('Pago', backref='usuario', lazy=True)
    transacciones_comprador = db.relationship('Transaccion', foreign_keys='Transaccion.comprador_id', backref='comprador', lazy=True)
    transacciones_vendedor = db.relationship('Transaccion', foreign_keys='Transaccion.vendedor_id', backref='vendedor', lazy=True)
    verificaciones = db.relationship('Verificacion', backref='usuario', lazy=True)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    productos = db.relationship('Producto', backref='categoria', lazy=True)

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10,2), nullable=False)
    estado = db.Column(db.String(50))
    fecha_publicacion = db.Column(db.Date, default=datetime.utcnow)
    fecha_creacion = db.Column(db.Date, default=datetime.utcnow)
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
    archivo = db.Column(db.String(255))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Resena(db.Model):
    __tablename__ = 'resenas'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Oferta(db.Model):
    __tablename__ = 'ofertas'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    monto = db.Column(db.Numeric(10,2), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    monto = db.Column(db.Numeric(10,2), nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Transaccion(db.Model):
    __tablename__ = 'transacciones'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    pago_id = db.Column(db.Integer, db.ForeignKey('pagos.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='En proceso')

class Verificacion(db.Model):
    __tablename__ = 'verificaciones'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.String(255))
    verificado = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# RUTAS PRINCIPALES
@app.route('/')
def index():
    productos = Producto.query.order_by(Producto.fecha_publicacion.desc()).all()
    return render_template('index.html', productos=productos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        ubicacion = request.form['ubicacion']
        if Usuario.query.filter_by(username=username).first():
            flash('El usuario ya existe.')
            return redirect(url_for('register'))
        user = Usuario(
            username=username,
            password=password,
            email=email,
            ubicacion=ubicacion,
            fecha_registro=datetime.utcnow(),
            verificado=False
        )
        db.session.add(user)
        db.session.commit()
        flash('Usuario registrado exitosamente. Inicia sesión.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username, password=password).first()
        if user:
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
        precio = request.form['precio']
        estado = request.form['estado']
        categoria_id = int(request.form['categoria'])
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
        flash('Producto publicado exitosamente.')
        return redirect(url_for('index'))
    return render_template('publicar.html', categorias=categorias)

@app.route('/producto/<int:producto_id>', methods=['GET', 'POST'])
def producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    if request.method == 'POST':
        if 'comentario' in request.form:
            texto = request.form['comentario']
            comentario = Comentario(producto_id=producto.id, usuario_id=session['user_id'], texto=texto)
            db.session.add(comentario)
            db.session.commit()
            flash('Comentario agregado.')
        elif 'resena' in request.form:
            texto = request.form['resena']
            resena = Resena(producto_id=producto.id, usuario_id=session['user_id'], texto=texto)
            db.session.add(resena)
            db.session.commit()
            flash('Reseña agregada.')
        elif 'oferta' in request.form:
            monto = request.form['oferta']
            oferta = Oferta(producto_id=producto.id, usuario_id=session['user_id'], monto=monto)
            db.session.add(oferta)
            db.session.commit()
            flash('Oferta enviada.')
        elif 'pago' in request.form:
            monto = request.form['pago']
            pago = Pago(producto_id=producto.id, usuario_id=session['user_id'], monto=monto, estado='Pagado')
            db.session.add(pago)
            db.session.commit()
            transaccion = Transaccion(producto_id=producto.id, comprador_id=session['user_id'], vendedor_id=producto.usuario_id, pago_id=pago.id, estado='Completada')
            db.session.add(transaccion)
            db.session.commit()
            flash('Pago realizado y transacción registrada.')
        elif 'imagen' in request.files:
            archivo = request.files['imagen']
            if archivo.filename:
                filename = archivo.filename
                archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagen = Imagen(producto_id=producto.id, usuario_id=session['user_id'], archivo=filename)
                db.session.add(imagen)
                db.session.commit()
                flash('Imagen subida.')
        elif 'verificacion_tipo' in request.form:
            tipo = request.form['verificacion_tipo']
            valor = request.form['verificacion_valor']
            verificacion = Verificacion(usuario_id=session['user_id'], tipo=tipo, valor=valor, verificado=True)
            db.session.add(verificacion)
            db.session.commit()
            flash('Verificación registrada.')
        return redirect(url_for('producto', producto_id=producto.id))
    comentarios = Comentario.query.filter_by(producto_id=producto.id).order_by(Comentario.fecha).all()
    resenas = Resena.query.filter_by(producto_id=producto.id).order_by(Resena.fecha).all()
    imagenes = Imagen.query.filter_by(producto_id=producto.id).order_by(Imagen.fecha).all()
    ofertas = Oferta.query.filter_by(producto_id=producto.id).order_by(Oferta.fecha).all()
    pagos = Pago.query.filter_by(producto_id=producto.id).order_by(Pago.fecha).all()
    transacciones = Transaccion.query.filter_by(producto_id=producto.id).order_by(Transaccion.fecha).all()
    return render_template('producto.html', producto=producto, categorias=categorias, comentarios=comentarios, resenas=resenas, imagenes=imagenes, ofertas=ofertas, pagos=pagos, transacciones=transacciones)

@app.route('/historial')
def historial():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tu historial.')
        return redirect(url_for('login'))
    usuario = Usuario.query.get(session['user_id'])
    productos = Producto.query.filter_by(usuario_id=usuario.id).all()
    comentarios = Comentario.query.filter_by(usuario_id=usuario.id).all()
    resenas = Resena.query.filter_by(usuario_id=usuario.id).all()
    imagenes = Imagen.query.filter_by(usuario_id=usuario.id).all()
    ofertas = Oferta.query.filter_by(usuario_id=usuario.id).all()
    pagos = Pago.query.filter_by(usuario_id=usuario.id).all()
    transacciones = Transaccion.query.filter((Transaccion.comprador_id==usuario.id)|(Transaccion.vendedor_id==usuario.id)).all()
    verificaciones = Verificacion.query.filter_by(usuario_id=usuario.id).all()
    return render_template('historial.html', usuario=usuario, productos=productos, comentarios=comentarios, resenas=resenas, imagenes=imagenes, ofertas=ofertas, pagos=pagos, transacciones=transacciones, verificaciones=verificaciones)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
