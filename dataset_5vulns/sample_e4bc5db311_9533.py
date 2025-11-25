from principal.models import Fase
from principal.models import Item
from principal.models import VersionItem
from principal.models import AtributoItem
from principal.models import TipoItem
from principal.models import Relacion
from principal.models import ArchivoForm, Archivo
from principal.models import HistorialItem
from principal.models import Usuario
from principal.views import is_logged
from django.shortcuts import render, redirect
from django.http.response import HttpResponse
import json
import datetime
from django.utils.timezone import utc
from django.db import transaction
from django.contrib import messages
# Create your views here.


def indexItem(request, id_fase):
    u = is_logged(request.session)
    if(u):
        fase = Fase.objects.get(id=id_fase)
        if request.method != 'POST':
            lista = fase.item_set.all().order_by('numero')
        else:
            lista = fase.item_set.all().filter(nombre__startswith=request.POST['search'])
        return render(request, 'item.html', {'usuario': u, 'fase': fase, 'lista': lista})
    else:
        return redirect('/login')


def nuevoItem(request, id_fase, id_tipo_item):
    u = is_logged(request.session)
    if (u):
        fase = Fase.objects.get(id=id_fase)
        tipo_item = TipoItem.objects.get(id=id_tipo_item)
        if (request.method == 'POST'):
            if('nombre' in request.POST and
               'numero' in request.POST and
               'complejidad' in request.POST and
               'costo' in request.POST and
               'prioridad' in request.POST):
                user = Usuario.objects.get(id=request.session['usuario'])
                atributos = {
                    'complejidad': request.POST['complejidad'],
                    'costo': request.POST['costo'],
                    'prioridad': request.POST['prioridad']
                }
                for atributo in tipo_item.atributotipoitem_set.all():
                    valor = atributo.valor_por_defecto
                    if(atributo.nombre in request.POST):
                        valor = request.POST[atributo.nombre]
                    atributos[atributo.nombre] = valor
                try:
                    newItem(request.POST["nombre"], request.POST["numero"], fase.id, tipo_item.id, atributos)
                    historialItem("crear", fase.id, user.id)
                except Exception as e:
                    print(e)
                    return render(request, 'nuevo-item.html', {'usuario': u, 'fase': fase, 'tipo_item': tipo_item, 'mensaje': 'Ocurrio un error al crear el item. Verifique los datos.'})
                return redirect('item:index', id_fase)
            else:
                return render(request, 'nuevo-item.html', {'usuario': u, 'fase': fase, 'tipo_item': tipo_item, 'mensaje': 'Ocurrio un error al crear el item. Verifique los datos.'})
        else:
            return render(request, 'nuevo-item.html', {'usuario': u, 'fase': fase, 'tipo_item': tipo_item})
    else:
        return redirect('/login')


def eliminarItem(request, id_fase, id_item):
    u = is_logged(request.session)
    if(u):
        deleteItem(id_item)
        return redirect('item:index', id_fase=id_fase)
    else:
        return redirect('/login')


def revivirItem(request, id_fase, id_item):
    u = is_logged(request.session)
    if(u):
        resurrectItem(id_item)
        return redirect('item:index', id_fase=id_fase)
    else:
        return redirect('/login')


def modificarItem(request, id_fase, id_item):
    u = is_logged(request.session)
    if (u):
        fase = Fase.objects.get(id=id_fase)
        lbs = fase.lineabase_set.all()
        item = Item.objects.get(id=id_item)
        version = VersionItem.objects.get(id=item.id_actual)
        tipo_item = item.tipo_item
        if (request.method == 'POST'):
            if('complejidad' in request.POST and
               'costo' in request.POST and
               'prioridad' in request.POST and
               'estado' in request.POST):
                atributos = {
                    'complejidad': request.POST['complejidad'],
                    'costo': request.POST['costo'],
                    'prioridad': request.POST['prioridad'],
                    'estado': request.POST['estado']
                }
                for atributo in tipo_item.atributotipoitem_set.all():
                    valor = atributo.valor_por_defecto
                    if(atributo.nombre in request.POST):
                        valor = request.POST[atributo.nombre]
                    atributos[atributo.nombre] = valor
                user = Usuario.objects.get(id=request.session['usuario'])
                try:
                    item.linea_base = None
                    item.save()
                    newVersion(id_item, atributos)
                    historialItem('modificar', item.id, user.id)
                    item = Item.objects.get(id=id_item)
                    version = item.versionitem_set.filter(id=item.id_actual).first()
                    estadoRevisionItem(version)
                    condicion = False
                    for lb in lbs:
                        cantidadItems = lb.item_set.all().count()
                        if (cantidadItems == 0):
                            condicion = True
                        elif (cantidadItems > 0):
                            condicion = False
                    if (condicion == True):
                        fase.estado = 'en desarrollo'
                        fase.save()
                except Exception as e:
                    print(e)
                    return render(request, 'modificar-item.html', {'usuario': u, 'fase': fase, 'item': item, 'version': version, 'tipo_item': tipo_item, 'mensaje': 'Ocurrio un error al modificar el item. Verifique los datos.'})
                return redirect('item:index', id_fase)
            else:
                return render(request, 'modificar-item.html', {'usuario': u, 'fase': fase, 'item': item, 'version': version, 'tipo_item': tipo_item, 'mensaje': 'Ocurrio un error al modificar el item. Verifique los datos.'})
        else:
            return render(request, 'modificar-item.html', {'usuario': u, 'fase': fase, 'item': item, 'version': version, 'tipo_item': tipo_item})
    else:
        return redirect('/login')


