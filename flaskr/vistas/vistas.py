import json
from flask import request
from flask.json import JSONEncoder
from flaskr.modelos.modelos import db, Cancion, CancionSchema, Usuario, UsuarioSchema, Album, AlbumSchema, RecursoCompartido, RecursoCompartidoSchema, Comentario, ComentarioSchema, Notificacion, TipoNotificacion, NotificacionSchema, ComentarioRespuestaSchema
from marshmallow.fields import Date
from sqlalchemy.orm import query
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
import datetime
import pytz

cancion_schema = CancionSchema()
usuario_schema = UsuarioSchema()
album_schema = AlbumSchema()
recurso_compartido_schema = RecursoCompartidoSchema()
notificacion_schema = NotificacionSchema()
comentario_schema = ComentarioSchema()
comentario_respuesta_schema = ComentarioRespuestaSchema()

class VistaCancionesUsuario(Resource):

    @jwt_required()
    def post(self, id_usuario):
        nueva_cancion = Cancion(titulo=request.json["titulo"], minutos=request.json["minutos"], segundos=request.json["segundos"], interprete=request.json["interprete"])
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.canciones.append(nueva_cancion)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 'El usuario ya tiene una cancion con dicho nombre',409

        return cancion_schema.dump(nueva_cancion)

    # @jwt_required()

    def get(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        propios = []

        for c in usuario.canciones:
            propios.append(c)

        # compartidos = []
        for c in usuario.compartidos:
            if c.cancion_id != None :
                cc = Cancion.query.filter(Cancion.id == c.cancion_id).first()
                cc.propia = 'False'
                propios.append(cc)

        return [cancion_schema.dump(ca) for ca in propios]

class VistaCancion(Resource):

    def get(self, id_cancion):
        return cancion_schema.dump(Cancion.query.get_or_404(id_cancion))

    def put(self, id_cancion):
        cancion = Cancion.query.get_or_404(id_cancion)
        cancion.titulo = request.json.get("titulo",cancion.titulo)
        cancion.minutos = request.json.get("minutos",cancion.minutos)
        cancion.segundos = request.json.get("segundos",cancion.segundos)
        cancion.interprete = request.json.get("interprete",cancion.interprete)
        db.session.commit()
        return cancion_schema.dump(cancion)

    def delete(self, id_cancion):
        cancion = Cancion.query.get_or_404(id_cancion)
        db.session.delete(cancion)
        db.session.commit()
        return '',204

class VistaAlbumesCanciones(Resource):
    def get(self, id_cancion):
        cancion = Cancion.query.get_or_404(id_cancion)
        return [album_schema.dump(al) for al in cancion.albumes]

class VistaSignIn(Resource):

    def post(self):
        nuevo_usuario = Usuario(nombre=request.json["nombre"], contrasena=request.json["contrasena"])
        db.session.add(nuevo_usuario)
        db.session.commit()
        token_de_acceso = create_access_token(identity = nuevo_usuario.id)
        return {"mensaje":"usuario creado exitosamente", "token":token_de_acceso}

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.contrasena = request.json.get("contrasena",usuario.contrasena)
        db.session.commit()
        return usuario_schema.dump(usuario)

    def delete(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        db.session.delete(usuario)
        db.session.commit()
        return '',204

class VistaLogIn(Resource):

    def post(self):
        usuario = Usuario.query.filter(Usuario.nombre == request.json["nombre"], Usuario.contrasena == request.json["contrasena"]).first()
        db.session.commit()
        if usuario is None:
            return "El usuario no existe.", 400
        else:
            token_de_acceso = create_access_token(identity = usuario.id)
            return {"mensaje":"Inicio de sesión exitoso", "token": token_de_acceso}

class VistaAlbumesUsuario(Resource):

    @jwt_required()
    def post(self, id_usuario):
        nuevo_album = Album(titulo=request.json["titulo"], anio=request.json["anio"], descripcion=request.json["descripcion"], medio=request.json["medio"], propio=1)
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.albumes.append(nuevo_album)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 'El usuario ya tiene un album con dicho nombre',409

        return album_schema.dump(nuevo_album)

    # @jwt_required()
    def get(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        propios = []
        for a in usuario.albumes:
            propios.append(a)

        for c in usuario.compartidos:
            if c.album_id != None :
                ac = Album.query.filter(Album.id == c.album_id).first()
                ac.propio = 0
                propios.append(ac)

        return [album_schema.dump(al) for al in propios]

class VistaUsuario(Resource):
    def get(self, id_usuario):
        return usuario_schema.dump(Usuario.query.get_or_404(id_usuario))

class VistaCancionesAlbum(Resource):

    def post(self, id_album):
        album = Album.query.get_or_404(id_album)

        if "id_cancion" in request.json.keys():

            nueva_cancion = Cancion.query.get(request.json["id_cancion"])
            if nueva_cancion is not None:
                album.canciones.append(nueva_cancion)
                db.session.commit()
            else:
                return 'Canción errónea',404
        else:
            nueva_cancion = Cancion(titulo=request.json["titulo"], minutos=request.json["minutos"], segundos=request.json["segundos"], interprete=request.json["interprete"])
            album.canciones.append(nueva_cancion)
        db.session.commit()
        return cancion_schema.dump(nueva_cancion)

    def get(self, id_album):
        album = Album.query.get_or_404(id_album)
        return [cancion_schema.dump(ca) for ca in album.canciones]

class VistaAlbum(Resource):

    def get(self, id_album):
        return album_schema.dump(Album.query.get_or_404(id_album))

    def put(self, id_album):
        album = Album.query.get_or_404(id_album)
        album.titulo = request.json.get("titulo",album.titulo)
        album.anio = request.json.get("anio", album.anio)
        album.descripcion = request.json.get("descripcion", album.descripcion)
        album.medio = request.json.get("medio", album.medio)
        db.session.commit()
        return album_schema.dump(album)

    def delete(self, id_album):
        album = Album.query.get_or_404(id_album)
        db.session.delete(album)
        db.session.commit()
        return '',204

class VistaUsuarios(Resource):

    def get(self):
        return [usuario_schema.dump(u) for u in Usuario.query.all()]

class VistaAlbumes(Resource):

    def get(self):
        return [album_schema.dump(a) for a in Album.query.all()]

class VistaRecursosCompartidos(Resource):

    def get(self):
        return [recurso_compartido_schema.dump(rc) for rc in RecursoCompartido.query.all()]

    # @jwt_required()
    def post(self):

        usuario_destino = request.json["usuario_destino"]
        usuario_origen_id = request.json["usuario_origen_id"]
        tipo_recurso = request.json["tipo_recurso"]
        id_recurso = request.json["id_recurso"]

        check = self.check_data_recurso_compartido(usuario_destino, usuario_origen_id, tipo_recurso, id_recurso)

        if "Error." in check:
            return check, 400

        usuario_o = Usuario.query.filter(Usuario.id == usuario_origen_id).first()
        if usuario_o is None:
            db.session.rollback()
            return "El usuario origen no existe", 400

        usuarios_destinos = usuario_destino.split(',')
        for ud in usuarios_destinos:
            if usuario_o.nombre == ud:
                db.session.rollback()
                return "Error. No se puede compartir a usted mismo.", 400

            usuario_d = Usuario.query.filter(Usuario.nombre == ud).first()
            if usuario_d is None:
                label = "el album" if tipo_recurso == "ALBUM" else "la canción"
                db.session.rollback()
                return 'No se puede compartir ' + label + ' porque una o más personas no se encuentran registradas en Ionic.', 400

            recurso_compartido = RecursoCompartido(
                tipo_recurso= tipo_recurso,
                usuario_origen_id=usuario_origen_id,
                usuario_destino_id=usuario_d.id,
            )
            if tipo_recurso == "ALBUM":
                recurso_compartido.album_id = id_recurso
            else:
                recurso_compartido.cancion_id = id_recurso

            db.session.add(recurso_compartido)

        db.session.commit()
        return recurso_compartido_schema.dump(recurso_compartido)

    def check_data_recurso_compartido(self, usuario_destino, usuario_origen_id, tipo_recurso, id_recurso):
        if usuario_destino == None or usuario_origen_id == None:
            db.session.rollback()
            return "Error. El usuario destinatario o de origen no puede ser vacio."

        if type(usuario_destino) != str:
            db.session.rollback()
            return "Error. El usuario destinatario debe ser un texto."

        if type(usuario_origen_id) != int:
            db.session.rollback()
            return "Error. El id de usuario origen debe ser un numero."

        if tipo_recurso == None:
            db.session.rollback()
            return "Error. El tipo de recurso no puede ser vacio."

        if tipo_recurso != "ALBUM" and tipo_recurso != "CANCION":
            db.session.rollback()
            return "Error. El tipo de recurso debe ser ALBUM o CANCION."

        if id_recurso == None:
            db.session.rollback()
            return "Error. El id de recurso no puede ser vacio."

        return ''

class VistaUsuariosCompartidosPorTipo(Resource):

    def get(self, id_recurso, tipo_recurso):
        if tipo_recurso == "ALBUM":
            recurso_compartido = RecursoCompartido.query.filter(RecursoCompartido.album_id == id_recurso).group_by(RecursoCompartido.usuario_destino_id).all()
        else:
            recurso_compartido = RecursoCompartido.query.filter(RecursoCompartido.cancion_id == id_recurso).group_by(RecursoCompartido.usuario_destino_id).all()

        usuarios = []
        for rc in recurso_compartido:
            u = Usuario.query.filter(Usuario.id == rc.usuario_destino_id).first()
            usuarios.append(u)
        return [usuario_schema.dump(u) for u in usuarios]

class VistaComentarios(Resource):
    # @jwt_required()
    def post(self):
        usuario = request.json["usuario"]
        texto = request.json["texto"]
        recurso_id = ''
        if 'album_id' in request.json:
            recurso_id = request.json["album_id"]
            tipo_recurso = "ALBUM"
        else:
            recurso_id = request.json["cancion_id"]
            tipo_recurso = "CANCION"

        if recurso_id == None or type(recurso_id) != int:
            db.session.rollback()
            return "Error. El id de album o el id de cancion esta vacio o no es numerico", 400

        if usuario == None or type(usuario) != int:
            db.session.rollback()
            return "Error. El id de usuario no puede ser vacio o no es numerico", 400

        if Usuario.query.filter(Usuario.id == usuario).first() is None:
            db.session.rollback()
            return "El usuario origen no existe", 400

        if texto is None or len(texto) > 1000:
            db.session.rollback()
            return "El texto no puede ser vacio o el texto excede los 1000 caracteres.", 400

        comentario = Comentario(
            time=datetime.datetime.now(pytz.timezone('Etc/GMT+5')),
            usuario=usuario,
            texto=texto,
        )

        if tipo_recurso == "ALBUM":
            comentario.album_id = recurso_id
        else:
            comentario.cancion_id = recurso_id

        try:
            db.session.add(comentario)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return "No se puedo guardar el comentario", 400

        return comentario_schema.dump(comentario)

class VistaComentario(Resource):
    def get(self, id_comentario):
        return comentario_schema.dump(Comentario.query.get_or_404(id_comentario))

class VistaComentariosPorTipo(Resource):
    def get(self, id_recurso, tipo_recurso):

        if tipo_recurso == "ALBUM":
            query = db.session.query(Comentario.id, Comentario.cancion_id, Comentario.album_id, Comentario.time, Comentario.texto, Usuario.nombre.label('nombre')). \
            join(Comentario, Comentario.usuario == Usuario.id). \
            order_by(Comentario.time).filter(Comentario.album_id == id_recurso)
        else:
            query = db.session.query(Comentario.id, Comentario.cancion_id, Comentario.album_id, Comentario.time, Comentario.texto, Usuario.nombre.label('nombre')). \
            join(Comentario, Comentario.usuario == Usuario.id). \
            order_by(Comentario.time).filter(Comentario.cancion_id == id_recurso)

        comentarios = query.all()

        response = []
        for c in comentarios:
            r = {
                'id': c['id'],
                'cancion_id': c['cancion_id'],
                'album_id': c['album_id'],
                'time': c['time'],
                'texto': c['texto'],
                'nombre_usuario': c['nombre']
            }
            response.append(r)

        return [comentario_respuesta_schema.dump(cr) for cr in response]

class VistaNotificacionUsuario(Resource):

    #@jwt_required()
    def post(self, id_usuario):
        tipo_notificacion = request.json["tipo"]
        nombre_recurso = request.json["nombre"]
        usuarios_destino = request.json["usuarios"]

        if tipo_notificacion == None or nombre_recurso == None or usuarios_destino == None:
            db.session.rollback()
            return "Error. El tipo y el nombre de recurso no pueden ser vacio", 400

        usuarioOrigen = Usuario.query.get_or_404(id_usuario)
        #armar mensaje
        if tipo_notificacion == TipoNotificacion.COMPARTIR_ALBUM.name:
            mensaje = "El usuario {} le ha compartido el álbum {} el día {}";
        elif tipo_notificacion == TipoNotificacion.COMPARTIR_CANCION.name:
            mensaje = "El usuario {} le ha compartido la canción {} el día {}";
        else:
            mensaje = "El usuario {} le ha compartido {} el día {}";

        mensaje = mensaje.format(usuarioOrigen.nombre, nombre_recurso, datetime.datetime.now(pytz.timezone('Etc/GMT+5')));

        usuarios = usuarios_destino.split(',')
        for ud in usuarios:
            usuario = Usuario.query.filter(Usuario.nombre == ud).first()
            if usuario is not None:
                nuevo_notificacion = Notificacion(mensaje=mensaje, tipo_notificacion=tipo_notificacion)
                usuario.notificaciones.append(nuevo_notificacion)

        db.session.commit()
        return notificacion_schema.dump(nuevo_notificacion)

    # @jwt_required()
    def get(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        notificaciones = sorted(usuario.notificaciones, key=lambda x: x.id, reverse=True);
        return [notificacion_schema.dump(ca) for ca in notificaciones]
