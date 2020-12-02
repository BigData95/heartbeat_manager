#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import copy
from simulador import Event, Model, Simulation

import tkinter as tk


# Martinez Vargas Edgar Ivan
#

class Mensaje(Event):
    """ Modifica la clase Event para agregar mas parametros necesarios para el algoritmo

        Atributos:
            name: Es el mensaje que será transmitido, Identifica que tipo de operación se llevara a cabo
            time: El momento en el que se encolara la tarea para ser transmitida al nodo que le corresponde. (clock+tiempo)
            target: El ID del nodo a quien va dirigido el mensaje.
            source: EL ID del nodo quien manda el mensaje. (self.id)
            listaVivos: Guarda la lista de los nodos activos.
            numHeartBeat: Contador de los heartbeat realizados.
            nodosQueMueren: Contiene la lista de los nodos que van a fallar.
            tiempoMuerte: Contiene la lista con los tiempos en los que los nodos van a fallar
            tiempoRevivir: Contiene la lista con los tiempo en los que los nodos van a regresar después de que hayan fallado.

        Los siguientes atributos son determinados desde el inicio del algoritmo a traves del GUI y no pueden ser
        modficados una vez incializado:
            nodosQueMueren
            tiempoMuerte
            tiempoRevivir

        Los siguientes atributos solo pueden ser modificados si el nodo esta identificado como líder:
            numHeartBeart: Se puede modificar la frecuencia en la que el líder manda un heartbeat atraves de GUI
            listaVivos: La información de quien esta activo la recibe el líder con una confirmación de cada nodo
                        después de su ultimo heartbeat emitido.
    """

    def __init__(self, 
                name, 
                time, 
                target, 
                source, 
                listaVivos, 
                numHeartbeat, 
                nodosQueMueren, 
                tiempoMuerte,
                tiempoRevivir
                ):
        Event.__init__(self, name, time, target, source)
        self.listaVivos = listaVivos
        self.numHeartbeat = numHeartbeat
        self.nodosQueMueren = nodosQueMueren
        self.tiempoMuerte = tiempoMuerte
        self.tiempoRevivir = tiempoRevivir

    def getListaVivos(self):
        return self.listaVivos

    def getNumHeartbeat(self):
        return self.numHeartbeat

    def getNodosQueMueren(self):
        return self.nodosQueMueren

    def getTiempoMuerte(self):
        return self.tiempoMuerte

    def getTiempoRevivir(self):
        return self.tiempoRevivir