def revertirItem(request, id_fase, id_item):
    u = is_logged(request.session)
    if (u):
        fase = Fase.objects.get(id=id_fase)
        item = Item.objects.get(id=id_item)
        if (request.method == 'POST'):
            if('id_version' in request.POST):
                id_version = request.POST['id_version']
                user = Usuario.objects.get(id=request.session['usuario'])
                try:
                    setVersionItem(id_item, id_version)
                    historialItem('revertir a' + str(id_version), id_item, user.id)
                except Exception as e:
                    print(e)
                    return render(request, 'revertir-item.html', {'usuario': u, 'fase': fase, 'item': item, 'mensaje': 'Ocurrio un error al revertir el item. Intente de nuevo'})
                item = Item.objects.get(id=id_item)
                return render(request, 'revertir-item.html', {'usuario': u, 'fase': fase, 'item': item, 'mensaje': 'Se cambio la version del item con exito.'})
            else:
                return render(request, 'revertir-item.html', {'usuario': u, 'fase': fase, 'item': item, 'mensaje': 'Ocurrio un error al revertir el item. Intente de nuevo.'})
        else:
            return render(request, 'revertir-item.html', {'usuario': u, 'fase': fase, 'item': item})
    else:
        return redirect('/login')


def relacionarItem(request, id_fase, id_item):
    u = is_logged(request.session)
    if(u):
        fase = Fase.objects.get(id=id_fase)
        item = Item.objects.get(id=id_item)
        if request.method == 'POST':
            if(('sucesor' in request.POST or 'hijo' in request.POST) and
               'tipo' in request.POST):
                try:
                    id_antecesor = id_item
                    tipo = request.POST['tipo']
                    if(tipo == 'padre-hijo'):
                        id_sucesor = request.POST['hijo']
                    else:
                        id_sucesor = request.POST['sucesor']
                    if(not detectCicle(id_antecesor, id_sucesor)):
                        item1 = Item.objects.get(id=id_antecesor)
                        item2 = Item.objects.get(id=id_sucesor)
                        user = Usuario.objects.get(id=request.session['usuario'])
                        newRelacionItems(id_fase, tipo, id_antecesor, id_sucesor)
                        messages.success(request, 'Se creo la relacion con exito.')
                        historialItem('relacionar ' + item1.nombre + ' y ' + item2.nombre, id_item, user.id)
                    else:
                        messages.error(request, 'No se pudo crear la relacion por que se formaria un ciclo.')
                except Exception as e:
                    print(e)
                    messages.error(request, 'No se pudo crear la relacion. Intente de nuevo.')
        lista = getRelacionesItem(id_item)
        graph = generarArborItem(id_item)
        return render(request, 'relacionar-item.html', {'usuario': u, 'fase': fase, 'item': item, 'lista': lista, 'graph': graph})
    else:
        return redirect('/login')


def removerRelacionItem(request, id_fase, id_item, id_relacion):
    try:
        relacion = Relacion.objects.get(id=id_relacion)
        item1 = Item.objects.get(id=id_item)
        item2 = Item.objects.get(id=relacion.sucesor.proxy.id)
        user = Usuario.objects.get(id=request.session['usuario'])
        deleteRelacion(id_relacion)
        messages.success(request, "Se elimino la relacion con exito")
        historialItem('eliminar relacion con' + item2.nombre, item1.id, user.id)
    except Exception as e:
        print(e)
        messages.error(request, "No se pudo eliminar la relacion")
    return redirect('item:relacionar', id_fase=id_fase, id_item=id_item)


