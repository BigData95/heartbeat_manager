from simulador import Event

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
        self.__listaVivos = listaVivos
        self.__numHeartbeat = numHeartbeat
        self.__nodosQueMueren = nodosQueMueren
        self.__tiempoMuerte = tiempoMuerte
        self.__tiempoRevivir = tiempoRevivir

    
    @property
    def lista_vivos(self):
        return self.__listaVivos

    @property
    def num_heartbeat(self):
        return self.__numHeartbeat

    @property
    def nodos_mueren(self):
        return self.__nodosQueMueren

    @property
    def tiempo_muerte(self):
        return self.__tiempoMuerte

    @property
    def tiempo_revivir(self):
        return self.__tiempoRevivir

def mensaje(self, mensaje, destino):
    newevent = Event(mensaje, self.clock + 1.0, destino, self.id)
    self.transmit(newevent)