class Algorithm2(Model):

    def init(self):
        # print("inicializo algoritmo")

        self.lider = self.id
        self.mejorCandidato = self.id
        self.soyLider = False  # Nos ayudara a saber cuando hay dos lideres (?)
        self.estoyVivo = True
        self.listaVivos = [100] * len(self.neighbors)
        self.numHeartbeat = 0

        self.recienRevivido = False
        # Nuevos
        self.candidaturaMandada = False
        self.timerReiniciado = 0
        self.timerDespachadoAlerta = False
        self.estadoAlerta = False
        self.estadoElecciones = False
        self.ignorarMensajes = False
        # Lista ingresadas por GUI
        self.nodosQueMueren = []
        self.tiempoMuerte = []
        self.tiempoRevivir = []

    def receive(self, event):

        if self.estoyVivo:  # EL nodo esta activo

            # TODOS: Me despierto por primera vez
            # Pongo timer para saber si líder esta activo o no, e inicializo las variables que necesito
            if event.getName() == "DESPIERTA":
                # Aunque esta en init debe reiniciarse las variables para el siguiente Run
                self.lider = self.id
                self.mejorCandidato = self.id
                self.soyLider = False  # Nos ayudara a saber cuando hay dos lideres (?)
                self.estoyVivo = True
                self.listaVivos = [100] * len(self.neighbors)
                self.numHeartbeat = 0
                self.recienRevivido = False
                # Nuevos
                self.candidaturaMandada = False
                self.timerReiniciado = 0
                self.timerDespachadoAlerta = False
                self.estadoAlerta = False
                self.estadoElecciones = False
                self.ignorarMensajes = False
                self.nodosQueMueren = event.getNodosQueMueren()
                self.tiempoMuerte = event.getTiempoMuerte()
                self.tiempoRevivir = event.getTiempoRevivir()

                # Programa su muerte desde el inicio
                if self.id in self.nodosQueMueren:
                    indexes = [i for i, x in enumerate(self.nodosQueMueren) if x == self.id]
                    print("Los indices son" + str(indexes)) 
                    for i in indexes:
                        newevent = Event("MUERO", self.clock + self.tiempoMuerte[i], self.id, self.id)   
                        self.transmit(newevent)         
                    #index = self.nodosQueMueren.index(self.id)
                    #print(str(self.tiempoMuerte[index]))
                    #newevent = Event("MUERO", self.clock + self.tiempoMuerte[index], self.id, self.id)
                    #self.transmit(newevent)

                setPrint(
                    "[" + str(self.clock) + "]:" + 
                    " Nodo: " + str(self.id), 
                    'heartbeat'
                    )
                setTimerEstadoLider(self)

            # Estado de alerta ##################################
            # Puede que le llegue cuando erea lider
            if self.estadoAlerta and event.getName() != "OK" and event.getName() != "TIMER_HEARTBEAT":
                self.estadoAlerta = False
                # Inicia elecciones
                if event.getName() == "HEARTBEAT":
                    mensaje(self, "OK", event.getSource())
                    self.numHeartbeat = event.getNumHeartbeat()
                    print(
                        "[" + str(self.clock) + "]:" + 
                        " Nodo: " + str(self.id) + 
                        " Mando timer estado ,heartbeat en estado"
                        )
                    setTimerEstadoLider(self)
                    self.timerReiniciado += 1

                if event.getName() == "TIMERESTADO":
                    setPrint(
                        "[" + str(self.clock) + "]:" + 
                        " Nodo: " + str(self.id) + 
                        " Alerta: Mando Inicio Elecciones","elecciones"
                        )
                    for t in self.neighbors:
                        mensaje(self, "CANDIDATO", t)
                    self.candidaturaMandada = True
                    self.estadoElecciones = True
                    self.timerReiniciado -= 1 # Quiza esta linea esta demas ?
                    self.timerDespachadoAlerta = True
                    setTimerElecciones(self)

                if event.getName() == "CANDIDATO":
                    enviaCandidato(self, event)
                # Hay dos lideres hizo decempate
                # self.estadoAlerta = False
                print(
                    "[" + str(self.clock) + "]:" + 
                    " Nodo: " + str(self.id) + 
                    " Estado de alerta desactivado por " + 
                    str(event.getName())
                    )



            # SoyLider #############################
            if self.soyLider:
                print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + "Soy Lider, me llega mensaje " + str(event.getName()) + " de " + str(event.getSource()) )
                # LIDER: Agrega a la lista los nodos que le respondieron
                if event.getName() == "OK" and not self.ignorarMensajes:
                    self.listaVivos.append(event.getSource())
                    self.recienRevivido = False
                if event.getName() == "HEARTBEAT" and not self.ignorarMensajes:
                    if event.getNumHeartbeat() > self.numHeartbeat or (
                            event.getNumHeartbeat() == self.numHeartbeat and event.getSource() > self.id) or (event.getNumHeartbeat() == self.numHeartbeat and self.recienRevivido):
                        self.soyLider = False
                        self.lider = event.getSource()
                        setPrint(
                            "[" + str(self.clock) + "]:" + 
                            " Nodo: " + str(self.id) + 
                            " Mi reinado a terimando. Mi Heartbeat: " + 
                            str(self.numHeartbeat) + 
                            " Heartbeat del otro:" + 
                            str(event.getNumHeartbeat()), 
                            'muere'
                            )
                        # print("[" + str(self.clock) + "]:" + 
                        #     " Nodo: " + str(self.id) + 
                        #     " Mando timer estado termino ser lider"
                        #     )
                        setTimerEstadoLider(self)
                       # self.timerReiniciado += 1
                    else:
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " + str(
                            self.id) + " YO SOY EL LIDER: " + str(self.id) + " Mi HeartBeat: " + str(
                            self.numHeartbeat) + " Heartbeat del otro:" + str(event.getNumHeartbeat()), 'soyLider')
                if event.getName() == "CANDIDATO":# and not self.estadoElecciones:
                    if not self.estadoElecciones:
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " +str(self.id) + " Soy lider y entro a elecciones porque recibi candidatura de: " + str(event.getSource()),"elecciones")
                    enviaCandidato(self, event)
                if event.getName() == "TIMER_HEARTBEAT":
                    setHeartbeat(self)
                    setTimerHeartbeat(self)

            # No soy lider #################
            if not self.soyLider:
                # Respondo al lider
                if event.getName() == "HEARTBEAT" and not self.ignorarMensajes:
                    print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Mando timer estado respuesta a heartbeat")
                    setTimerEstadoLider(self)
                    self.timerReiniciado += 1
                    mensaje(self, "OK", event.getSource())
                    self.numHeartbeat = event.getNumHeartbeat()
                    print("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + "Mando Ok al lider")

                if event.getName() == "CANDIDATO":
                    if not self.estadoElecciones:
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Entro a elecciones porque recibi candidatura de: " + str(event.getSource()), "elecciones")
                    enviaCandidato(self, event)

                if event.getName() == "TIMERESTADO" and not self.estadoAlerta and not self.timerDespachadoAlerta:
                    if self.timerReiniciado != 0:
                        self.timerReiniciado -= 1
                        print("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Ignoro este timer, viene otro atras, TIMERS A IGNORAR: " + str(self.timerReiniciado))
                    else:
                        print("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Entra estaado Alerta,PRIMER TIMER EXPIRADO    ")
                        print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Mando timer estado entro estado alerta")
                        setTimerEstadoLider(self)
                        self.estadoAlerta = True
                        #self.timerReiniciado = False

                if event.getName() == "TIMERESTADO" and self.timerDespachadoAlerta:
                    self.timerDespachadoAlerta = False
            
            
            # Elecciones ############
            if self.estadoElecciones:
                self.ignorarMensajes = True
                if event.getName() == "CANDIDATO":
                    if event.getSource() > self.mejorCandidato:  # Al inicio siempre es self.id
                        self.mejorCandidato = event.getSource()
                if event.getName() == "TIMERELECCIONES":  # Se terminan las elecciones
                    print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " cierran elecciones" )
                    self.candidaturaMandada = False
                    self.estadoElecciones = False
                    self.ignorarMensajes = False
                    self.lider = self.mejorCandidato
                    if self.lider == self.id:  # Soy lider
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + "  Soy lider: " + str(self.id), 'soyLider')
                        #self.timerReiniciado = 0
                        self.soyLider = True
                        setTimerHeartbeat(self)
                    else:
                        self.soyLider = False
                        self.mejorCandidato = self.id  # Reinicia para siguientes elecciones
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " +str(self.id) + " Mi lider" + str(self.lider),"nuevoLider")
                        print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Mando timer estado se eligio un nuevo lider")
                        setTimerEstadoLider(self)
                        self.timerReiniciado += 1


            # TODOS: Simula el fallo
            if event.getName() == "MUERO":
                self.estoyVivo = False
                if self.soyLider:
                    setPrint("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Soy el lider " + str(self.id) + " y ME MUERO", 'muere')
                else:
                    setPrint("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Soy " + str(self.id) + " y ME MUERO", 'muere')
                index = self.nodosQueMueren.index(self.id)
                tiempo = self.tiempoRevivir[index]
                newevent = Event("REVIVE", self.clock + tiempo, self.id, self.id)
                self.transmit(newevent)

            #! TODOS: Criterio para fallo
            #if self.id in self.nodosQueMueren:
            #    index = self.nodosQueMueren.index(self.id)
            #    if self.clock == self.tiempoMuerte[index] - 1.0:
            #        mensaje(self, "MUERO", self.id)

        else:  # Estoy muerto. Ignoro todos los mensajes, excepto el que me revive.

            if event.getName() == "REVIVE":
                self.estoyVivo = True
                if self.soyLider:
                    setPrint("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Que se armen ya revivi: " + str(self.id) + " Heartbeat: " + str(self.numHeartbeat), 'revivir')
                    setTimerHeartbeat(self)
                    self.timerDespachadoAlerta = False
                    #setHeartbeat(self)
                    self.timerReiniciado = 0
                    self.recienRevivido = True
                else:
                    setPrint("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Ya revivi: " + str(self.id),'revivir')
                    self.candidaturaMandada = False
                    self.timerReiniciado = 0
                    self.timerDespachadoAlerta = False
                    self.estadoAlerta = False
                    self.estadoElecciones = False
                    self.ignorarMensajes = False
                    print("[" + str(self.clock) + "]: " + " Nodo: " + str(self.id) + "Recien revivido, mando timer estado lider")
                    setTimerEstadoLider(self)
                    #self.timerReiniciado +=1