def getItem(request, id_tipo_item):
    ti = Item.objects.raw("SELECT * FROM principal_item WHERE id=%s" % id_tipo_item)[0]
    dic = {}
    dic['nombre'] = ti.nombre
    dic['descripcion'] = ti.descripcion
    dic['codigo'] = ti.codigo
    listaAtributos = []
    for a in ti.atributotipoitem_set.all():
        listaAtributos.append({'nombre': a.nombre, 'tipo': a.tipo, 'valor_por_defecto': a.valor_por_defecto})
    dic['atributos'] = listaAtributos
    data = json.dumps(dic)
    return HttpResponse(data)


def getImpactoItem(request, id_item):
    item = Item.objects.get(id=id_item)
    impacto = calcularImpacto(id_item)
    dic = {}
    dic['impacto'] = impacto
    dic['nombre'] = item.nombre
    data = json.dumps(dic)
    return HttpResponse(data)


def newItem(nombre, numero, id_fase, id_tipo_item, atributos):
    with transaction.atomic():
        item = Item()
        item.nombre = nombre
        item.numero = numero
        item.eliminado = False
        fase = Fase.objects.get(id=id_fase)
        tipo_item = TipoItem.objects.get(id=id_tipo_item)
        item.fase = fase
        item.tipo_item = tipo_item
        item.save()
        version_item = VersionItem()
        version_item.version = item.version
        version_item.complejidad = atributos["complejidad"]
        version_item.costo = atributos["costo"]
        version_item.prioridad = atributos["prioridad"]
        version_item.estado = "inicial"
        version_item.proxy = item
        version_item.save()
        atributos_tipo_item = tipo_item.atributotipoitem_set.all()
        for atributo_tipo_item in atributos_tipo_item:
            atributo_item = AtributoItem()
            atributo_item.valor = atributos[atributo_tipo_item.nombre]
            atributo_item.atributo_tipo_item = atributo_tipo_item
            atributo_item.save()
            version_item.atributos.add(atributo_item)
        version_item.save()
        item.version = version_item.version
        item.id_actual = version_item.id
        item.save()


def newVersion(id_item, atributos):
    with transaction.atomic():
        item = Item.objects.get(id=id_item)
        tipo_item = item.tipo_item
        version_item = VersionItem()
        version_item.version = item.version
        version_item.complejidad = atributos["complejidad"]
        version_item.costo = atributos["costo"]
        version_item.prioridad = atributos["prioridad"]
        version_item.estado = atributos["estado"]
        version_item.proxy = item
        version_item.save()
        atributos_tipo_item = tipo_item.atributotipoitem_set.all()
        for atributo_tipo_item in atributos_tipo_item:
            atributo_item = AtributoItem()
            atributo_item.valor = atributos[atributo_tipo_item.nombre]
            atributo_item.atributo_tipo_item = atributo_tipo_item
            atributo_item.save()
            version_item.atributos.add(atributo_item)
        version_item.save()
        for r in getRelacionesItem(id_item, True):
            if(str(r.antecesor.proxy.id) == str(id_item)):
                r.antecesor = version_item
            if(str(r.sucesor.proxy.id) == str(id_item)):
                r.sucesor = version_item
            r.save()
        item.version = version_item.version
        item.id_actual = version_item.id
        item.save()


def setEstadoItem(id_item, estado):
    with transaction.atomic():
        item = Item.objects.get(id=id_item)
        version_actual = VersionItem.objects.get(id=item.id_actual)
        version_actual.estado = estado
        version_actual.save()
        item.version = version_actual.version
        item.save()


def setVersionItem(id_item, id_version):
    with transaction.atomic():
        item = Item.objects.get(id=id_item)
        version_item = VersionItem.objects.get(id=id_version)
        version_item.proxy = item
        version_item.save()
        item.version = version_item.version
        item.id_actual = version_item.id
        item.save()


def deleteItem(id_item):
    with transaction.atomic():
        item = Item.objects.get(id=id_item)
        item.eliminado = True
        setEstadoItem(id_item, 'eliminado')
        relaciones = getRelacionesItem(id_item)
        for r in relaciones:
            r.eliminado = True
            r.save()
        item.save()


def resurrectItem(id_item):
    with transaction.atomic():
        item = Item.objects.get(id=id_item)
        item.eliminado = False
        setEstadoItem(id_item, 'inicial')
        relaciones = getRelacionesItem(id_item, True)
        for r in relaciones:
            id_ant = r.antecesor.proxy.id
            id_suc = r.sucesor.proxy.id
            if(not detectCicle(id_ant, id_suc)):
                r.eliminado = False
                r.save()
            else:
                r.delete()
        item.save()


