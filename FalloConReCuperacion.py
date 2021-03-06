#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import copy
from simulador import Event, Model, Simulation
# from GUI import setPrint, run
from mensaje import Mensaje, mensaje
import tkinter as tk        


# Martinez Vargas Edgar Ivan
#

class Algorithm2(Model):

    
    def init(self):
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

            # Pongo timer para saber si líder esta activo o no, e inicializo las variables que necesito
            if event.name == "DESPIERTA":
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
                self.nodosQueMueren = event.nodos_mueren
                self.tiempoMuerte = event.tiempo_muerte
                self.tiempoRevivir = event.tiempo_revivir

                # Programa su muerte desde el inicio
                print(self.nodosQueMueren)
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
            if self.estadoAlerta and event.name != "OK" and event.name != "TIMER_HEARTBEAT":
                self.estadoAlerta = False
                # Inicia elecciones
                if event.name == "HEARTBEAT":
                    mensaje(self, "OK", event.source)
                    self.numHeartbeat = event.num_heartbeat
                    print(
                        "[" + str(self.clock) + "]:" + 
                        " Nodo: " + str(self.id) + 
                        " Mando timer estado ,heartbeat en estado"
                        )
                    setTimerEstadoLider(self)
                    self.timerReiniciado += 1

                if event.name == "TIMERESTADO":
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

                if event.name == "CANDIDATO":
                    enviaCandidato(self, event)
                # Hay dos lideres hizo decempate
                # self.estadoAlerta = False
                print(
                    "[" + str(self.clock) + "]:" + 
                    " Nodo: " + str(self.id) + 
                    " Estado de alerta desactivado por " + 
                    str(event.name)
                    )


            # SoyLider #############################
            if self.soyLider:
                print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + "Soy Lider, me llega mensaje " + str(event.name) + " de " + str(event.source) )
                # LIDER: Agrega a la lista los nodos que le respondieron
                if event.name == "OK" and not self.ignorarMensajes:
                    self.listaVivos.append(event.source)
                    self.recienRevivido = False
                if event.name == "HEARTBEAT" and not self.ignorarMensajes:
                    if event.num_heartbeat > self.numHeartbeat or (
                        event.num_heartbeat == self.numHeartbeat and event.source > self.id) or (
                        event.num_heartbeat == self.numHeartbeat and self.recienRevivido):
                        self.soyLider = False
                        self.lider = event.source
                        setPrint(
                            "[" + str(self.clock) + "]:" + 
                            " Nodo: " + str(self.id) + 
                            " Mi reinado a terimando. Mi Heartbeat: " + 
                            str(self.numHeartbeat) + 
                            " Heartbeat del otro:" + 
                            str(event.num_heartbeat), 
                            'muere'
                            )
                        setTimerEstadoLider(self)
                    else:
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " + str(
                            self.id) + " YO SOY EL LIDER: " + str(self.id) + " Mi HeartBeat: " + str(
                            self.numHeartbeat) + " Heartbeat del otro:" + str(event.num_heartbeat), 'soyLider')
                if event.name == "CANDIDATO":# and not self.estadoElecciones:
                    if not self.estadoElecciones:
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " +str(self.id) + " Soy lider y entro a elecciones porque recibi candidatura de: " + str(event.source),"elecciones")
                    enviaCandidato(self, event)
                if event.name == "TIMER_HEARTBEAT":
                    setHeartbeat(self)
                    setTimerHeartbeat(self)

            # No soy lider #################
            if not self.soyLider:
                # Respondo al lider
                if event.name == "HEARTBEAT" and not self.ignorarMensajes:
                    print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Mando timer estado respuesta a heartbeat")
                    setTimerEstadoLider(self)
                    self.timerReiniciado += 1
                    mensaje(self, "OK", event.source)
                    self.numHeartbeat = event.num_heartbeat
                    print("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + "Mando Ok al lider")

                if event.name == "CANDIDATO":
                    if not self.estadoElecciones:
                        setPrint("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Entro a elecciones porque recibi candidatura de: " + str(event.source), "elecciones")
                    enviaCandidato(self, event)

                if event.name == "TIMERESTADO" and not self.estadoAlerta and not self.timerDespachadoAlerta:
                    if self.timerReiniciado != 0:
                        self.timerReiniciado -= 1
                        print("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Ignoro este timer, viene otro atras, TIMERS A IGNORAR: " + str(self.timerReiniciado))
                    else:
                        print("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Entra estaado Alerta,PRIMER TIMER EXPIRADO    ")
                        print("[" + str(self.clock) + "]:" + " Nodo: " + str(self.id) + " Mando timer estado entro estado alerta")
                        setTimerEstadoLider(self)
                        self.estadoAlerta = True
                        #self.timerReiniciado = False

                if event.name == "TIMERESTADO" and self.timerDespachadoAlerta:
                    self.timerDespachadoAlerta = False
            
            
            # Elecciones ############
            if self.estadoElecciones:
                self.ignorarMensajes = True
                if event.name == "CANDIDATO":
                    if event.source > self.mejorCandidato:  # Al inicio siempre es self.id
                        self.mejorCandidato = event.source
                if event.name == "TIMERELECCIONES":  # Se terminan las elecciones
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


            # Simula el fallo
            if event.name == "MUERO":
                self.estoyVivo = False
                if self.soyLider:
                    setPrint("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Soy el lider " + str(self.id) + " y ME MUERO", 'muere')
                else:
                    setPrint("[" + str(self.clock) + "]: " + "Nodo: " + str(self.id) + " Soy " + str(self.id) + " y ME MUERO", 'muere')
                index = self.nodosQueMueren.index(self.id)
                tiempo = self.tiempoRevivir[index]
                newevent = Event("REVIVE", self.clock + tiempo, self.id, self.id)
                self.transmit(newevent)


        else:  # Estoy muerto. Ignoro todos los mensajes, excepto el que me revive.

            if event.name == "REVIVE":
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
    if event.source > self.mejorCandidato:
        print(
            "[" + str(self.clock) + "]:" + 
            " Nodo: " + str(self.id) + 
            " !enviaCandidato! No soy mejor candidato que " + 
            str(event.source) + 
            " no mando nada"
            )
        self.mejorCandidato = event.source
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
            str(event.source)
            )
        setTimerElecciones(self)
    else:
        print(
            "[" + str(self.clock) + "]:" + 
            " Nodo: " + str(self.id) + 
            " !enviaCandidato! Ya estoy en eleccinoes activas me llego candidato de: " + 
            str(event.source)
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

experiment = Simulation("topo.txt" , 50)
for i in range(1, len(experiment.graph) + 1):
    m = Algorithm2()
    experiment.setModel(m, i)


def start():
    listaMuertos = inputToListInteger(quienMuere.get())
    tiempoMueren = inputToList(tiempoMuerte.get())
    tiempoReviven = inputToList(tiempoRevive.get())

    for i in range(1,5):
        seed = Mensaje("DESPIERTA", 0.0, i, i, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
        experiment.init(seed)
    # seed = Mensaje("DESPIERTA", 0.0, 1, 1, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
    # seed2 = Mensaje("DESPIERTA", 0.0, 2, 2, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
    # seed3 = Mensaje("DESPIERTA", 0.0, 3, 3, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
    # seed4 = Mensaje("DESPIERTA", 0.0, 4, 4, [], 0, listaMuertos, tiempoMueren, tiempoReviven)
    # experiment.init(seed)
    # experiment.init(seed2)
    # experiment.init(seed3)
    # experiment.init(seed4)
    experiment.run()


#GUI
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