def setHeartbeat(self):
    """ Encargado de mandar heartbeat a todos los vecinos cuando se es líder
        El líder se lo manda a sí mismo como timer para mandar el siguiente hearbeat """
    self.numHeartbeat += 1
    listaVivos = copy.copy(self.listaVivos)
    for t in self.neighbors:
        newevent = Mensaje(
            "HEARTBEAT", 
            self.clock + 1.0, 
            t, 
            self.id, 
            listaVivos, 
            self.numHeartbeat,
            self.nodosQueMueren, 
            self.tiempoMuerte, 
            self.tiempoRevivir
            )
        self.transmit(newevent)
    setPrint(
        "[" + str(self.clock) + "]:" + 
        " Nodo: " + str(self.id) + 
        " HEARTBEAT num: " + 
        str(self.numHeartbeat),
        'heartbeat'
        )


def enviaCandidato(self, event):
    if event.getSource() > self.mejorCandidato:
        print(
            "[" + str(self.clock) + "]:" + 
            " Nodo: " + str(self.id) + 
            " !enviaCandidato! No soy mejor candidato que " + 
            str(event.getSource()) + 
            " no mando nada"
            )
        self.mejorCandidato = event.getSource()
    else:
        if not self.candidaturaMandada:
            print(
                "[" + str(self.clock) + "]:" + 
                " Nodo: " + str(self.id) + 
                " !enviaCandidato! Soy mejor candidato, mando canditatura"
                )
            self.candidaturaMandada = True
            for t in self.neighbors:
                mensaje(self, "CANDIDATO", t)
    if not self.estadoElecciones:
        print(
            "[" + str(self.clock) + "]:" + 
            " Nodo: " + str(self.id) + 
            " !enviaCandidato! Inicio estado de elecciones por candidatura " + 
            str(event.getSource())
            )
        setTimerElecciones(self)
    else:
        print(
            "[" + str(self.clock) + "]:" + 
            " Nodo: " + str(self.id) + 
            " !enviaCandidato! Ya estoy en eleccinoes activas me llego candidato de: " + 
            str(event.getSource())
            )
    self.estadoElecciones = True
    