def newRelacionItems(id_fase, tipo, id_antecesor, id_sucesor):
    fase = Fase.objects.get(id=id_fase)
    item_antecesor = Item.objects.get(id=id_antecesor)
    item_sucesor = Item.objects.get(id=id_sucesor)
    for relacion in getRelacionesItem(id_antecesor):
        if(item_sucesor == relacion.sucesor.proxy):
            raise Exception("Ya posee esta relacion!")
    antecesor = VersionItem.objects.get(id=item_antecesor.id_actual)
    sucesor = VersionItem.objects.get(id=item_sucesor.id_actual)
    proyecto = fase.proyecto
    relacion = Relacion()
    relacion.fase = fase
    relacion.proyecto = proyecto
    relacion.sucesor = sucesor
    relacion.antecesor = antecesor
    relacion.tipo = tipo
    relacion.save()


def deleteRelacion(id_relacion):
    relacion = Relacion.objects.get(id=id_relacion)
    relacion.delete()


def getRelacionesItem(id_item, all=False):
    relaciones = None
    try:
        item = Item.objects.get(id=id_item)
        version = VersionItem.objects.get(id=item.id_actual)
        if(all):
            antecesores = version.relacion_antecesor_set.all()
            sucesores = version.relacion_sucesor_set.all()
        else:
            antecesores = version.relacion_antecesor_set.all().filter(eliminado=False)
            sucesores = version.relacion_sucesor_set.all().filter(eliminado=False)
        relaciones = []
        relaciones += antecesores
        relaciones += sucesores
    except Exception as e:
        print(e)
    return relaciones


def estadoRevisionItem(version):
    itemac = version.proxy
    fase = itemac.fase
    fase.estado = 'con linea base'
    fase.save()
    version_item = version
    relacionVerant = Relacion.objects.filter(antecesor=version_item)
    relacionVersuc = Relacion.objects.filter(sucesor=version_item)
    if(relacionVerant.exists()):
        for r in relacionVerant:
            versionSuc = r.sucesor
            versionSuc.estado = 'revision'
            versionSuc.save()
            itemSuc = versionSuc.proxy
            lineab = itemSuc.linea_base
            if(lineab is not None):
                if(lineab.estado != 'liberada'):
                    lineab.estado = 'no valido'
                    lineab.save()
                    fase = lineab.fase
                    if(fase.estado == 'finalizada'):
                        fase.estado = 'con linea base'
                        fase.save()
    if(relacionVersuc.exists()):
        for r in relacionVersuc:
            versionAnt = r.antecesor
            versionAnt.estado = 'revision'
            versionAnt.save()
            itemAnt = versionAnt.proxy
            lineab = itemAnt.linea_base
            if(lineab is not None):
                if(lineab.estado != 'liberada'):
                    lineab.estado = 'no valido'
                    lineab.save()
                    fase = lineab.fase
                    if(fase.estado == 'finalizada'):
                        fase.estado = 'con linea base'
                        fase.save()


def getAntecesoresItem(id_item):
    antecesores = None
    try:
        item = Item.objects.get(id=id_item)
        version = VersionItem.objects.get(id=item.id_actual)
        antecesores_r = version.relacion_sucesor_set.all().filter(eliminado=False)
        antecesores = []
        for r in antecesores_r:
            i = Item.objects.get(id=r.antecesor.proxy.id)
            antecesores.append(i)
    except Exception as e:
        print(e)
    return antecesores


def getAntecesoresItemDeep(id_item):
    antecesores = None
    try:
        item = Item.objects.get(id=id_item)
        version = VersionItem.objects.get(id=item.id_actual)
        antecesores_r = version.relacion_sucesor_set.all().filter(eliminado=False)
        antecesores = []
        for r in antecesores_r:
            i = Item.objects.get(id=r.antecesor.proxy.id)
            antecesores += getAntecesoresItemDeep(i.id)
            antecesores.append(i)
    except Exception as e:
        print(e)
    return antecesores


def getSucesoresItem(id_item):
    sucesores = None
    try:
        item = Item.objects.get(id=id_item)
        version = VersionItem.objects.get(id=item.id_actual)
        sucesores_r = version.relacion_antecesor_set.all().filter(eliminado=False)
        sucesores = []
        for r in sucesores_r:
            i = Item.objects.get(id=r.sucesor.proxy.id)
            sucesores.append(i)
    except Exception as e:
        print(e)
    return sucesores


