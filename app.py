from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime

app = Flask(__name__)

# Configuración de la base de datos
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mi_clave_secreta'

db = SQLAlchemy(app)

# Modelo Cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    tipo_identificacion = db.Column(db.String(50), nullable=False)
    numero_identificacion = db.Column(db.String(50), unique=True, nullable=False)
    celular = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(50), nullable=True)
    tareas = db.relationship('Tarea', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

# Modelo Tarea
class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    completado = db.Column(db.Boolean, default=False)
    estado = db.Column(db.String(50), nullable=False, default='Pendiente')
    valor = db.Column(db.String(50), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)

    def __repr__(self):
        return f'<Tarea {self.descripcion}>'

# Función para enviar el correo
def enviar_correos_a_clientes(clientes):
    # Configura tu servidor SMTP aquí
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'crmprueba60@gmail.com'
    smtp_password = 'dxuh lwzy qgkb ilnw'  # Cambia esto a un valor más seguro

    for cliente in clientes:
        if cliente.estado in ['Frío', 'Interesado']:
            mensaje = EmailMessage()
            mensaje['Subject'] = '¡Hola! Queremos saber de ti'
            mensaje['From'] = smtp_user
            mensaje['To'] = cliente.email
            mensaje.set_content(f"Hola {cliente.nombre},\n\nQueremos saber más sobre tu interés.\n\nSaludos.")

            try:
                with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(smtp_user, smtp_password)
                    smtp.send_message(mensaje)
                print(f"Correo enviado a {cliente.email}")
            except Exception as e:
                print(f"Error al enviar correo a {cliente.email}: {e}")

# Ruta principal
@app.route('/')
def index():
    clientes = Cliente.query.all()
    return render_template('index.html', clientes=clientes)

# Ruta para enviar correos a clientes fríos o interesados
@app.route('/enviar_correos', methods=['POST'])
def enviar_correos():
    clientes = Cliente.query.filter(Cliente.estado.in_(['Frío', 'Interesado'])).all()
    enviar_correos_a_clientes(clientes)
    flash("Correos enviados exitosamente a los clientes Fríos o Interesados.", "success")
    return redirect(url_for('index'))

# Agregar cliente
@app.route('/add', methods=['GET', 'POST'])
def add_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        tipo_identificacion = request.form['tipo_identificacion']
        numero_identificacion = request.form['numero_identificacion']
        celular = request.form['celular']

        # Verificar si el email o numero de identificación ya existe
        cliente_existente = Cliente.query.filter((Cliente.email == email) | (Cliente.numero_identificacion == numero_identificacion)).first()
        if cliente_existente:
            flash('El correo electrónico o número de identificación ya está registrado', 'danger')
            return redirect(url_for('add_cliente'))

        nuevo_cliente = Cliente(
            nombre=nombre,
            email=email,
            tipo_identificacion=tipo_identificacion,
            numero_identificacion=numero_identificacion,
            celular=celular
        )
        db.session.add(nuevo_cliente)
        db.session.commit()
        flash('Cliente agregado correctamente', 'success')
        return redirect(url_for('index'))
    return render_template('add_cliente.html')

# Editar cliente
@app.route('/editar_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.email = request.form['email']
        cliente.tipo_identificacion = request.form['tipo_identificacion']
        cliente.numero_identificacion = request.form['numero_identificacion']
        cliente.celular = request.form['celular']
        cliente.estado = request.form['estado']

        db.session.commit()
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('index'))

    return render_template('editar_cliente.html', cliente=cliente)

# Eliminar cliente
@app.route('/eliminar_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    # Eliminar tareas asociadas
    for tarea in cliente.tareas:
        db.session.delete(tarea)

    # Eliminar cliente
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado correctamente', 'success')
    return redirect(url_for('index'))

# Ver tareas de un cliente
@app.route('/tareas/<int:cliente_id>')
def tareas_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    tareas = Tarea.query.filter_by(cliente_id=cliente_id).all()
    return render_template('tareas_cliente.html', cliente=cliente, tareas=tareas)

# Agregar tarea a un cliente
@app.route('/add_tarea/<int:cliente_id>', methods=['GET', 'POST'])
def add_tarea(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        descripcion = request.form['descripcion']
        fecha_vencimiento_str = request.form['fecha_vencimiento']
        estado = request.form['estado']
        valor = request.form['valor']

        fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()

        nueva_tarea = Tarea(
            descripcion=descripcion,
            fecha_vencimiento=fecha_vencimiento,
            completado=False,
            estado=estado,
            valor=valor,
            cliente_id=cliente.id
        )
        db.session.add(nueva_tarea)
        db.session.commit()
        flash('Tarea agregada correctamente', 'success')
        return redirect(url_for('tareas_cliente', cliente_id=cliente.id))

    return render_template('add_tarea.html', cliente=cliente)

# Editar tarea
@app.route('/editar_tarea/<int:tarea_id>', methods=['GET', 'POST'])
def editar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)

    if request.method == 'POST':
        tarea.descripcion = request.form['descripcion']
        tarea.fecha_vencimiento = datetime.strptime(request.form['fecha_vencimiento'], '%Y-%m-%d').date()
        tarea.estado = request.form['estado']
        tarea.valor = request.form['valor']

        db.session.commit()
        flash('Tarea actualizada correctamente', 'success')
        return redirect(url_for('tareas_cliente', cliente_id=tarea.cliente_id))

    return render_template('editar_tarea.html', tarea=tarea)

# Editar solo el estado del cliente
@app.route('/editar_estado/<int:cliente_id>', methods=['GET', 'POST'])
def editar_estado(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        cliente.estado = request.form['estado']
        db.session.commit()
        flash('Estado actualizado correctamente', 'success')
        return redirect(url_for('index'))

    return render_template('editar_estado.html', cliente=cliente)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear las tablas en la base de datos si no existen
    app.run(debug=True)