def setTimerHeartbeat(self):
    frecuencia = float(frecuenciaHeartbeat.get())
    newevent = Event("TIMER_HEARTBEAT", self.clock + frecuencia, self.id, self.id)
    self.transmit(newevent)


def inputToList(entradaString):
    """ Convierte la entrada de GUI en una lista para poder procesarla
        Los elementos de la entrada tienen que esta separados por comas ","   """
    # TODO: Admitir tambien separados por espacios
    lista = list(entradaString.split(","))
    for i in range(0, len(lista)):
        lista[i] = float(lista[i])
    return lista


def inputToListInteger(entradaString):
    """ Convierte la entrada de GUI en una lista para poder procesarla
        Los elementos de la entrada tienen que esta separados por comas ","   """
    # TODO: Admitir tambien separados por espacios
    lista = list(entradaString.split(","))
    for i in range(0, len(lista)):
        lista[i] = int(lista[i])
    return lista


def setTimerElecciones(self):
    frecuencia = float(timerELecciones.get())
    newevent = Event("TIMERELECCIONES", self.clock + frecuencia, self.id, self.id)
    self.transmit(newevent)
    print(
        "[" + str(self.clock) + "]:" + 
        " Nodo: " + str(self.id) + 
        "Activo timer elecciones"
        )


def setPrint(s, tipo):
    print(s)
    tex.insert(tk.END, s + "\n", tipo)
    tex.see(tk.END)


def mensaje(self, mensaje, destino):
    newevent = Event(mensaje, self.clock + 1.0, destino, self.id)
    self.transmit(newevent)

    """ Encargado de programar el timer al tiempo indicado en el GUI que checara el estado del líder
        IMPORTANTE: El timer tiene que ser más largo que el hearbeat, mínimo igual """


def setTimerEstadoLider(self):
    if self.id == 4:
        print(
            "????????????????????????????????????[" + str(self.clock) + "]: " + 
            " Nodo: " + 
            str(self.id) +
            " Mando TIMER ESTADO, A IGNORAR: " + 
            str(self.timerReiniciado + 1)
            )
    else:
        print(
            "!!!!!!!!![" + str(self.clock) + "]: " + 
            " Nodo: " + str(self.id) + 
            " Mando TIMER ESTADO, A IGNORAR: " + 
            str(self.timerReiniciado + 1)
            )
    newevent = Event("TIMERESTADO", self.clock + float(timerNodo.get()), self.id, self.id)
    self.transmit(newevent)


# ----------------------------------------------------------------------------------------
# "main()"
# ----------------------------------------------------------------------------------------

# construye una instancia de la clase Simulation recibiendo como parametros el nombre del 
# archivo que codifica la lista de adyacencias de la grafica y el tiempo max. de simulacion


# if len(sys.argv) != 2:
#     print("Please supply a file name")
#     raise SystemExit(1)
# experiment = Simulation(sys.argv[1], 50)

experiment = Simulation("topo.txt" , 500)