def getSucesoresItemDeep(id_item):
    sucesores = None
    try:
        item = Item.objects.get(id=id_item)
        version = VersionItem.objects.get(id=item.id_actual)
        sucesores_r = version.relacion_antecesor_set.all().filter(eliminado=False)
        sucesores = []
        for r in sucesores_r:
            i = Item.objects.get(id=r.sucesor.proxy.id)
            sucesores += getSucesoresItemDeep(i.id)
            sucesores.append(i)
    except Exception as e:
        print(e)
    return sucesores


def historialItem(operacion, id_item, id_usuario):
    item = Item.objects.get(id=id_item)
    date = datetime.datetime.now().replace(tzinfo=utc)
    user = Usuario.objects.get(id=id_usuario)
    op = operacion
    hist = HistorialItem()
    hist.fecha = date
    hist.operacion = op
    hist.item = item
    hist.usuario = user.username
    hist.save()


def indexHistorialItem(request, id_fase, id_item):
    u = is_logged(request.session)
    if(u):
        item = Item.objects.get(id=id_item)
        fase = Fase.objects.get(id=id_fase)
        return render(request, 'historial-item.html', {'usuario': u, 'fase': fase, 'item': item})
    else:
        redirect('/login')


def aprobarItem(request, id_fase, id_item):
    try:
        item = Item.objects.get(id=id_item)
        v = item.versionitem_set.filter(id=item.id_actual).first()
        v.estado = 'aprobado'
        v.save()
    except Exception as e:
        print(e)
    return redirect('item:index', id_fase=id_fase)


def adjuntarArchivo(request, id_fase, id_item):
    u = is_logged(request.session)
    if(u):
        item = Item.objects.get(id=id_item)
        fase = Fase.objects.get(id=id_fase)
        if request.method == 'POST':
            form = ArchivoForm(request.POST, request.FILES)
            try:
                if form.is_valid():
                    nuevoArchivo = Archivo(archivo=request.FILES['archivo'])
                    nuevoArchivo.item = item
                    nuevoArchivo.save()
                    return redirect('item:adjuntar', id_fase=id_fase, id_item=id_item)
            except Exception as e:
                print(e)
                messages.error(request, 'No se pudo subir el archivo.')
        else:
            form = ArchivoForm()
        documents = Archivo.objects.filter(item=item)
        return render(request, 'item-adjuntar.html', {'usuario': u, 'documents': documents, 'form': form, 'item': item, 'fase': fase})
    else:
        return redirect('/login')


def calcularImpacto(id_item):
    item = Item.objects.get(id=id_item)
    version = VersionItem.objects.get(id=item.id_actual)
    antecesores = version.relacion_antecesor_set.all()
    sucesores = version.relacion_sucesor_set.all()
    relaciones = []
    relaciones += antecesores
    relaciones += sucesores
    impacto = 0 + version.costo
    for r in relaciones:
        if(r.antecesor.id != version.id):
            v = VersionItem.objects.get(id=r.antecesor.id)
            impacto += v.costo
        if(r.sucesor.id != version.id):
            v = VersionItem.objects.get(id=r.sucesor.id)
            impacto += v.costo
    return impacto


def generarArborItem(id_item):
    js = ""
    item = Item.objects.get(id=id_item)
    js += 'nodes:{' + str(item.id) + ':{ color:"#428bca", mass:200, label:"' + item.nombre + '"},'
    ant = getAntecesoresItem(id_item)
    for i in ant:
        js += ' ' + str(i.id) + ':{ color: "green", label: "' + i.nombre + '"},'
    suc = getSucesoresItem(id_item)
    for i in suc:
        js += ' ' + str(i.id) + ':{ color: "red", label: "' + i.nombre + '"},'
    js += '}, edges:{'
    js += ' ' + str(item.id) + ': {'
    for i in suc:
        js += ' ' + str(i.id) + ':{ color: "red" },'
    js += '},'
    for i in ant:
        js += ' ' + str(i.id) + ': { ' + str(item.id) + ': { color : "green" } },'
    js += '}'
    return js


def detectCicle(id_antecesor, id_sucesor):
    ants = getAntecesoresItemDeep(id_antecesor)
    for i in ants:
        if(str(i.id) == str(id_sucesor)):
            return True
    sucs = getSucesoresItemDeep(id_sucesor)
    for i in sucs:
        if(str(i.id) == str(id_antecesor)):
            return True
    return False