for i in range(1, len(experiment.graph) + 1):
    m = Algorithm2()
    experiment.setModel(m, i)


def start():
    listaMuertos = inputToListInteger(quienMuere.get())
    tiempoMueren = inputToList(tiempoMuerte.get())
    tiempoReviven = inputToList(tiempoRevive.get())

    seed = Mensaje("DESPIERTA", 0.0, 1, 1, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
    seed2 = Mensaje("DESPIERTA", 0.0, 2, 2, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
    seed3 = Mensaje("DESPIERTA", 0.0, 3, 3, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
    seed4 = Mensaje("DESPIERTA", 0.0, 4, 4, [], 0, listaMuertos, tiempoMueren, tiempoReviven)

    experiment.init(seed)
    experiment.init(seed2)
    experiment.init(seed3)
    experiment.init(seed4)
    experiment.run()


root = tk.Tk()
root.title("Simulador de eleccion de lider ")

# Elementos(Como se muestran, de izquierda a derecha, de arriba hacia a bajo)
quienMuereL = tk.Label(root, text="¿Qué nodod quieres que fallen?")
quienMuere = tk.Entry(root, borderwidth=2)

tiempoMuerteL = tk.Label(root, text="¿A qué tiempos quieres que fallen?")
tiempoMuerte = tk.Entry(root, borderwidth=2)

tiempoReviveL = tk.Label(root, text="¿Cuantos tiempos despues quieres que se recuperen?")
tiempoRevive = tk.Entry(root, borderwidth=2)

timerNodosL = tk.Label(root, text="¿Cuanto quieres que dure el timer de estado del lider?")
timerNodo = tk.Entry(root, borderwidth=2)

frecuenciaHeartbeatL = tk.Label(root, text="¿Cual quieres que sea la frecuencia del heartbeat")
frecuenciaHeartbeat = tk.Entry(root, borderwidth=2)

timerEleccionesL = tk.Label(root, text="¿Cuando deben de durar las elecciones?")
timerELecciones = tk.Entry(root, borderwidth=2)

tex = tk.Text(root)  # ,heigh=10),,
scr = tk.Scrollbar(root, orient=tk.VERTICAL, command=tex.yview)
run = tk.Button(root, text="Run", command=start)  # padx=15,pady=15
# clean = tk.Button(root, text="Clear", commmand=borrar)# lambda: tex.delete("1.0", tk.END))
# tex.delete("1", tk.END)

exit = tk.Button(root, text='Salir', command=root.destroy)

# Looks
# clean.grid(row=7,column=0)

quienMuereL.grid(row=0, column=0)
quienMuere.grid(row=1, column=0, sticky=tk.N)

tiempoMuerteL.grid(row=2, column=0)
tiempoMuerte.grid(row=3, column=0, sticky=tk.N)

tiempoReviveL.grid(row=4, column=0)
tiempoRevive.grid(row=5, column=0, sticky=tk.N)

timerNodosL.grid(row=6, column=0)
timerNodo.grid(row=7, column=0)

frecuenciaHeartbeatL.grid(row=8, column=0)
frecuenciaHeartbeat.grid(row=9, column=0)

timerEleccionesL.grid(row=10, column=0)
timerELecciones.grid(row=11, column=0)

run.grid(row=12, column=0 )
exit.grid(row=13, column=0)
tex.grid(row=0, column=1, rowspan=16, columnspan=3, sticky=tk.W, pady=10)
scr.grid(row=0, column=4, rowspan=17, columnspan=1, sticky=tk.NS)

# root.grid_columnconfigure(9, weight=1)
root.grid_rowconfigure(17, minsize=100, weight=1)

# Funcionalidad Como estan ordenados los inserts, dentro del int() esta su valor por default
tiempoMuerte.insert(0, float(9.0))
quienMuere.insert(1, int(4))
tiempoRevive.insert(2, float(5))
timerNodo.insert(3, float(2))
frecuenciaHeartbeat.insert(4, float(1))
timerELecciones.insert(5, float(2))

tex.config(yscrollcommand=scr.set)

tex.tag_config('heartbeat', foreground="#000000")  # background="yellow"    
tex.tag_config('muere', foreground="#FE0113")
tex.tag_config('revivir', foreground="#0a6df0")
tex.tag_config('cambiaLider', foreground="#05571a")
tex.tag_config('elecciones', foreground='#069c85')
tex.tag_config('nuevoLider', foreground='#c9ac08')
tex.tag_config('soyLider', foreground="#bd720b")
tex.tag_config('protocolo', foreground="green")

# experiment.run()
root.mainloop()
